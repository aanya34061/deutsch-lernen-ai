from types import SimpleNamespace

import pytest

from app.rate_limit import LIMITS, enforce_request_limit


class RateLimitCollection:
    def __init__(self):
        self.counts = {}

    async def find_one_and_update(self, query, update, **_kwargs):
        key = query["_id"]
        self.counts[key] = self.counts.get(key, 0) + update["$inc"]["count"]
        return {"count": self.counts[key]}


@pytest.mark.asyncio
async def test_shared_rate_limit_blocks_after_configured_threshold(monkeypatch):
    collection = RateLimitCollection()
    monkeypatch.setattr("app.rate_limit.get_db", lambda: SimpleNamespace(request_limits=collection))
    monkeypatch.setattr("app.rate_limit.client_key", lambda _request: "hashed-client")
    request = SimpleNamespace(url=SimpleNamespace(path="/api/v1/auth/login"))

    results = [await enforce_request_limit(request) for _ in range(LIMITS["auth"][0] + 1)]

    assert all(allowed for allowed, _ in results[:-1])
    assert results[-1][0] is False
    assert results[-1][1] >= 1


@pytest.mark.parametrize("path, expected", [
    ("/api/v1/auth/register", "auth"),
    ("/api/v1/library/upload", "upload"),
    ("/api/v1/tutor/chat", "ai"),
    ("/api/v1/practice/writing/evaluate", "ai"),
    ("/api/v1/practice/speaking/sessions", "ai"),
])
def test_sensitive_routes_are_rate_limited(path, expected):
    from app.rate_limit import category_for

    assert category_for(path) == expected


def test_client_ip_ignores_spoofable_forwarded_header_outside_vercel(monkeypatch):
    from app.rate_limit import client_key

    monkeypatch.delenv("VERCEL", raising=False)
    request = SimpleNamespace(
        headers={"x-vercel-forwarded-for": "203.0.113.55"},
        client=SimpleNamespace(host="198.51.100.20"),
    )

    key = client_key(request)

    import hashlib
    assert key == hashlib.sha256(b"198.51.100.20").hexdigest()


def test_sentry_scrubber_removes_learner_payloads_and_exception_values():
    from app.main import _scrub_sentry_event

    event = {
        "request": {"data": "learner text", "headers": {"Cookie": "session"}},
        "user": {"id": "learner-id"},
        "exception": {"values": [{
            "value": "raw exception with possible request data",
            "stacktrace": {"frames": [{"vars": {"prompt": "learner writing"}}]},
        }]},
    }

    scrubbed = _scrub_sentry_event(event, {})

    assert "request" not in scrubbed
    assert "user" not in scrubbed
    assert scrubbed["exception"]["values"][0]["value"] == "Application exception"
    assert "vars" not in scrubbed["exception"]["values"][0]["stacktrace"]["frames"][0]
