"""LLM service for generating explanations."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, List, Dict, Any
import logging

from openai import AsyncOpenAI

from config import get_settings

logger = logging.getLogger(__name__)

# System prompt for all providers
SYSTEM_PROMPT = "You are a helpful assistant that explains social media posts by providing clear, factual context."


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    name: str = "base"
    
    @abstractmethod
    async def generate(self, prompt: str, image_data: Optional[dict] = None) -> str:
        """Generate a complete response."""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, image_data: Optional[dict] = None) -> AsyncGenerator[str, None]:
        """Stream response chunks."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider with vision support."""
    
    name = "openai"
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    def _build_messages(self, prompt: str, image_data: Optional[dict] = None) -> List[Dict[str, Any]]:
        """Build messages array, optionally with image."""
        if image_data:
            # Vision request with image
            content = [
                {"type": "text", "text": prompt},
                image_data
            ]
        else:
            content = prompt
        
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
    
    async def generate(self, prompt: str, image_data: Optional[dict] = None) -> str:
        """
        Generate a complete response, optionally with image analysis.
        
        Args:
            prompt: The prompt to send to the model
            image_data: Optional image data for vision
            
        Returns:
            The generated text response
        """
        settings = get_settings()
        messages = self._build_messages(prompt, image_data)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {str(e)}")
            raise
    
    async def stream(self, prompt: str, image_data: Optional[dict] = None) -> AsyncGenerator[str, None]:
        """
        Stream response chunks.
        
        Args:
            prompt: The prompt to send to the model
            image_data: Optional image data for vision
            
        Yields:
            Text chunks as they are generated
        """
        settings = get_settings()
        messages = self._build_messages(prompt, image_data)
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider with vision support."""
    
    name = "anthropic"
    
    # Model fallback list - try these in order
    MODEL_FALLBACKS = [
        "claude-3-5-sonnet-20241022",  # Latest
        "claude-3-5-sonnet-20240620",  # Previous version
        "claude-3-opus-20240229",      # Most powerful
        "claude-3-sonnet-20240229",    # Balanced
        "claude-3-haiku-20240307",     # Fastest
    ]
    
    def __init__(self, api_key: str, model: str = None):
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=api_key)
            # Use provided model or first fallback
            self.model = model or self.MODEL_FALLBACKS[0]
            self.available = True
        except ImportError:
            logger.warning("anthropic package not installed")
            self.available = False
            self.model = None
    
    def _build_content(self, prompt: str, image_data: Optional[dict] = None) -> List[Dict[str, Any]]:
        """Build content array for Claude."""
        content = []
        
        if image_data and image_data.get("image_url", {}).get("url", "").startswith("data:"):
            # Extract base64 from data URL
            data_url = image_data["image_url"]["url"]
            # Format: data:image/jpeg;base64,<base64_data>
            media_type = data_url.split(";")[0].split(":")[1]
            base64_data = data_url.split(",")[1]
            
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_data
                }
            })
        
        content.append({"type": "text", "text": prompt})
        return content
    
    async def generate(self, prompt: str, image_data: Optional[dict] = None) -> str:
        """Generate a complete response with optional image."""
        if not self.available:
            raise RuntimeError("Anthropic provider not available")
        
        settings = get_settings()
        content = self._build_content(prompt, image_data)
        
        # Try models in fallback order
        last_error = None
        for model in self.MODEL_FALLBACKS:
            try:
                response = await self.client.messages.create(
                    model=model,
                    max_tokens=settings.max_tokens,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": content}]
                )
                
                # Success - update self.model for future use
                self.model = model
                return response.content[0].text
                
            except Exception as e:
                last_error = e
                # If it's not a 404, don't try other models
                if "404" not in str(e) and "not_found" not in str(e).lower():
                    logger.error(f"Anthropic generation error with {model}: {str(e)}")
                    raise
                # Otherwise, try next model
                logger.warning(f"Model {model} not available, trying next...")
                continue
        
        # All models failed
        logger.error(f"All Anthropic models failed. Last error: {last_error}")
        raise RuntimeError(f"Failed to generate with any Claude model: {last_error}")
    
    async def stream(self, prompt: str, image_data: Optional[dict] = None) -> AsyncGenerator[str, None]:
        """Stream response chunks."""
        if not self.available:
            raise RuntimeError("Anthropic provider not available")
        
        settings = get_settings()
        content = self._build_content(prompt, image_data)
        
        # Try models in fallback order
        last_error = None
        for model in self.MODEL_FALLBACKS:
            try:
                async with self.client.messages.stream(
                    model=model,
                    max_tokens=settings.max_tokens,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": content}]
                ) as stream:
                    # Success - update self.model
                    self.model = model
                    async for text in stream.text_stream:
                        yield text
                    return  # Success, exit
                    
            except Exception as e:
                last_error = e
                # If it's not a 404, don't try other models
                if "404" not in str(e) and "not_found" not in str(e).lower():
                    logger.error(f"Anthropic streaming error with {model}: {str(e)}")
                    raise
                # Otherwise, try next model
                logger.warning(f"Model {model} not available for streaming, trying next...")
                continue
        
        # All models failed
        logger.error(f"All Anthropic models failed for streaming. Last error: {last_error}")
        raise RuntimeError(f"Failed to stream with any Claude model: {last_error}")


class LLMService:
    """Main LLM service that manages multiple providers."""
    
    def __init__(self):
        settings = get_settings()
        
        # Primary provider (OpenAI)
        self.openai_provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
        
        # Optional Claude provider
        self.anthropic_provider: Optional[AnthropicProvider] = None
        if settings.anthropic_api_key:
            self.anthropic_provider = AnthropicProvider(
                api_key=settings.anthropic_api_key
            )
        
        # Default provider
        self.provider = self.openai_provider
    
    def get_provider(self, name: str = "openai") -> LLMProvider:
        """Get a specific provider by name."""
        if name == "anthropic" and self.anthropic_provider:
            return self.anthropic_provider
        return self.openai_provider
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        providers = ["openai"]
        if self.anthropic_provider and self.anthropic_provider.available:
            providers.append("anthropic")
        return providers
    
    async def generate(self, prompt: str, image_data: Optional[dict] = None) -> str:
        """Generate a complete response."""
        return await self.provider.generate(prompt, image_data)
    
    async def stream(self, prompt: str, image_data: Optional[dict] = None) -> AsyncGenerator[str, None]:
        """Stream response chunks."""
        async for chunk in self.provider.stream(prompt, image_data):
            yield chunk
    
    async def generate_with_provider(
        self, 
        prompt: str, 
        provider_name: str,
        image_data: Optional[dict] = None
    ) -> str:
        """Generate with a specific provider."""
        provider = self.get_provider(provider_name)
        return await provider.generate(prompt, image_data)
    
    async def compare_providers(
        self, 
        prompt: str,
        image_data: Optional[dict] = None
    ) -> Dict[str, str]:
        """
        Generate responses from all available providers.
        
        Returns:
            Dict mapping provider name to response
        """
        results = {}
        
        for provider_name in self.get_available_providers():
            try:
                provider = self.get_provider(provider_name)
                response = await provider.generate(prompt, image_data)
                results[provider_name] = response
            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {e}")
                results[provider_name] = f"Error: {str(e)}"
        
        return results

