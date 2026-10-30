from ...config import settings
from .base import BaseAIProvider
from .gemini_provider import GeminiAIProvider
from .mock_provider import MockAIProvider

def get_ai_provider() -> BaseAIProvider:
    """
    Factory para obter o provedor de IA ativo.
    Permite trocar para OpenAI, Anthropic ou modelo local no futuro apenas alterando
    a variável AI_PROVIDER ou instanciando a classe correspondente.
    """
    provider_type = (settings.AI_PROVIDER or "gemini").lower()

    if provider_type == "mock":
        return MockAIProvider(is_fallback=False)

    if provider_type == "gemini":
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            return GeminiAIProvider(
                api_key=settings.GEMINI_API_KEY.strip(),
                model_name=settings.GEMINI_MODEL or "gemini-2.5-flash",
                temperature=settings.AI_TEMPERATURE,
                max_output_tokens=settings.AI_MAX_OUTPUT_TOKENS
            )
        # Fallback seguro para demonstração caso chave ainda não esteja inserida
        return MockAIProvider(is_fallback=True)

    # Fallback padrão
    return MockAIProvider(is_fallback=True)

def is_gemini_configured() -> bool:
    """Retorna True se uma chave do Gemini estiver configurada no backend."""
    return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
