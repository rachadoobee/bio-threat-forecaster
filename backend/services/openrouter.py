import httpx
import json
from typing import Optional
from config import get_settings

settings = get_settings()

class OpenRouterClient:
    """Client for OpenRouter API."""
    
    def __init__(self, model: Optional[str] = None):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = model or settings.DEFAULT_MODEL
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> str:
        """Send a completion request and return the text response."""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://biosecurity-forecaster.local",
                    "X-Title": "Biosecurity Threat Forecaster"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=90.0
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    
    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.2
    ) -> dict:
        """Send a completion request and parse JSON response."""
        
        json_system = (system_prompt or "") + "\n\nRespond ONLY with valid JSON. No markdown, no explanation."
        text = await self.complete(prompt, json_system, max_tokens, temperature)
        
        # Clean potential markdown wrapping
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())


# Singleton instance
_client: Optional[OpenRouterClient] = None

def get_llm_client() -> OpenRouterClient:
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client