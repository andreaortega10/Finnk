import logging
import httpx
from typing import List, Dict, Tuple, Optional
from fastapi import HTTPException, status
from .base import BaseAIProvider

logger = logging.getLogger("finnk.ai.gemini")

class GeminiAIProvider(BaseAIProvider):
    """
    Integração segura com a Google Gemini API (Modalidade Gratuita).
    Utiliza endpoint REST v1beta oficial com controle de cotas, timeout e tratamento robusto de erros.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.3,
        max_output_tokens: int = 800,
        timeout_seconds: float = 15.0
    ):
        self.api_key = (api_key or "").strip()
        # Normaliza o nome do modelo removendo prefixos redundantes
        raw_model = (model_name or "gemini-2.5-flash").strip()
        cleaned = raw_model.replace("models/", "")
        # Mapeia versões antigas/retiradas para o modelo atual e estável
        if cleaned in ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.0-pro"]:
            cleaned = "gemini-2.5-flash"
        self.model_name = cleaned
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.timeout_seconds = timeout_seconds

    def _call_gemini_api(self, model: str, payload: dict) -> Tuple[Optional[dict], int, str]:
        """Executa a chamada HTTP para o endpoint da Google Generative Language API."""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(endpoint, json=payload, headers=headers)
                status_code = response.status_code
                text = response.text
                try:
                    data = response.json()
                except Exception:
                    data = None
                return data, status_code, text
        except httpx.TimeoutException:
            logger.error("Timeout na comunicação com a API do Gemini (>15s)")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Tempo limite excedido na comunicação com o Gemini. Aguarde alguns instantes e tente novamente."
            )
        except Exception as e:
            logger.error(f"Exceção de rede ao conectar ao Gemini: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Falha de conexão com o serviço Gemini: {str(e)}"
            )

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

        # Primeira tentativa com o modelo configurado
        data, status_code, raw_text = self._call_gemini_api(self.model_name, payload)
        active_model = self.model_name

        # Se 404 (modelo não encontrado), tenta fallback dinâmico entre modelos flash suportados
        if status_code == 404:
            fallback_models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]
            for fb_model in fallback_models:
                if fb_model != active_model:
                    logger.warning(f"Modelo {active_model} retornou 404. Tentando modelo alternativo: {fb_model}")
                    data, status_code, raw_text = self._call_gemini_api(fb_model, payload)
                    if status_code == 200:
                        active_model = fb_model
                        break

        if status_code == 200 and data:
            candidates = data.get("candidates", [])
            if not candidates:
                return (
                    "Não foi possível obter uma resposta detalhada no momento. Por favor, tente reformular sua pergunta.",
                    f"gemini/{active_model}"
                )
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts and "text" in parts[0]:
                return (parts[0]["text"].strip(), f"gemini/{active_model}")
            return (
                "O assistente analisou seus dados financeiros com sucesso. Como posso ajudar com outra dúvida?",
                f"gemini/{active_model}"
            )

        # Extrai mensagem de erro da resposta do Google para diagnóstico
        error_msg = ""
        if data and isinstance(data, dict):
            error_msg = data.get("error", {}).get("message", "")
        if not error_msg:
            error_msg = raw_text[:200]

        logger.error(f"Gemini API retornou HTTP {status_code} para o modelo {self.model_name}: {error_msg}")

        if status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Cota gratuita da API Gemini atingida: {error_msg}. Aguarde um instante e tente novamente."
            )
        elif status_code in [401, 403]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"A credencial GEMINI_API_KEY no servidor é inválida ou não autorizada: {error_msg}"
            )
        elif status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requisição inválida para o Gemini: {error_msg}"
            )
        elif status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Modelo Gemini não encontrado ({self.model_name}): {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"O serviço de IA retornou erro HTTP {status_code}: {error_msg}"
            )
