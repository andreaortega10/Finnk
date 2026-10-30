import datetime
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from ...models import User, Transaction, InstallmentPurchase, CreditCard, Category
from ..financial_engine import get_dashboard_analytics, is_tx_overdue, is_tx_pending, MONTH_NAMES_PT

def format_currency_br(val: float) -> str:
    """Formata valor em Real brasileiro determinístico (ex: R$ 1.250,00)."""
    val = round(val or 0.0, 2)
    formatted = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"

def build_financial_context(
    db: Session,
    user: User,
    month: int = None,
    year: int = None
) -> Tuple[str, str]:
    """
    Constrói o contexto financeiro mínimo, agregado e anonimizado do usuário,
    utilizando estritamente a fonte de verdade determinística do Finnk.
    Retorna: (system_prompt, period_label)
    """
    today = datetime.date.today()
    sel_month = month or today.month
    sel_year = year or today.year

    # 1. Indicadores do período selecionado
    analytics = get_dashboard_analytics(db, user, sel_month, sel_year)
    period_label = analytics.get("selected_period", f"{MONTH_NAMES_PT.get(sel_month, '')}/{sel_year}")

    # 2. Indicadores do mês anterior para comparativos
    prev_m = 12 if sel_month == 1 else sel_month - 1
    prev_y = sel_year - 1 if sel_month == 1 else sel_year
    prev_analytics = get_dashboard_analytics(db, user, prev_m, prev_y)
    prev_period_label = prev_analytics.get("selected_period", f"{MONTH_NAMES_PT.get(prev_m, '')}/{prev_y}")

    # Cálculos determinísticos de variação
    curr_exp = analytics.get("period_expense_total", 0.0)
    prev_exp = prev_analytics.get("period_expense_total", 0.0)
    exp_diff = round(curr_exp - prev_exp, 2)
    exp_pct = round(((curr_exp - prev_exp) / prev_exp) * 100, 1) if prev_exp > 0 else 0.0
    var_sign = "+" if exp_diff >= 0 else "-"

    # 3. Categorias de gastos do período
    cat_dist = analytics.get("category_distribution", [])
    cats_lines = []
    for c in cat_dist[:6]:  # Top 6 categorias para economizar tokens
        cats_lines.append(f"- {c.get('name')}: {format_currency_br(c.get('amount'))} ({c.get('percentage')}%)")
    cats_text = "\n".join(cats_lines) if cats_lines else "- Nenhuma despesa categorizada neste período."

    # 4. Próximos compromissos futuros do usuário (mínimo, sem dados pessoais)
    upcoming = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        Transaction.status.in_(["PENDENTE", "ATRASADA"]),
        or_(
            and_(Transaction.due_date.isnot(None), Transaction.due_date >= today),
            and_(Transaction.due_date.is_(None), Transaction.date >= today)
        )
    ).order_by(
        func.coalesce(Transaction.due_date, Transaction.date).asc()
    ).limit(5).all()

    upcoming_lines = []
    for t in upcoming:
        ref_d = t.due_date or t.date
        date_str = ref_d.strftime("%d/%m/%Y")
        upcoming_lines.append(f"- {t.title}: {format_currency_br(t.amount)} (vencimento: {date_str})")
    upcoming_text = "\n".join(upcoming_lines) if upcoming_lines else "- Nenhum compromisso pendente próximo identificado."

    # 5. Compras parceladas ativas
    installments = db.query(InstallmentPurchase).filter(
        InstallmentPurchase.user_id == user.id
    ).order_by(InstallmentPurchase.created_at.desc()).limit(4).all()

    inst_lines = []
    for inst in installments:
        paid_c = db.query(Transaction).filter(
            Transaction.installment_id == inst.id,
            Transaction.status.in_(["PAGA", "RECEBIDA"])
        ).count()
        inst_lines.append(
            f"- {inst.title}: total {format_currency_br(inst.total_amount)} em {inst.total_installments}x "
            f"({paid_c}/{inst.total_installments} parcelas pagas)"
        )
    inst_text = "\n".join(inst_lines) if inst_lines else "- Nenhuma compra parcelada ativa cadastrada."

    # 6. Montagem do prompt do sistema com diretrizes estritas
    system_prompt = f"""Você é o Assistente Virtual do Finnk, o aplicativo de organização financeira pessoal.
Sua missão é responder de forma cordial, clara, prática e transparente em Português do Brasil.

DIRETRIZES FUNDAMENTAIS:
1. Utilize ESTRITAMENTE os valores do contexto financeiro oficial abaixo. NUNCA invente movimentações, valores, categorias, tendências ou parcelas.
2. Não realize cálculos próprios ou adivinhações: todos os totais, saldos e variações oficiais já foram calculados pelo sistema do Finnk.
3. Diferencie sempre valores já REALIZADOS (pagos/recebidos) de valores PREVISTOS (pendentes/futuros) e do Saldo Projetado.
4. Explique que o Saldo Real considera o dinheiro disponível em conta hoje, enquanto o Saldo Projetado projeta o saldo ao final do mês após receitas e despesas previstas.
5. Se não houver dados suficientes no contexto para responder com precisão, informe isso explicitamente e com educação.
6. A assistência é estritamente de consulta (leitura) e orientação prática; você não pode e não deve cadastrar, alterar ou excluir dados financeiros.
7. Não dê conselhos de investimento de risco nem faça promessas financeiras; ofereça sugestões responsáveis de organização e planejamento.
8. FORMATAÇÃO LIMPA: NUNCA utilize asteriscos no texto. Não use asteriscos duplos (**) para negrito e não use asterisco (*) para tópicos. Escreva em texto limpo e direto, com quebras de linha normais entre os parágrafos e marcadores de traço simples (-) ou números (1., 2.) quando listar itens.

--- CONTEXTO FINANCEIRO OFICIAL DETERMINÍSTICO (FINNK) ---
Período Analisado: {period_label}
Saldo Atual (Real): {format_currency_br(analytics.get('current_balance'))}
Saldo Projetado ao Final do Período: {format_currency_br(analytics.get('projected_balance'))}
Total de Receitas no Período: {format_currency_br(analytics.get('period_income_total'))} (Recebidas: {format_currency_br(analytics.get('total_income_received') if analytics.get('total_income_received') is not None else analytics.get('income_received'))} | Previstas: {format_currency_br(analytics.get('total_income_expected') if analytics.get('total_income_expected') is not None else analytics.get('income_expected'))})
Total de Despesas no Período: {format_currency_br(analytics.get('period_expense_total'))} (Pagas: {format_currency_br(analytics.get('total_expense_paid') if analytics.get('total_expense_paid') is not None else analytics.get('expense_paid'))} | Pendentes: {format_currency_br(analytics.get('total_expense_pending') if analytics.get('total_expense_pending') is not None else analytics.get('expense_pending'))} | Atrasadas: {format_currency_br(analytics.get('total_overdue') if analytics.get('total_overdue') is not None else analytics.get('overdue_amount'))})

Comparativo com Período Anterior ({prev_period_label}):
- Despesas no Período Anterior: {format_currency_br(prev_exp)}
- Despesas no Período Atual: {format_currency_br(curr_exp)}
- Variação Nominal: {var_sign} {format_currency_br(abs(exp_diff))} ({exp_pct}%)

Gastos por Categoria ({period_label}):
{cats_text}

Próximos Compromissos a Vencer:
{upcoming_text}

Compras Parceladas Ativas:
{inst_text}
---------------------------------------------------------
"""
    return system_prompt.strip(), period_label
