"""
Configuration settings for Google's Gemini API integration.
"""
import os
from typing import Dict, Optional
from pydantic import BaseModel, Field, SecretStr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiConfig(BaseModel):
    """Configuration for Google's Gemini API integration."""
    
    # API Settings
    api_key: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("GEMINI_API_KEY", "")),
        description="Gemini API key"
    )
    model: str = Field(
        default=os.getenv("GEMINI_MODEL", "gemini-pro"),
        description="Gemini model to use"
    )
    
    # Generation Settings
    temperature: float = Field(
        default=float(os.getenv("TEMPERATURE", "0.7")),
        description="Temperature for generation (0-1)"
    )
    max_tokens: int = Field(
        default=int(os.getenv("MAX_TOKENS", "4000")),
        description="Maximum tokens per request"
    )
    top_p: float = Field(
        default=float(os.getenv("TOP_P", "0.95")),
        description="Nucleus sampling parameter (0-1)"
    )
    top_k: int = Field(
        default=int(os.getenv("TOP_K", "40")),
        description="Top-k sampling parameter"
    )
    
    # Safety Settings
    safety_settings: Dict[str, str] = Field(
        default_factory=lambda: {
            "HARM_CATEGORY_HARASSMENT": os.getenv("HARM_CATEGORY_HARASSMENT", "BLOCK_NONE"),
            "HARM_CATEGORY_HATE_SPEECH": os.getenv("HARM_CATEGORY_HATE_SPEECH", "BLOCK_NONE"),
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": os.getenv("HARM_CATEGORY_SEXUALLY_EXPLICIT", "BLOCK_NONE"),
            "HARM_CATEGORY_DANGEROUS_CONTENT": os.getenv("HARM_CATEGORY_DANGEROUS_CONTENT", "BLOCK_NONE")
        },
        description="Safety settings for Gemini model"
    )
    
    # API Configuration
    use_api: bool = Field(
        default=os.getenv("USE_API", "true").lower() == "true",
        description="Whether to use API for LLM integration"
    )
    api_base_url: Optional[str] = Field(
        default=os.getenv("API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
        description="Base URL for API"
    )
    
    def get_api_config(self) -> Dict[str, any]:
        """Return the API configuration for Gemini."""
        return {
            "api_key": self.api_key.get_secret_value(),
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "safety_settings": self.safety_settings,
            "api_base_url": self.api_base_url
        }
    
    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """Create configuration from environment variables."""
        return cls() 