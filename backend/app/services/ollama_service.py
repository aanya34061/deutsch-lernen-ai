import logging
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("german_app.ollama")

class OllamaError(Exception):
    """Base exception for Ollama errors."""
    pass

class OllamaNotRunningError(OllamaError):
    """Raised when Ollama server is unreachable."""
    pass

class OllamaModelMissingError(OllamaError):
    """Raised when the configured model is not installed in Ollama."""
    pass

class OllamaTimeoutError(OllamaError):
    """Raised when an Ollama request times out."""
    pass

class OllamaService:
    @staticmethod
    def _provider() -> str:
        return (settings.AI_PROVIDER or "disabled").strip().lower()

    @staticmethod
    def _normalize_model_name(name: str) -> str:
        """Strip :latest or tag for flexible matching."""
        if ":" in name:
            return name
        return f"{name}:latest"

    @classmethod
    async def check_status(cls) -> Dict[str, Any]:
        """
        Check whether Ollama is running and whether configured models are available.
        Does not throw; returns a structured status object.
        """
        provider = cls._provider()
        if provider == "disabled":
            return {
                "status": "disabled", "provider": "disabled", "is_ready": False,
                "is_running": False, "model_available": False,
                "message": "AI features are unavailable in this deployment.",
                "setup_instructions": "A hosted AI provider can be configured by the application owner.",
            }
        if provider in {"openai-compatible", "hosted"}:
            configured = bool(settings.AI_API_BASE_URL and settings.AI_API_KEY and settings.AI_MODEL)
            return {
                "status": "ready" if configured else "not_configured",
                "provider": "hosted", "is_ready": configured, "is_running": configured,
                "model_available": configured,
                "configured_model": settings.AI_MODEL if configured else None,
                "message": "Hosted AI is configured." if configured else "Hosted AI is not fully configured.",
            }
        if provider != "ollama" or not settings.OLLAMA_BASE_URL:
            return {
                "status": "disabled", "provider": "disabled", "is_ready": False,
                "is_running": False, "model_available": False,
                "message": "AI features are unavailable in this deployment.",
                "setup_instructions": "A hosted AI provider can be configured by the application owner.",
            }

        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        configured_model = settings.OLLAMA_MODEL
        configured_embed = settings.OLLAMA_EMBED_MODEL

        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                res = await client.get(f"{base_url}/api/tags")
                if res.status_code != 200:
                    return {
                        "status": "ollama_not_running",
                        "is_ready": False,
                        "is_running": False,
                        "configured_model": configured_model,
                        "configured_embed_model": configured_embed,
                        "model_available": False,
                        "embed_model_available": False,
                        "installed_models": [],
                        "base_url": base_url,
                        "message": f"Ollama returned HTTP {res.status_code}",
                        "setup_instructions": "Check that Ollama is running and accessible at " + base_url
                    }

                data = res.json()
                raw_models = data.get("models", [])
                installed_names = [m.get("name", "") for m in raw_models]

                # Match model name (e.g. qwen2.5:3b matches qwen2.5:3b or qwen2.5:3b:latest)
                def matches(model_req: str, installed_list: List[str]) -> bool:
                    req_norm = model_req.strip().lower()
                    req_base = req_norm.split(":")[0]
                    for inst in installed_list:
                        inst_norm = inst.strip().lower()
                        inst_base = inst_norm.split(":")[0]
                        if req_norm == inst_norm:
                            return True
                        if req_base == inst_base and (":latest" in inst_norm or ":" not in model_req):
                            return True
                    return False

                model_found = matches(configured_model, installed_names)
                embed_found = matches(configured_embed, installed_names)

                if model_found:
                    return {
                        "status": "ready",
                        "is_ready": True,
                        "is_running": True,
                        "configured_model": configured_model,
                        "configured_embed_model": configured_embed,
                        "model_available": True,
                        "embed_model_available": embed_found,
                        "installed_models": installed_names,
                        "base_url": base_url,
                        "message": f"Ollama is ready with model '{configured_model}'",
                        "setup_instructions": None
                    }
                else:
                    return {
                        "status": "model_not_installed",
                        "is_ready": False,
                        "is_running": True,
                        "configured_model": configured_model,
                        "configured_embed_model": configured_embed,
                        "model_available": False,
                        "embed_model_available": embed_found,
                        "installed_models": installed_names,
                        "base_url": base_url,
                        "message": f"Ollama is running, but configured model '{configured_model}' is not installed.",
                        "setup_instructions": f"Run 'ollama pull {configured_model}' in your terminal."
                    }

        except (httpx.ConnectError, httpx.ConnectTimeout):
            return {
                "status": "ollama_not_running",
                "is_ready": False,
                "is_running": False,
                "configured_model": configured_model,
                "configured_embed_model": configured_embed,
                "model_available": False,
                "embed_model_available": False,
                "installed_models": [],
                "base_url": base_url,
                "message": "Ollama is not running. Please start Ollama locally.",
                "setup_instructions": f"Start the Ollama app or run 'ollama serve' in your terminal."
            }
        except httpx.TimeoutException:
            return {
                "status": "ollama_not_running",
                "is_ready": False,
                "is_running": False,
                "configured_model": configured_model,
                "configured_embed_model": configured_embed,
                "model_available": False,
                "embed_model_available": False,
                "installed_models": [],
                "base_url": base_url,
                "message": "Connection to Ollama timed out.",
                "setup_instructions": "Ensure Ollama is responsive on " + base_url
            }
        except Exception as e:
            logger.warning("Error checking Ollama status (%s).", type(e).__name__)
            return {
                "status": "error",
                "is_ready": False,
                "is_running": False,
                "configured_model": configured_model,
                "configured_embed_model": configured_embed,
                "model_available": False,
                "embed_model_available": False,
                "installed_models": [],
                "base_url": base_url,
                "message": "The configured AI service could not be checked.",
                "setup_instructions": "Check Ollama installation and connection settings."
            }

    @classmethod
    async def generate_chat(
        cls,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        timeout: Optional[float] = None
    ) -> str:
        """
        Send a conversation history to Ollama and return the assistant response string.
        """
        provider = cls._provider()
        if provider == "disabled":
            raise OllamaNotRunningError("AI tutoring is unavailable because no AI provider is configured.")
        if provider in {"openai-compatible", "hosted"}:
            if not (settings.AI_API_BASE_URL and settings.AI_API_KEY and settings.AI_MODEL):
                raise OllamaNotRunningError("AI tutoring is unavailable because the hosted provider is not fully configured.")
            formatted_messages = ([{"role": "system", "content": system_prompt}] if system_prompt else []) + [
                {"role": message.get("role", "user"), "content": message.get("content", "")}
                for message in messages if message.get("content")
            ]
            try:
                async with httpx.AsyncClient(timeout=timeout or settings.OLLAMA_TIMEOUT_SECONDS) as client:
                    res = await client.post(
                        f"{settings.AI_API_BASE_URL.rstrip('/')}/chat/completions",
                        headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
                        json={"model": settings.AI_MODEL, "messages": formatted_messages, "temperature": max(0.0, min(1.0, temperature))},
                    )
                    res.raise_for_status()
                    return res.json()["choices"][0]["message"]["content"].strip()
            except httpx.TimeoutException as exc:
                raise OllamaTimeoutError("The hosted AI provider timed out. Please try again.") from exc
            except Exception as exc:
                logger.warning("Hosted AI request failed (%s).", type(exc).__name__)
                raise OllamaError("The hosted AI provider could not complete this request.") from exc
        if provider != "ollama" or not settings.OLLAMA_BASE_URL:
            raise OllamaNotRunningError("AI tutoring is unavailable because no AI provider is configured.")

        status_info = await cls.check_status()
        if not status_info["is_running"]:
            raise OllamaNotRunningError(
                f"Ollama is not running at {settings.OLLAMA_BASE_URL}. "
                f"Please start Ollama ({status_info.get('setup_instructions', '')})."
            )
        if not status_info["model_available"]:
            raise OllamaModelMissingError(
                f"Model '{settings.OLLAMA_MODEL}' is not installed in Ollama. "
                f"Run 'ollama pull {settings.OLLAMA_MODEL}' to install it."
            )

        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        req_timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role in ["user", "assistant", "system"] and content:
                formatted_messages.append({"role": role, "content": content})

        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": max(0.0, min(1.0, temperature))
            }
        }

        try:
            async with httpx.AsyncClient(timeout=req_timeout) as client:
                res = await client.post(f"{base_url}/api/chat", json=payload)
                if res.status_code != 200:
                    raise OllamaError(f"Ollama chat error (HTTP {res.status_code}): {res.text}")
                data = res.json()
                assistant_msg = data.get("message", {}).get("content", "")
                return assistant_msg.strip()
        except httpx.TimeoutException:
            raise OllamaTimeoutError(
                f"Ollama response timed out after {req_timeout}s. "
                "Consider selecting a lighter model (e.g. qwen2.5:3b or gemma2:2b)."
            )
        except httpx.ConnectError:
            raise OllamaNotRunningError(f"Lost connection to Ollama at {base_url}.")
        except (OllamaError, OllamaNotRunningError, OllamaModelMissingError, OllamaTimeoutError):
            raise
        except Exception as e:
            raise OllamaError(f"Unexpected error calling Ollama chat: {str(e)}")

    @classmethod
    async def generate_embeddings(cls, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Request embeddings from Ollama. Returns None if Ollama is unreachable or
        embed model is unavailable, allowing callers to fall back cleanly.
        """
        if not texts:
            return []

        if cls._provider() == "disabled":
            return None
        if cls._provider() in {"openai-compatible", "hosted"}:
            if not (settings.AI_API_BASE_URL and settings.AI_API_KEY and settings.AI_EMBED_MODEL):
                return None
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    res = await client.post(
                        f"{settings.AI_API_BASE_URL.rstrip('/')}/embeddings",
                        headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
                        json={"model": settings.AI_EMBED_MODEL, "input": texts},
                    )
                    res.raise_for_status()
                    data = res.json().get("data", [])
                    embeddings = [row.get("embedding") for row in data]
                    return embeddings if len(embeddings) == len(texts) else None
            except Exception as exc:
                logger.info("Hosted embeddings unavailable (%s).", type(exc).__name__)
                return None
        if cls._provider() != "ollama" or not settings.OLLAMA_BASE_URL:
            return None

        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        embed_model = settings.OLLAMA_EMBED_MODEL

        # Try /api/embed first (Ollama v0.1.44+)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                embed_res = await client.post(
                    f"{base_url}/api/embed",
                    json={"model": embed_model, "input": texts}
                )
                if embed_res.status_code == 200:
                    data = embed_res.json()
                    embeddings = data.get("embeddings", [])
                    if len(embeddings) == len(texts):
                        return embeddings

                # Fallback to single-item /api/embeddings endpoint
                results = []
                for t in texts:
                    res = await client.post(
                        f"{base_url}/api/embeddings",
                        json={"model": embed_model, "prompt": t}
                    )
                    if res.status_code == 200:
                        results.append(res.json().get("embedding", []))
                    else:
                        return None
                return results if len(results) == len(texts) else None
        except Exception as e:
            logger.debug(f"Ollama embeddings unavailable ({e}); falling back to local vectors.")
            return None
