"""Groq AI service for chat completions using llama-3.3-70b-versatile model."""

import os
from typing import Dict, List, Optional, AsyncGenerator
from groq import Groq
import asyncio
import random
from ..config.settings import settings


class GroqService:
    """Service for Groq AI API integration."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Groq service with API key."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or self._get_fallback_key()
        if not self.api_key:
            raise ValueError("Groq API key is required")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama3-70b-8192"  # Using LLaMA3-70B as specified
    
    def _get_fallback_key(self) -> Optional[str]:
        """Get a random fallback API key from the configured keys."""
        if settings.fallback_groq_keys:
            return random.choice(settings.fallback_groq_keys)
        return None
    
    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: int = 1024,
        top_p: float = 1.0,
        stream: bool = False,
        api_key: Optional[str] = None
    ) -> Dict:
        """Create a chat completion using Groq API."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            if stream:
                return await self._create_streaming_completion(
                    messages, temperature, max_tokens, top_p
                )
            else:
                # Add timeout to prevent hanging
                completion = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            top_p=top_p,
                            stream=False
                        )
                    ),
                    timeout=30.0  # 30 second timeout
                )
                
                return {
                    "id": completion.id,
                    "object": completion.object,
                    "created": completion.created,
                    "model": completion.model,
                    "choices": [{
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    } for choice in completion.choices],
                    "usage": {
                        "prompt_tokens": completion.usage.prompt_tokens,
                        "completion_tokens": completion.usage.completion_tokens,
                        "total_tokens": completion.usage.total_tokens
                    }
                }
                
        except asyncio.TimeoutError:
            # If using fallback key and it times out, try another one
            if not api_key and settings.fallback_groq_keys:
                return await self._retry_with_different_key(messages, temperature, max_tokens, top_p, stream)
            raise Exception("Groq API timeout - request took too long")
        except Exception as e:
            # If using fallback key and it fails, try another one
            if not api_key and settings.fallback_groq_keys:
                return await self._retry_with_different_key(messages, temperature, max_tokens, top_p, stream)
            raise Exception(f"Groq API error: {str(e)}")
    
    async def _create_streaming_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float
    ) -> AsyncGenerator[Dict, None]:
        """Create streaming chat completion."""
        try:
            # Create the streaming completion with timeout
            loop = asyncio.get_event_loop()
            completion = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        stream=True
                    )
                ),
                timeout=10.0  # 10 second timeout for stream initiation
            )
            
            # Process chunks in an async manner
            for chunk in completion:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield {
                            "id": chunk.id,
                            "object": chunk.object,
                            "created": chunk.created,
                            "model": chunk.model,
                            "choices": [{
                                "index": chunk.choices[0].index,
                                "delta": {
                                    "content": delta.content or ""
                                },
                                "finish_reason": chunk.choices[0].finish_reason
                            }]
                        }
                        # Yield control to the event loop
                        await asyncio.sleep(0)
                    
        except Exception as e:
            raise Exception(f"Groq streaming error: {str(e)}")
    
    async def _retry_with_different_key(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        stream: bool
    ):
        """Retry the request with a different fallback key."""
        # Get a different fallback key
        available_keys = [k for k in settings.fallback_groq_keys if k != self.api_key]
        if not available_keys:
            raise Exception("All fallback API keys exhausted")
        
        # Try with a different key
        new_key = random.choice(available_keys)
        self.api_key = new_key
        self.client = Groq(api_key=new_key)
        
        # Retry the request
        return await self.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream
        )
    
    async def validate_api_key(self) -> bool:
        """Validate the Groq API key."""
        try:
            # Test with a simple completion
            test_messages = [{"role": "user", "content": "Hello"}]
            await self.create_chat_completion(
                messages=test_messages,
                max_tokens=5
            )
            return True
        except Exception:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Groq models."""
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile", 
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
    
    def get_model_info(self) -> Dict:
        """Get information about the current model."""
        return {
            "model": self.model,
            "provider": "groq",
            "max_tokens": 8192,
            "context_window": 8192,
            "description": "Llama 3.3 70B Versatile - Advanced reasoning and instruction following"
        }


# Global instance
groq_service: Optional[GroqService] = None


def get_groq_service(api_key: Optional[str] = None) -> GroqService:
    """Get or create Groq service instance."""
    global groq_service
    
    if groq_service is None or (api_key and api_key != groq_service.api_key):
        groq_service = GroqService(api_key)
    
    return groq_service


async def create_groq_completion(
    messages: List[Dict[str, str]],
    api_key: Optional[str] = None,
    **kwargs
) -> Dict:
    """Create a Groq completion with the specified configuration."""
    service = get_groq_service(api_key)
    
    # Default parameters matching your specification
    completion_params = {
        "temperature": 1.0,
        "max_tokens": 1024,
        "top_p": 1.0,
        "stream": False
    }
    completion_params.update(kwargs)
    
    return await service.create_chat_completion(messages, **completion_params)


async def create_groq_stream(
    messages: List[Dict[str, str]],
    api_key: Optional[str] = None,
    **kwargs
) -> AsyncGenerator[Dict, None]:
    """Create a streaming Groq completion."""
    service = get_groq_service(api_key)
    
    # Default parameters matching your specification
    completion_params = {
        "temperature": 1.0,
        "max_tokens": 1024,
        "top_p": 1.0,
        "stream": True
    }
    completion_params.update(kwargs)
    
    async for chunk in service._create_streaming_completion(
        messages,
        completion_params["temperature"],
        completion_params["max_tokens"], 
        completion_params["top_p"]
    ):
        yield chunk