from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional

class BaseAIProvider(ABC):
    """
    Interface abstrata para desacoplar provedores de IA (Google Gemini, OpenAI, Claude, Mock, etc.)
    Garante que a substituição de provedores futuros ocorra sem reescrever serviços financeiros,
    autenticação ou interfaces do Finnk.
    """

    @abstractmethod
    def generate_reply(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, str]:
        """
        Executa a geração de resposta a partir do prompt e contexto fornecido.
        Retorna:
            Tuple[str, str]: (conteúdo_da_resposta, identificador_do_provedor)
        """
        pass
