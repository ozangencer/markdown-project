"""
AI Provider abstraction layer for different LLM providers
"""
import os
from abc import ABC, abstractmethod
from openai import OpenAI
from typing import Dict
import google.generativeai as genai

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured"""
        pass
    
    @abstractmethod
    def chat_completion(self, messages: list, max_tokens: int = 1500) -> str:
        """Generate chat completion"""
        pass
    
    @abstractmethod
    def get_client_for_markitdown(self):
        """Get client instance compatible with MarkItDown"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name to use"""
        pass
    
    @abstractmethod
    def process_image(self, image_path: str, prompt: str = None) -> str:
        """Process image file and return description"""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI provider implementation"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-4o"
    
    def is_available(self) -> bool:
        return self.api_key is not None and self.client is not None
    
    def chat_completion(self, messages: list, max_tokens: int = 1500) -> str:
        if not self.is_available():
            raise Exception("OpenAI API key is not configured")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def get_client_for_markitdown(self):
        return self.client
    
    def get_model_name(self) -> str:
        return self.model
    
    def process_image(self, image_path: str, prompt: str = None) -> str:
        """OpenAI ile MarkItDown kullanarak görüntü işleme"""
        from markitdown import MarkItDown
        
        markitdown = MarkItDown(llm_client=self.client, llm_model=self.model)
        if prompt:
            result = markitdown.convert(image_path, llm_prompt=prompt)
        else:
            result = markitdown.convert(image_path)
        return result.text_content

class DeepSeekProvider(AIProvider):
    """DeepSeek provider implementation (OpenAI compatible)"""
    
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = "https://api.deepseek.com"
        self.client = OpenAI(
            api_key=self.api_key, 
            base_url=self.base_url
        ) if self.api_key else None
        self.model = "deepseek-chat"  # DeepSeek's main model
    
    def is_available(self) -> bool:
        return self.api_key is not None and self.client is not None
    
    def chat_completion(self, messages: list, max_tokens: int = 1500) -> str:
        if not self.is_available():
            raise Exception("DeepSeek API key is not configured")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def get_client_for_markitdown(self):
        return self.client
    
    def get_model_name(self) -> str:
        return self.model
    
    def process_image(self, image_path: str, prompt: str = None) -> str:
        """DeepSeek görüntü işleme desteklemiyor"""
        # Parametreler kullanılmıyor ama interface uyumluluğu için gerekli
        _ = image_path, prompt
        raise Exception("DeepSeek V3 does not support image processing yet. Please use OpenAI or Google providers for image analysis. DeepSeek-VL2 (vision model) is coming soon to the API.")

class GoogleProvider(AIProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model_name = "gemini-2.0-flash"
            try:
                self.model = genai.GenerativeModel(self.model_name)
            except Exception:
                self.model = None
        else:
            self.model = None
    
    def is_available(self) -> bool:
        return self.api_key is not None and self.model is not None
    
    def chat_completion(self, messages: list, max_tokens: int = 1500) -> str:
        if not self.is_available():
            raise Exception("Google API key is not configured")
        
        # Google Gemini format farklı - messages'i tek prompt'a çeviriyoruz
        conversation = ""
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                conversation += f"Instructions: {content}\n\n"
            elif role == "user":
                conversation += f"User: {content}\n\n"
            elif role == "assistant":
                conversation += f"Assistant: {content}\n\n"
        
        # Son user message'ını ayrı olarak gönder
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            prompt = conversation + f"Please respond to: {user_messages[-1]['content']}"
        else:
            prompt = conversation
        
        try:
            # Google Gemini API call
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")
    
    def get_client_for_markitdown(self):
        # Google Gemini'nin MarkItDown ile direkt entegrasyonu yok
        # Bu durumda OpenAI wrapper'ı kullanabiliriz veya None döneriz
        return None
    
    def process_image(self, image_path: str, prompt: str = None) -> str:
        """Google Gemini ile görüntü işleme"""
        if not self.is_available():
            raise Exception("Google API key is not configured")
        
        try:
            import PIL.Image
            
            # Görüntüyü yükle
            image = PIL.Image.open(image_path)
            
            # Varsayılan prompt - sadece Google provider için dahili kullanım
            if not prompt:
                prompt = """Analyze this image and provide a detailed description in markdown format. 
                What do you see in the image? If there is text, read and include it. 
                Describe the type, content and important details of the image."""
            
            # Gemini Vision model ile işle - safety settings tamamen devre dışı
            response = self.model.generate_content(
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.1
                )
            )
            
            # Response kontrolü ve güvenlik filtresi kontrolü
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    if candidate.finish_reason == 2:  # SAFETY
                        # Güvenlik filtresinin hangi kategorisini tetiklediğini kontrol et
                        safety_ratings = getattr(candidate, 'safety_ratings', [])
                        blocked_categories = []
                        for rating in safety_ratings:
                            if hasattr(rating, 'category') and hasattr(rating, 'probability'):
                                if rating.probability in ['HIGH', 'MEDIUM']:
                                    blocked_categories.append(rating.category.name)
                        
                        if blocked_categories:
                            blocked_list = ', '.join(blocked_categories)
                            raise Exception(f"Content was blocked by Google's safety filters ({blocked_list}). This content appears to violate Google's policy. Try using OpenAI provider for this image.")
                        else:
                            raise Exception("Content was blocked by Google's safety filters. Try using OpenAI provider for this image.")
                    elif candidate.finish_reason == 3:  # RECITATION
                        raise Exception("Content was blocked due to recitation concerns.")
            
            # Text içeriğini güvenli şekilde al
            try:
                if hasattr(response, 'text') and response.text:
                    return response.text
            except ValueError:
                # response.text accessor failed, try manual extraction
                pass
            
            # Fallback: parts'tan text çıkar
            if hasattr(response, 'parts') and response.parts:
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text'):
                        text_parts.append(part.text)
                
                if text_parts:
                    return ''.join(text_parts)
            
            # Son fallback: candidates'tan text çıkar
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                text_parts.append(part.text)
                        if text_parts:
                            return ''.join(text_parts)
            
            raise Exception("Google API response contains no text content.")
            
        except Exception as e:
            raise Exception(f"Google image processing error: {str(e)}")
    
    def get_model_name(self) -> str:
        return self.model_name

class AIProviderFactory:
    """Factory class to manage AI providers"""
    
    providers = {
        'openai': OpenAIProvider,
        'deepseek': DeepSeekProvider,
        'google': GoogleProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_name: str = None) -> AIProvider:
        """Get AI provider instance"""
        # If no provider specified, use environment variable or default
        if not provider_name:
            provider_name = os.getenv('AI_PROVIDER', 'openai').lower()
        
        if provider_name not in cls.providers:
            raise ValueError(f"Unknown AI provider: {provider_name}. Available: {list(cls.providers.keys())}")
        
        provider = cls.providers[provider_name]()
        
        if not provider.is_available():
            # Try to fallback to other available providers
            for fallback_name, fallback_class in cls.providers.items():
                if fallback_name != provider_name:
                    fallback_provider = fallback_class()
                    if fallback_provider.is_available():
                        return fallback_provider
            
            raise Exception(f"No AI provider is properly configured. Please set API keys for: {list(cls.providers.keys())}")
        
        return provider
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, bool]:
        """Get list of available providers and their status"""
        status = {}
        for name, provider_class in cls.providers.items():
            provider = provider_class()
            status[name] = provider.is_available()
        return status
    
    @classmethod
    def add_provider(cls, name: str, provider_class: type):
        """Add a new provider to the factory"""
        cls.providers[name] = provider_class