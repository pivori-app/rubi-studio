"""
Abstraction des fournisseurs LLM pour Rubi Studio
Support pour OpenAI, Gemini, Claude
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import logging
from openai import AsyncOpenAI
import google.generativeai as genai
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Classe abstraite pour les fournisseurs LLM"""
    
    @abstractmethod
    async def execute(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Exécuter un prompt avec le LLM
        
        Returns:
            Dict contenant:
            - output: str - Le texte généré
            - tokens_used: int - Nombre de tokens utilisés
            - model: str - Modèle utilisé
        """
        pass
    
    @abstractmethod
    def calculate_cost(self, tokens: int, model: str) -> float:
        """Calculer le coût en USD pour un nombre de tokens"""
        pass


class OpenAIProvider(LLMProvider):
    """Provider pour OpenAI (GPT-4, GPT-3.5, etc.)"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Tarifs par modèle (USD par 1000 tokens)
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        }
    
    async def execute(
        self,
        prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "output": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": model
            }
        except Exception as e:
            logger.error(f"OpenAI execution error: {str(e)}")
            raise
    
    def calculate_cost(self, tokens: int, model: str) -> float:
        if model not in self.pricing:
            # Utiliser le tarif de gpt-4 par défaut
            model = "gpt-4"
        
        # Approximation: 75% input, 25% output
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        cost = (
            (input_tokens / 1000) * self.pricing[model]["input"] +
            (output_tokens / 1000) * self.pricing[model]["output"]
        )
        return round(cost, 6)


class GeminiProvider(LLMProvider):
    """Provider pour Google Gemini"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        
        # Tarifs Gemini (USD par 1000 tokens)
        self.pricing = {
            "gemini-pro": {"input": 0.00025, "output": 0.0005},
            "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},
        }
    
    async def execute(
        self,
        prompt: str,
        model: str = "gemini-pro",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            model_instance = genai.GenerativeModel(model)
            response = await model_instance.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            # Estimation des tokens (Gemini ne fournit pas toujours le compte exact)
            tokens_used = len(prompt.split()) + len(response.text.split())
            
            return {
                "output": response.text,
                "tokens_used": tokens_used,
                "model": model
            }
        except Exception as e:
            logger.error(f"Gemini execution error: {str(e)}")
            raise
    
    def calculate_cost(self, tokens: int, model: str) -> float:
        if model not in self.pricing:
            model = "gemini-pro"
        
        # Approximation: 75% input, 25% output
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        cost = (
            (input_tokens / 1000) * self.pricing[model]["input"] +
            (output_tokens / 1000) * self.pricing[model]["output"]
        )
        return round(cost, 6)


class ClaudeProvider(LLMProvider):
    """Provider pour Anthropic Claude"""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = AsyncAnthropic(api_key=api_key)
        
        # Tarifs Claude (USD par 1000 tokens)
        self.pricing = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        }
    
    async def execute(
        self,
        prompt: str,
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024
    ) -> Dict[str, Any]:
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                "output": response.content[0].text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "model": model
            }
        except Exception as e:
            logger.error(f"Claude execution error: {str(e)}")
            raise
    
    def calculate_cost(self, tokens: int, model: str) -> float:
        if model not in self.pricing:
            model = "claude-3-sonnet-20240229"
        
        # Approximation: 75% input, 25% output
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        cost = (
            (input_tokens / 1000) * self.pricing[model]["input"] +
            (output_tokens / 1000) * self.pricing[model]["output"]
        )
        return round(cost, 6)


class LLMFactory:
    """Factory pour obtenir le bon provider LLM"""
    
    _providers = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
    }
    
    @classmethod
    def get_provider(cls, name: str) -> LLMProvider:
        """
        Obtenir une instance du provider LLM
        
        Args:
            name: Nom du provider ("openai", "gemini", "claude")
        
        Returns:
            Instance du provider
        
        Raises:
            ValueError: Si le provider n'existe pas
        """
        if name not in cls._providers:
            raise ValueError(
                f"Unknown LLM provider: {name}. "
                f"Available providers: {', '.join(cls._providers.keys())}"
            )
        
        return cls._providers[name]()
    
    @classmethod
    def list_providers(cls) -> list:
        """Liste des providers disponibles"""
        return list(cls._providers.keys())

