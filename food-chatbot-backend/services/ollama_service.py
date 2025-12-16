"""
Ollama LLM service for text generation.
"""
import httpx
from typing import List, Dict, Any, Optional
from config import settings


class OllamaService:
    """Interface to Ollama API for LLM operations."""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = httpx.Timeout(120.0)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            context: Conversation context
            temperature: Generation temperature
            
        Returns:
            Generated text
        """
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add context
        if context:
            messages.extend(context)
        
        # Add current prompt
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["message"]["content"]
            except Exception as e:
                print(f"Ollama API error: {e}")
                raise
    
    async def check_health(self) -> bool:
        """
        Check if Ollama service is available.
        
        Returns:
            True if service is healthy
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
            except:
                return False


# Global instance
ollama_service = OllamaService()
