import re
from typing import List, Dict, Tuple, Optional
from .base import BaseAIProvider

class MockAIProvider(BaseAIProvider):
    """
    Provedor simulado para testes automatizados, demonstração acadêmica e fallback offline.
    Responde perguntas interpretando o contexto financeiro determinístico fornecido,
    garantindo que nunca inventa valores e espelha fielmente as regras do Finnk.
    """

    def __init__(self, is_fallback: bool = False):
        self.is_fallback = is_fallback

    def generate_reply(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, str]:
        p = prompt.lower()

        provider_name = "mock/demonstracao" if not self.is_fallback else "mock/fallback-demonstracao"

        # 1. Quanto gastei neste mês / despesas totais
        if any(w in p for w in ["quanto gastei", "total de gastos", "despesas deste mês", "despesas do mês"]):
            # Extrai total de despesas do system_prompt
            match = re.search(r"Total de Despesas no Período:\s*R\$\s*([\d\.,]+)", system_prompt)
            if match:
                val = match.group(1)
                paid_match = re.search(r"Despesas Pagas:\s*R\$\s*([\d\.,]+)", system_prompt)
                pend_match = re.search(r"Despesas Pendentes:\s*R\$\s*([\d\.,]+)", system_prompt)
                paid_val = paid_match.group(1) if paid_match else "0,00"
                pend_val = pend_match.group(1) if pend_match else "0,00"
                return (
                    f"Neste mês, você tem um total de R$ {val} em despesas registradas. "
                    f"Deste valor, R$ {paid_val} já foram efetivamente pagos e R$ {pend_val} ainda estão pendentes de pagamento.",
                    provider_name
                )
            return ("Não encontrei despesas registradas para o período selecionado.", provider_name)

        # 2. Categorias que concentram gastos
        if any(w in p for w in ["categoria", "categorias", "concentram", "maiores gastos"]):
            lines = [l.strip() for l in system_prompt.split("\n") if l.strip().startswith("- ")]
            cat_lines = [l for l in lines if "%" in l or "R$" in l]
            if cat_lines:
                cats_text = "\n".join(cat_lines[:4])
                return (
                    f"As categorias que mais concentram suas despesas no período são:\n\n{cats_text}\n\n"
                    "Recomendo monitorar especialmente a categoria de maior peso para manter o orçamento equilibrado.",
                    provider_name
                )
            return ("Não há despesas categorizadas suficientes neste período para gerar a distribuição.", provider_name)

        # 3. Comparação com o mês anterior / como mudaram
        if any(w in p for w in ["mês anterior", "mudaram", "comparativo", "comparação"]):
            m_curr = re.search(r"Total de Despesas no Período:\s*R\$\s*([\d\.,]+)", system_prompt)
            m_prev = re.search(r"Despesas Mês Anterior:\s*R\$\s*([\d\.,]+)", system_prompt)
            if m_curr and m_prev:
                c_val = m_curr.group(1)
                p_val = m_prev.group(1)
                return (
                    f"Comparando os períodos: no mês anterior suas despesas somaram R$ {p_val}, "
                    f"enquanto no período atual somam R$ {c_val}. "
                    "Essa comparação considera todas as despesas consolidadas de cada mês.",
                    provider_name
                )
            return ("Não há dados históricos do mês anterior suficientes para realizar o comparativo.", provider_name)

        # 4. Compromissos futuros / vencem em breve
        if any(w in p for w in ["compromisso", "vencem", "vencimento", "próximos", "a pagar"]):
            comp_match = re.search(r"Próximos Compromissos:\n(.*?)(?=\n\n|\Z)", system_prompt, re.DOTALL)
            if comp_match and comp_match.group(1).strip():
                return (
                    f"Aqui estão os compromissos mais próximos identificados:\n\n{comp_match.group(1).strip()}\n\n"
                    "Lembre-se de reservar o saldo correspondente para quitá-los na data correta.",
                    provider_name
                )
            return ("Você não possui compromissos pendentes com vencimento próximo no momento.", provider_name)

        # 5. Parcelas previstas / compras parceladas
        if any(w in p for w in ["parcela", "parcelas", "parcelamento", "cartão", "fatura"]):
            parc_match = re.search(r"Compras Parceladas Ativas:\n(.*?)(?=\n\n|\Z)", system_prompt, re.DOTALL)
            if parc_match and parc_match.group(1).strip():
                return (
                    f"Suas compras parceladas e previsões futuras no cartão incluem:\n\n{parc_match.group(1).strip()}\n\n"
                    "As parcelas futuras impactam o limite do cartão e o saldo projetado dos próximos meses.",
                    provider_name
                )
            return ("Não foram localizadas compras parceladas ativas para os próximos meses.", provider_name)

        # 6. Saldo atual vs saldo projetado
        if any(w in p for w in ["saldo", "saldo atual", "projetado", "diferença"]):
            m_atual = re.search(r"Saldo Atual \(Real\):\s*R\$\s*([\d\.,]+)", system_prompt)
            m_proj = re.search(r"Saldo Projetado(?: ao Final do Período)?:\s*R\$\s*([\d\.,]+)", system_prompt)
            if m_atual and m_proj:
                atual = m_atual.group(1)
                proj = m_proj.group(1)
                return (
                    f"Seu Saldo Atual (Real) é de R$ {atual}. Ele considera o saldo inicial somado às receitas recebidas "
                    f"e subtraído das despesas já pagas até hoje.\n\n"
                    f"Já o seu Saldo Projetado ao final do período é de R$ {proj}. Ele calcula quanto você terá em conta "
                    f"após o recebimento de receitas pendentes e o pagamento de todas as obrigações e parcelas previstas no período.",
                    provider_name
                )
            return ("Não foi possível obter o cálculo dos saldos para o período selecionado.", provider_name)

        # 7. Resposta padrão contextual
        return (
            "Com base nas suas informações no Finnk, posso detalhar seus gastos por categoria, "
            "comparar seu desempenho com o mês anterior, listar compromissos e parcelas a vencer, "
            "ou explicar seu saldo atual e projetado. Como prefere começar?",
            provider_name
        )
