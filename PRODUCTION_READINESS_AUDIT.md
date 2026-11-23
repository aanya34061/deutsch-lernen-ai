# Deutsch Lernen AI — Production Readiness Audit

Audit date: 2026-11-23
Repository inspected: `aanya34061/deutsch-lernen-ai`
Production URL: https://deutsch-lernen-ai.vercel.app
Verdict: **Ready for controlled beta testing; not production ready for the full advertised experience.**

## Executive summary

The existing React/Vite frontend and FastAPI/MongoDB backend were retained. Production is deployed on Vercel; the live health endpoint reports MongoDB connected and Vercel Blob configured as persistent storage. The frontend returns HTTP 200, and an unauthenticated dashboard request returns HTTP 401. Registration, login, logout, session expiry, CSRF checks, representative cross-account access checks, curriculum loading, and core API flows pass the backend tests.

The production AI provider is disabled. As a result, the AI Tutor and AI-generated writing evaluation are unavailable, and speaking practice cannot continue beyond its authored opening prompt. Listening exercises use browser speech synthesis when no audio file exists; they are not all recordings. Actual production Vercel Blob upload/retrieval/deletion and a full browser/mobile session were not exercised. These limitations prevent a claim of production readiness for all requested features.

## Findings and disposition

| Component | Current implementation and issue | Severity | Fix / verification |
|---|---|---:|---|
| Authentication | PBKDF2-SHA256 password hashes, secure session cookies, hashed session tokens, CSRF checks, and 14-day expiry. No login/register rate limiting is configured. | Medium | Verified registration, login, logout, invalid and expired sessions, anonymous API denial, and CSRF behavior in backend tests. Rate limiting remains deployment work. |
| User data isolation | API requests require a session; data services generally scope MongoDB operations to the authenticated account. | High | Cross-account tests cover materials/files, vocabulary, notes, and exercises. Broader per-collection isolation still merits ongoing regression coverage. |
| Server-side link fetching | User-provided links were fetched with automatic redirects and no private-network checks, creating an SSRF risk. | High | Added public-IP validation, redirect-by-redirect validation, disabled proxy environment inheritance, capped fetched HTML at 2 MiB, and sanitized unexpected fetch errors. Direct private-address tests and a mocked redirect-to-loopback test pass. DNS is checked before connection but not pinned to the resolved address, so deliberate DNS rebinding is a residual risk. |
| MongoDB | Motor connects to remote MongoDB in production; production health reports database `german_learning` connected. Data is external to the Vercel function filesystem. | Low | Live health verified. Backend integration suite uses randomized local test databases and drops only those test databases. No production learner data was created or modified for testing. |
| File storage | Production health reports private Vercel Blob configured and persistent. The backend previously accepted files larger than Vercel's function request limit. | High | Production file limit is now 4 MiB in both UI and API; local development keeps its existing limit. Local upload tests and an object-storage mock test pass. Actual Blob roundtrip and persistence across redeployment remain unverified. |
| Curriculum | Authored lesson material existed, but the manifest exposed A1=7, A2=6, B1=7 modules rather than the requested 6/5/7. | Medium | Consolidated supplementary topics into related modules while retaining all 87 authored lessons and their prior lesson/topic IDs. Tests verify 18 modules, 87 lessons, content fields, exercises, and persistence/seeding behavior. Grammar/CEFR appropriateness still needs review by a German instructor. |
| Lesen | Authored reading passages, vocabulary support, comprehension questions, answer explanations, and saved attempts exist. | Low | Backend reading tests pass. No independent teacher review of every answer or CEFR placement was performed. |
| Hören | Authored listening exercises and a maintained external-resource catalog exist. Browser speech synthesis is used where an exercise has no audio URL; link reachability varies by publisher. | Medium | Exercise/resource API tests pass. External resource availability and real-device audio playback were not checked. This is not uniformly recorded native-speaker audio. |
| Schreiben | Writing prompts and persistent drafts exist. Offline feedback is a small rule-based check, not full grammar evaluation; it previously assigned a misleading numeric score. | High | Removed the heuristic score. The UI now says no score is available when AI is offline, while saving the attempt and limited hints. Regression test verifies no score is stored/reported. AI correction remains unavailable in production. |
| Sprechen | Authored scenarios, typed responses, and browser speech recognition fallback exist; subsequent tutor turns require AI. | High | UI communicates the dependency and supports typing if speech recognition is absent. Backend tests ensure no fabricated tutor reply is saved. Production follow-up conversation is unavailable while AI is disabled. Browser mic behavior was not tested. |
| AI Tutor | Integration uses actual configured Ollama/hosted provider code; no hardcoded tutor answer path was found. Production health reports provider `disabled`. | High | Unavailability is surfaced rather than represented as working. Tutor chat and AI-generated practice are not usable in production until a provider/model is configured. No paid provider was added. |
| Dashboard/progress | Progress is derived from persisted user activity. A heuristic writing fallback could inflate scores. | High | Removed that score; unscored writing activity remains counted as activity and has no average score. API tests cover dashboards and skill progress. Live user progress was not altered. |
| Tutor status/errors | A broad status exception could return raw internal exception text. | Medium | Catch-all status responses and logs now expose only a generic message and exception class. Added and passed regression test. |
| Curriculum query performance | Module listing made one topic query per module. | Low | Replaced the N+1 pattern with one batched topic query and added compound indexes for module/topic ordering. Full backend suite passes. |
| Frontend/API integration | Same-origin `/api/v1` requests, cookie credentials, and CSRF header handling are configured. | Low | Frontend unit tests and production build pass; live frontend and protected-route checks pass. There is no browser automation, lint script, or type-check script configured. |
| Dependency audit | Frontend uses a lockfile; backend runtime requirements used broad minimum versions and included test-only packages. | Medium | Moved pytest dependencies to `backend/requirements-dev.txt`. `npm audit` could not reach the npm advisory registry, and `pip-audit` is not installed; known-vulnerability status is therefore unverified. No blanket upgrades were made. |
| Deployment | Vercel frontend/backend services, same-origin API rewrite, remote MongoDB, and Blob configuration are active. | Low | Final Vercel deployment reached READY and was verified via live health, frontend HTTP 200, and anonymous dashboard HTTP 401. The deployment was made from this local working tree; audit changes have not been committed or pushed to GitHub. |

## Persistence and data ownership

- User accounts, sessions, progress, lesson completions, attempts, vocabulary, notes, and conversation records are stored in MongoDB with authenticated user IDs.
- Production health confirmed MongoDB connectivity; local integration tests confirmed reads/writes and representative owner checks.
- Uploaded files are configured for Vercel Blob, which is external to ephemeral function storage. The production health endpoint confirms configuration, not a real file roundtrip. No production upload was made during this audit.
- A deployment cannot be used as evidence that a specific learner's data survives logout/relogin or redeployment; production-data lifecycle testing remains outstanding.

## Curriculum inventory

| CEFR | Modules | Authored lessons/topics |
|---|---:|---:|
| A1 | 6 | 28 |
| A2 | 5 | 31 |
| B1 | 7 | 28 |
| **Total** | **18** | **87** |

Manifest tests require objectives, substantial explanations, grammar rules, German/English examples, vocabulary, common mistakes, summaries, and at least three explained exercises per lesson. These are structural/content-presence checks, not a full linguistic proofread.

## AI and voice in production

- AI provider: **disabled**; the configured model name in health output is not evidence that the model is installed or reachable.
- Tutor chat, AI-generated exercises, AI writing corrections, and speaking follow-up turns: **unavailable** in the deployed environment.
- Writing fallback: limited capitalization/basic checks; no numeric score is generated.
- Speaking input and listening playback use browser speech APIs where available, with typing/external-resource fallbacks. Browser-specific behavior remains untested.

## Performance and deployment notes

- Last local production build: JavaScript 401.56 kB (115.37 kB gzip); CSS 315.59 kB (46.00 kB gzip).
- Curriculum module listing now batches topic loading rather than issuing a query per module.
- Production uploads are capped at 4 MiB because Vercel Functions default to a 4.5 MB request-body limit; the cap includes room for multipart framing. See [Vercel Function limits](https://vercel.com/docs/functions/limitations).
- Deployment build succeeded. Vercel CLI reported it could not fetch npm dist-tags, but the remote build completed and deployment became READY.
- The API logs to standard output; no external error reporting or alerting integration was found.

## Files changed

- Deployment and storage: `.gitignore`, `README.md`, `backend/app/config.py`, `backend/app/main.py`, `backend/app/routers/health.py`, `backend/app/services/library_service.py`, `backend/app/services/storage_service.py`, `backend/requirements.txt`, and new `backend/requirements-dev.txt`.
- Curriculum, performance, and security: `backend/app/data/curriculum_manifest.py`, `backend/app/database.py`, `backend/app/services/curriculum_service.py`, `backend/app/services/extractor_service.py`, `backend/app/routers/tutor.py`, and `backend/app/services/ollama_service.py`.
- Honest writing/progress feedback: `backend/app/models/practice.py`, `backend/app/services/practice_service.py`, `frontend/src/pages/PracticeWritingPage.jsx`, and `frontend/src/components/library/UploadDropzone.jsx`.
- Regression coverage: `backend/tests/test_auth_storage_security.py`, `backend/tests/test_curriculum_manifest.py`, `backend/tests/test_library.py`, `backend/tests/test_practice.py`, and `backend/tests/test_tutor.py`.

## Tests and checks performed

| Command/check | Result |
|---|---|
| `backend/.venv/bin/pytest -q --tb=short` from `backend/` | **98 passed**; MongoDB integration used randomized local test databases. |
| `backend/.venv/bin/pytest -q --tb=short tests/test_library.py::test_web_fetch_revalidates_redirect_destinations` | **1 passed**; mocked HTTP transport, no external request. |
| `npm test` from `frontend/` | **23 passed**. |
| `npm run build` from `frontend/` | **Passed**. |
| `backend/.venv/bin/python -m compileall -q app` | **Passed**. |
| `git diff --check` | **Passed**. |
| Live `GET /api/v1/health` | **healthy**, MongoDB connected, Blob configured/persistent, AI disabled. |
| Live `GET /` | HTTP **200**. |
| Live anonymous `GET /api/v1/dashboard` | HTTP **401**. |
| `npm audit --json` | **Not completed**: npm advisory endpoint was unreachable. |
| `python -m pip_audit -r requirements.txt` | **Not completed**: `pip_audit` is not installed; package registry access was unavailable. |
| Lint/type checks | **Not configured** in package scripts/project config. |
| Browser/mobile E2E, microphone, real Blob CRUD | **Not run**; no browser automation or production test account/file was used. |

## Remaining work before production launch

1. Configure a hosted AI provider/model (or explicitly scope the product as non-AI); verify tutor, writing correction, and speaking follow-up in production.
2. Add platform-level rate limits/bot controls for registration, login, uploads, and AI endpoints.
3. Verify Vercel Blob upload, authenticated download, deletion, and persistence across redeployment using a disposable test account/file.
4. Run browser-based desktop/mobile, accessibility, keyboard, microphone, and real audio-link checks.
5. Run dependency audits from an environment with registry access and add a Python lock/constraints strategy.
6. Review curriculum grammar, answer keys, and CEFR level with a qualified German instructor.
7. Commit and push the audited source to the public GitHub repository so its default branch matches the deployed implementation.

## Final verdict

A learner can register, sign in, access authored A1–B1 lessons, use reading and other authored practice content, and persist activity through the configured backend. The complete advertised experience is **not verified as production ready**: AI tutoring is disabled, speaking follow-up is unavailable, listening does not uniformly provide real recorded audio, and Vercel Blob has not had an end-to-end production upload test. The honest status is **ready for controlled beta testing with these limitations disclosed**.

## Follow-up remediation — 2026-11-23

This section supersedes the earlier “remaining work” statements above where it contains newer verification. Work is on branch `codex/production-readiness-fixes`.

### Current verdict

**Not ready for production as the full advertised German-learning product.** The live service is healthy and can be considered for a controlled beta with clear limitations, but its production AI provider is still disabled, AI writing feedback and speaking follow-up therefore remain unavailable, and a complete signed-in student browser test and redeployment persistence test have not been completed.

### Follow-up issue status

| Issue | Follow-up result | Status |
|---|---|---|
| Production AI provider | The backend supports OpenAI-compatible hosted endpoints and reports provider/model state accurately. Production health still reports `disabled`. No provider or credentials were selected/configured while the no-cost provider clarification is pending; no paid AI service was introduced. | **Blocked** on provider approval and credentials; tutor, AI writing evaluation, and speaking follow-up are **not working in production**. |
| Authentication/upload/AI bot controls | Added shared MongoDB fixed-window limits (auth 10/min, upload/link import 8/min, AI 12/min) with TTL cleanup and 429/Retry-After responses. Vercel's forwarded-client header is trusted only on Vercel; raw forwarded headers are ignored elsewhere. | **Implemented and unit-tested**. No CAPTCHA/challenge is configured, and full live abuse testing was not performed. |
| Private Blob operations | Using the production Blob credentials in memory and a unique non-learner audit object, upload, private download round-trip, and deletion through the backend storage adapter all passed. A live unauthenticated library file request returned 401. | Upload/download/delete **verified**. Positive authenticated API retrieval and ownership denial against the real store were **not tested** with a production test account. |
| Blob persistence after redeployment | No production code redeployment was performed for this follow-up. | **Not verified**. |
| User-level isolation | Added regression coverage for materials/files, vocabulary, notes/questions, curriculum completion/custom lessons, tutor conversations, writing drafts/submissions, speaking sessions, listening completion, exercise attempts, and indexed chunks. Queries inspected bind to the current authenticated user or to an owned material. | Code reviewed; integration regression tests **not executed against a reachable Mongo test database** in this environment. |
| URL fetching / DNS rebinding | Fetches resolve and validate every destination, reject hostnames with any non-public answer, pin the HTTP connection to the vetted IP while preserving Host/TLS SNI, disable environment proxies, revalidate redirects, cap response bytes, and return sanitized errors. | SSRF regressions for redirects, mixed public/private DNS answers, and proxy disabling **passed**. |
| Listening resources | Corrected the malformed A1 Goethe resource URL. Verified the Goethe A1/A2/B1 practice pages, DW Nicos Weg YouTube page, Slow German episode page, and LibriVox collection pages are reachable. Chrome decoded and played the catalog's direct LibriVox MP3. | External pages and one direct recording **verified**. The 5 in-app authored exercises (A1×2, A2×2, B1×1) have scripts and use browser speech synthesis; none has a recorded audio file. Other catalog sources play on their publisher pages rather than inside the app. |
| Desktop/mobile browser, keyboard, accessibility | Headless Chrome at 1440×1000 and 390×844 found no horizontal overflow or captured JS errors on sign-in. Username/password labels are associated; Tab order is username → password → sign-in → create account. Chrome exposes speech synthesis, SpeechRecognition, and getUserMedia APIs; direct audio playback passed. | **Partial**. No authenticated learner flows, screen-reader/axe audit, real microphone permission/capture, or actual speech-recognition conversation was tested. |
| German curriculum review | Rechecked the 87-lesson manifest (28 A1, 31 A2, 28 B1), its 264 exercises, and answer-option/token consistency; the structural answer-key scan found no mismatches. Existing content was left intact. | **Partial**. This is not a full human grammar, translation, answer rationale, or CEFR proofread by a German instructor. |
| Dependency security and reproducibility | Added `backend/requirements.in`; generated a Python 3.12 hash-pinned `backend/requirements.txt`; moved compiler/audit tools into dev requirements. Installed from the lock successfully. `pip-audit` reported no known vulnerabilities for the locked runtime packages. | Python audit/lock **verified**. `npm audit` could not reach the npm advisory endpoint; frontend dependency vulnerability status remains **unknown**. |
| Error monitoring/alerting | Added optional Sentry SDK setup, health reporting, and event scrubbing that removes request/user data, frame locals, and exception text. | Integration **implemented**, but no Sentry DSN/project/alert rules are configured in production; monitoring and alert delivery are **not active**. |
| GitHub source | Changes were committed as `ab2c1bd` and pushed to `codex/production-readiness-fixes`. | **Pushed and verified**; no main-branch merge is included. |

### Updated live checks and tests

| Check | Result |
|---|---|
| Production `/api/v1/health` | `healthy`; MongoDB connected; Blob configured/persistent; AI disabled. |
| Production anonymous library file retrieval | HTTP 401. |
| Production Blob backend adapter | Unique audit file upload PASS; private download bytes matched PASS; deletion PASS. |
| Chrome desktop/mobile public sign-in | No horizontal overflow or captured JS errors; labels and keyboard focus order PASS. |
| Chrome external audio playback | LibriVox MP3 reached `canplay` and playback time advanced PASS. |
| `frontend/npm test` | 23 passed. |
| `frontend/npm run build` | Passed; bundle sizes unchanged from previous report. |
| `backend/.venv/bin/pytest -q backend/tests/test_rate_limit.py` | 8 passed. |
| Targeted curriculum/security tests | 3 passed: 87-lesson structural/answer-key check, mixed DNS rejection, and transport proxy isolation. |
| `backend/.venv/bin/python -m pip_audit -r backend/requirements.txt --no-deps --disable-pip` | No known vulnerabilities found in the pinned Python runtime lock. |
| `python -m compileall -q backend/app backend/tests`; `git diff --check` | Passed. |
| Full backend test suite | Not run: this workspace could not establish its MongoDB test connection. The expanded per-collection integration tests therefore remain unverified here. |
| `npm audit --json` | Not completed: npm advisory endpoint failed from both sandboxed and escalated attempts. |

### Changes in this remediation

- Implemented shared request throttles and added limiter tests.
- Completed IP pinning and proxy disabling for server-side URL fetches; added rebinding and redirect regressions.
- Added cross-user isolation cases across the learner-owned record types.
- Corrected the A1 Goethe listening resource URL; documented which exercises synthesize speech versus use recorded audio.
- Added the hashed Python runtime lock and optional, privacy-scrubbed Sentry integration.
- Updated health reporting to show hosted AI and monitoring configuration accurately.
- Added user-facing production configuration documentation without adding AI credentials or selecting a provider.

### Remaining work

1. Owner must choose/approve a no-cost hosted AI service and supply its credentials/model; then verify all three AI flows against the real configured model.
2. Configure Sentry DSN and alert rules, or select another monitoring destination.
3. Run full backend integration tests against a dedicated non-production MongoDB database.
4. Run positive authenticated Blob upload/retrieval/delete and persistence checks across an approved deployment using a disposable test account. No learner data should be used.
5. Run the authenticated browser suite with a real microphone, speech recognition, screen reader/accessibility checks, and interactive listening exercises.
6. Have a qualified German instructor review all 87 lessons and their answer explanations/CEFR appropriateness.
7. Complete the npm advisory scan when the npm registry audit endpoint is reachable.
