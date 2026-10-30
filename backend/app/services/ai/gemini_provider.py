import logging
import httpx
import re
from typing import List, Dict, Tuple, Optional
from fastapi import HTTPException, status
from .base import BaseAIProvider

logger = logging.getLogger("finnk.ai.gemini")

def clean_markdown_artifacts(text: str) -> str:
    """Remove marcações visuais de asteriscos para garantir texto limpo e legível."""
    if not text:
        return ""
    # Transforma bullets de asterisco em traços: '* Item' -> '- Item'
    text = re.sub(r'^[ \t]*\*[ \t]+', '- ', text, flags=re.MULTILINE)
    # Remove asteriscos duplos de negrito: '**R$ 0,00**' -> 'R$ 0,00'
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove asteriscos simples remanescentes
    text = text.replace('*', '')
    return text.strip()

class GeminiAIProvider(BaseAIProvider):
    """
    Integração segura com a Google Gemini API (Modalidade Gratuita).
    Utiliza endpoint REST v1beta oficial com controle de cotas, timeout e tratamento robusto de erros.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-3.5-flash-lite",
        temperature: float = 0.3,
        max_output_tokens: int = 800,
        timeout_seconds: float = 22.0
    ):
        self.api_key = (api_key or "").strip()
        # Normaliza o nome do modelo removendo prefixos redundantes
        raw_model = (model_name or "gemini-3.5-flash-lite").strip()
        cleaned = raw_model.replace("models/", "")
        # Mapeia versões antigas/retiradas para a geração 3.x suportada
        if cleaned in ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.0-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"]:
            cleaned = "gemini-3.5-flash-lite"
        self.model_name = cleaned
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.timeout_seconds = timeout_seconds

    def _call_gemini_api(self, model: str, payload: dict, timeout: float = None) -> Tuple[Optional[dict], int, str]:
        """Executa a chamada HTTP para o endpoint da Google Generative Language API."""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        eff_timeout = timeout or self.timeout_seconds

        try:
            with httpx.Client(timeout=eff_timeout) as client:
                response = client.post(endpoint, json=payload, headers=headers)
                status_code = response.status_code
                text = response.text
                try:
                    data = response.json()
                except Exception:
                    data = None
                return data, status_code, text
        except httpx.TimeoutException:
            logger.warning(f"Timeout na comunicação com a API do Gemini ({eff_timeout}s) no modelo {model}")
            return None, 408, f"Timeout na comunicação com o Gemini ({eff_timeout}s)"
        except Exception as e:
            logger.error(f"Exceção de rede ao conectar ao Gemini ({model}): {str(e)}")
            return None, 503, str(e)

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

        # Sequência de modelos prioritários para resiliência: modelo ultra-rápido primeiro, depois alternativas
        models_to_try = [self.model_name]
        for candidate in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash"]:
            if candidate not in models_to_try:
                models_to_try.append(candidate)

        last_status = 503
        last_error = ""
        active_model = self.model_name

        for model_cand in models_to_try:
            logger.info(f"Tentando geração com o modelo Gemini: {model_cand}")
            data, status_code, raw_text = self._call_gemini_api(model_cand, payload)
            last_status = status_code
            active_model = model_cand

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
                    cleaned_reply = clean_markdown_artifacts(parts[0]["text"])
                    return (cleaned_reply, f"gemini/{active_model}")
                return (
                    "O assistente analisou seus dados financeiros com sucesso. Como posso ajudar com outra dúvida?",
                    f"gemini/{active_model}"
                )

            # Extrai mensagem de erro para logs e diagnóstico
            if data and isinstance(data, dict):
                last_error = data.get("error", {}).get("message", "")
            if not last_error:
                last_error = raw_text[:200]

            logger.warning(f"Modelo {model_cand} falhou com status {status_code}: {last_error}")

            # Se for erro de autenticação (401/403) ou cota global (429), não adianta tentar outro modelo
            if status_code in [401, 403, 429]:
                break

        # Se nenhum modelo funcionou
        logger.error(f"Falha em todos os modelos Gemini testados. Último status: {last_status}, erro: {last_error}")

        if last_status == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Cota gratuita da API Gemini atingida: {last_error}. Aguarde um instante e tente novamente."
            )
        elif last_status in [401, 403]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"A credencial GEMINI_API_KEY no servidor é inválida ou não autorizada: {last_error}"
            )
        elif last_status == 408:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Tempo limite excedido na comunicação com a API do Gemini. Aguarde alguns instantes e tente novamente."
            )
        elif last_status == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requisição inválida para o Gemini: {last_error}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"O serviço Gemini retornou erro HTTP {last_status}: {last_error}"
            )
