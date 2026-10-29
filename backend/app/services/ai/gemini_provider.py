import httpx
from typing import List, Dict, Tuple, Optional
from fastapi import HTTPException, status
from .base import BaseAIProvider

class GeminiAIProvider(BaseAIProvider):
    """
    Integração segura com a Google Gemini API (Modalidade Gratuita).
    Utiliza endpoint REST v1beta oficial com controle de cotas, timeout e tratamento robusto de erros.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-1.5-flash",
        temperature: float = 0.3,
        max_output_tokens: int = 800,
        timeout_seconds: float = 15.0
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.timeout_seconds = timeout_seconds

    def generate_reply(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, str]:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="A chave GEMINI_API_KEY não está configurada no ambiente do servidor. A assistência com IA está temporariamente indisponível."
            )

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        # Monta histórico de mensagens anteriores limitando o tamanho
        contents = []
        if history:
            for item in history[-6:]:  # Limita aos últimos 6 turnos para economizar tokens
                role = "user" if item.get("role") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": item.get("content", "")}]
                })

        # Adiciona o prompt atual do usuário
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens
            }
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(endpoint, json=payload)

            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return (
                        "Não foi possível obter uma resposta detalhada no momento. Por favor, tente reformular sua pergunta.",
                        f"gemini/{self.model_name}"
                    )
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts and "text" in parts[0]:
                    return (parts[0]["text"].strip(), f"gemini/{self.model_name}")
                return (
                    "O assistente analisou seus dados, mas não gerou texto adicional. Como posso ajudar com outra dúvida financeira?",
                    f"gemini/{self.model_name}"
                )

            elif response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="A cota gratuita temporária da API de IA foi atingida. Por favor, aguarde alguns instantes e tente novamente. Suas funcionalidades financeiras continuam disponíveis normalmente!"
                )
            elif response.status_code in [401, 403]:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="A credencial configurada para o serviço de IA é inválida ou expirou. Contate o administrador do sistema."
                )
            elif response.status_code == 400:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A solicitação não pôde ser processada pelo modelo de IA. Tente enviar uma mensagem mais curta."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="O serviço de IA está temporariamente indisponível. Suas informações financeiras permanecem intactas."
                )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Tempo limite excedido na comunicação com o provedor de IA. Por favor, tente novamente em instantes."
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ocorreu uma falha na conexão com a inteligência artificial. Tente novamente mais tarde."
            )
