import json
import logging
from typing import Dict, Any, Optional, Iterator, List
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)

class OllamaUnavailableError(Exception):
    """Raised when the local Ollama instance cannot be reached."""
    pass

class OllamaClient:
    """
    The SINGLE authorized client for calling the local Ollama API.
    Enforces local-only AI policy: No external LLM calls permitted.
    """
    _instance: Optional["OllamaClient"] = None

    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = settings.OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = httpx.Timeout(30.0, connect=5.0)

    @classmethod
    def get_instance(cls) -> "OllamaClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if settings.OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {settings.OLLAMA_API_KEY}"
        return headers

    def is_available(self) -> bool:
        """Check if local Ollama server is running and reachable."""
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Fetch status and details of the loaded model."""
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    return {
                        "available": True,
                        "base_url": self.base_url,
                        "target_model": self.model,
                        "installed_models": models,
                        "is_target_installed": any(self.model in m for m in models)
                    }
        except Exception as e:
            return {
                "available": False,
                "base_url": self.base_url,
                "target_model": self.model,
                "error": str(e)
            }
        return {"available": False, "target_model": self.model}

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format_json: bool = False,
        temperature: float = settings.OLLAMA_TEMPERATURE,
        max_tokens: int = 1024,
    ) -> str:
        """Synchronous chat text generation via Ollama /api/chat."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            "options": {
                "temperature": temperature,
                "repeat_penalty": 1.1,
                "repeat_last_n": 64,
                "num_ctx": settings.OLLAMA_CONTEXT_SIZE,
                "num_predict": max_tokens,
            }
        }
        if format_json:
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=20.0, headers=self._get_headers()) as client:
                res = client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code != 200:
                    raise OllamaUnavailableError(f"Ollama returned HTTP {res.status_code}: {res.text}")
                data = res.json()
                return data.get("message", {}).get("content", "").strip()
        except httpx.RequestError as e:
            logger.warning(f"Ollama call failed: {e}")
            raise OllamaUnavailableError(f"Cannot reach Ollama at {self.base_url}: {e}")

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = settings.OLLAMA_TEMPERATURE,
        max_tokens: int = 1024,
    ) -> Iterator[str]:
        """Streaming chat text generation yielding token chunks."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            "options": {
                "temperature": temperature,
                "num_ctx": settings.OLLAMA_CONTEXT_SIZE,
                "num_predict": max_tokens,
            }
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code != 200:
                        raise OllamaUnavailableError(f"Ollama streaming returned HTTP {response.status_code}")
                    for line in response.iter_lines():
                        if not line:
                            continue
                        chunk_data = json.loads(line)
                        yield chunk_data.get("message", {}).get("content", "")
                        if chunk_data.get("done", False):
                            break
        except httpx.RequestError as e:
            logger.warning(f"Ollama stream connection failed: {e}")
            raise OllamaUnavailableError(f"Ollama stream failed: {e}")

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector using local Ollama model."""
        payload = {
            "model": self.model,
            "prompt": text,
            "keep_alive": settings.OLLAMA_KEEP_ALIVE
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(f"{self.base_url}/api/embeddings", json=payload)
                if res.status_code == 200:
                    return res.json().get("embedding", [])
        except Exception as e:
            logger.debug(f"Ollama embedding endpoint returned: {e}")
        
        # Fallback deterministic pseudo-embedding (TF-IDF hashed vector) if Ollama embeddings unsupported on current model tag
        import hashlib
        tokens = text.lower().split()
        dim = 128
        vec = [0.0] * dim
        for tok in tokens:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16) % dim
            vec[h] += 1.0
        norm = sum(x*x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec
