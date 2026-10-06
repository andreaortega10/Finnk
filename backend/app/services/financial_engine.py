import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from ..models import Account, CreditCard, Transaction, Category, Budget, Alert, User
from .recurring_engine import sync_all_active_recurring_rules
from .alerts_engine import generate_financial_alerts

MONTH_NAMES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def calculate_account_balances(db: Session, account: Account) -> tuple[float, float]:
    """
    RN04:
    Saldo atual = saldo inicial + receitas pagas - despesas pagas
    Saldo projetado = saldo atual + receitas futuras pendentes - despesas futuras pendentes
    """
    today = datetime.date.today()

    # Receitas pagas
    paid_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account.id,
        Transaction.type == "RECEITA",
        Transaction.status.in_(["PAGA", "RECEBIDA"])
    ).scalar() or 0.0

    # Despesas pagas
    paid_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account.id,
        Transaction.type == "DESPESA",
        Transaction.status == "PAGA"
    ).scalar() or 0.0

    current_balance = round(account.initial_balance + paid_income - paid_expense, 2)

    # Receitas futuras pendentes (data >= hoje)
    future_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account.id,
        Transaction.type == "RECEITA",
        Transaction.status == "PENDENTE",
        Transaction.date >= today
    ).scalar() or 0.0

    # Despesas futuras pendentes (data >= hoje)
    future_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account.id,
        Transaction.type == "DESPESA",
        Transaction.status.in_(["PENDENTE", "ATRASADA"]),
        Transaction.date >= today
    ).scalar() or 0.0

    projected_balance = round(current_balance + future_income - future_expense, 2)

    return current_balance, projected_balance


def calculate_card_metrics(db: Session, card: CreditCard, month: int = None, year: int = None) -> tuple[float, float]:
    """Calcula limite disponível e valor da fatura atual do cartão."""
    today = datetime.date.today()
    target_month = month or today.month
    target_year = year or today.year

    # Fatura do período: despesas lançadas no cartão com vencimento no mês/ano
    invoice_amount = db.query(func.sum(Transaction.amount)).filter(
        Transaction.credit_card_id == card.id,
        Transaction.type == "DESPESA",
        extract('month', Transaction.date) == target_month,
        extract('year', Transaction.date) == target_year
    ).scalar() or 0.0

    # Todas as parcelas/despesas não pagas no cartão reduzem o limite total
    unpaid_on_card = db.query(func.sum(Transaction.amount)).filter(
        Transaction.credit_card_id == card.id,
        Transaction.type == "DESPESA",
        Transaction.status.in_(["PENDENTE", "ATRASADA"])
    ).scalar() or 0.0

    available_limit = max(0.0, round(card.limit_total - unpaid_on_card, 2))

    return available_limit, round(invoice_amount, 2)


def get_home_summary(db: Session, user: User, month: int = None, year: int = None) -> dict:
    """
    Retorna os dados consolidados exatamente no formato esperado pela tela Início
    conforme o protótipo de alta fidelidade `Painel financeiro em tons pastel.png`.
    """
    today = datetime.date.today()
    sel_month = month or today.month
    sel_year = year or today.year

    # Sincroniza lançamentos de recorrências e alertas antes de calcular
    sync_all_active_recurring_rules(db, user.id)
    generate_financial_alerts(db, user.id)

    # 1. Transações do mês selecionado
    tx_query = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        extract('month', Transaction.date) == sel_month,
        extract('year', Transaction.date) == sel_year
    )
    month_txs = tx_query.all()

    # Total de compromissos (despesas do mês)
    month_expenses = [t for t in month_txs if t.type == "DESPESA"]
    total_commitments_amount = sum(t.amount for t in month_expenses)
    total_commitments_count = len(month_expenses)

    # Pagos
    paid_items = [t for t in month_expenses if t.status == "PAGA"]
    paid_amount = sum(t.amount for t in paid_items)
    paid_count = len(paid_items)

    # Pendentes (somente as não atrasadas)
    pending_items = [t for t in month_expenses if t.status == "PENDENTE" and t.date >= today]
    pending_amount = sum(t.amount for t in pending_items)
    pending_count = len(pending_items)

    # Atrasados (despesas do mês com status ATRASADA ou pendentes com data < hoje)
    overdue_items = [t for t in month_expenses if t.status == "ATRASADA" or (t.status == "PENDENTE" and t.date < today)]
    overdue_amount = sum(t.amount for t in overdue_items)
    overdue_count = len(overdue_items)

    # Próximo vencimento (o item pendente mais próximo a partir de hoje)
    next_due_tx = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        Transaction.status == "PENDENTE",
        Transaction.date >= today
    ).order_by(Transaction.date.asc()).first()

    next_due_dict = None
    if next_due_tx:
        next_due_dict = {
            "date_formatted": next_due_tx.date.strftime("%d/%m"),
            "full_date": next_due_tx.date.strftime("%d/%m/%Y"),
            "title": next_due_tx.title,
            "amount": next_due_tx.amount
        }

    # Despesas por categoria
    category_expenses = []
    cat_totals = {}
    for t in month_expenses:
        cat_id = t.category_id
        cat_totals[cat_id] = cat_totals.get(cat_id, 0.0) + t.amount

    total_expense_val = sum(cat_totals.values()) or 1.0  # evitar divisão por zero
    for cat_id, amt in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
        cat = db.query(Category).filter(Category.id == cat_id).first()
        if cat:
            pct = round((amt / total_expense_val) * 100)
            category_expenses.append({
                "category_id": cat.id,
                "name": cat.name,
                "color": cat.color or "#D83A6F",
                "icon": cat.icon or "Tag",
                "amount": round(amt, 2),
                "percentage": pct
            })

    # Resumo dos cartões
    cards = db.query(CreditCard).filter(CreditCard.user_id == user.id).all()
    cards_summary = []
    for c in cards:
        avail, inv = calculate_card_metrics(db, c, sel_month, sel_year)
        cards_summary.append({
            "id": c.id,
            "name": c.name,
            "brand": c.brand,
            "color": c.color,
            "last_four_digits": c.last_four_digits,
            "limit_total": c.limit_total,
            "available_limit": avail,
            "current_invoice": inv
        })

    # Próximos vencimentos (lista de até 4 itens)
    upcoming_list = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        Transaction.date >= today
    ).order_by(Transaction.date.asc()).limit(4).all()

    # Formata lista de transações
    def format_tx(t: Transaction):
        cat = db.query(Category).filter(Category.id == t.category_id).first()
        acc = db.query(Account).filter(Account.id == t.account_id).first() if t.account_id else None
        crd = db.query(CreditCard).filter(CreditCard.id == t.credit_card_id).first() if t.credit_card_id else None
        return {
            "id": t.id,
            "user_id": t.user_id,
            "account_id": t.account_id,
            "credit_card_id": t.credit_card_id,
            "category_id": t.category_id,
            "category_name": cat.name if cat else "Geral",
            "category_color": cat.color if cat else "#D83A6F",
            "category_icon": cat.icon if cat else "Tag",
            "account_name": acc.name if acc else None,
            "credit_card_name": crd.name if crd else None,
            "title": t.title,
            "description": t.description,
            "amount": t.amount,
            "date": t.date,
            "type": t.type,
            "status": t.status,
            "payment_method": t.payment_method,
            "is_installment": t.is_installment,
            "installment_id": t.installment_id,
            "installment_number": t.installment_number,
            "total_installments": t.total_installments,
            "is_recurring": t.is_recurring,
            "recurring_id": t.recurring_id,
            "is_adjustment": t.is_adjustment,
            "created_at": t.created_at,
            "updated_at": t.updated_at
        }

    # Últimas transações cadastradas/realizadas (até 5 itens)
    recent_txs = db.query(Transaction).filter(
        Transaction.user_id == user.id
    ).order_by(Transaction.date.desc(), Transaction.id.desc()).limit(5).all()

    unread_alerts = db.query(Alert).filter(Alert.user_id == user.id, Alert.is_read == False).count()

    return {
        "user_name": user.name.split()[0],
        "selected_month": sel_month,
        "selected_year": sel_year,
        "month_name": f"{MONTH_NAMES_PT.get(sel_month, '')}/{sel_year}",
        "total_commitments_amount": round(total_commitments_amount, 2),
        "total_commitments_count": total_commitments_count,
        "paid_amount": round(paid_amount, 2),
        "paid_count": paid_count,
        "pending_amount": round(pending_amount, 2),
        "pending_count": pending_count,
        "overdue_amount": round(overdue_amount, 2),
        "overdue_count": overdue_count,
        "next_due_item": next_due_dict,
        "category_expenses": category_expenses,
        "total_expenses_period": round(sum(t.amount for t in month_expenses), 2),
        "cards_summary": cards_summary,
        "upcoming_commitments": [format_tx(t) for t in upcoming_list],
        "recent_transactions": [format_tx(t) for t in recent_txs],
        "unread_alerts_count": unread_alerts
    }


def get_dashboard_analytics(db: Session, user: User, month: int = None, year: int = None) -> dict:
    """Visão analítica consolidada do Dashboard."""
    today = datetime.date.today()
    sel_month = month or today.month
    sel_year = year or today.year

    sync_all_active_recurring_rules(db, user.id)

    # 1. Saldos consolidados de todas as contas
    accounts = db.query(Account).filter(Account.user_id == user.id, Account.is_active == True).all()
    total_current_balance = 0.0
    total_projected_balance = 0.0
    accounts_balance = []

    for acc in accounts:
        curr, proj = calculate_account_balances(db, acc)
        total_current_balance += curr
        total_projected_balance += proj
        accounts_balance.append({
            "id": acc.id,
            "name": acc.name,
            "type": acc.type,
            "color": acc.color,
            "current_balance": curr,
            "projected_balance": proj
        })

    # 2. Receitas e Despesas do mês
    month_txs = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        extract('month', Transaction.date) == sel_month,
        extract('year', Transaction.date) == sel_year
    ).all()

    income_received = sum(t.amount for t in month_txs if t.type == "RECEITA" and t.status in ["PAGA", "RECEBIDA"])
    income_expected = sum(t.amount for t in month_txs if t.type == "RECEITA" and t.status == "PENDENTE")
    expense_paid = sum(t.amount for t in month_txs if t.type == "DESPESA" and t.status == "PAGA")
    expense_pending = sum(t.amount for t in month_txs if t.type == "DESPESA" and t.status == "PENDENTE" and t.date >= today)
    overdue_val = sum(t.amount for t in month_txs if t.type == "DESPESA" and (t.status == "ATRASADA" or (t.status == "PENDENTE" and t.date < today)))

    # 3. Compromissos futuros (a partir do mês seguinte até o fim do ano ou 6 meses)
    future_commitments = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        Transaction.date > today,
        Transaction.status == "PENDENTE"
    ).scalar() or 0.0

    # 4. Evolução mensal (últimos 6 meses até o mês selecionado)
    evolution_data = []
    start_date = today.replace(day=1) - datetime.timedelta(days=150)
    for i in range(6):
        m_date = today.replace(day=1) - datetime.timedelta(days=(5 - i) * 30)
        m_num = m_date.month
        y_num = m_date.year

        m_inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == "RECEITA",
            Transaction.status.in_(["PAGA", "RECEBIDA"]),
            extract('month', Transaction.date) == m_num,
            extract('year', Transaction.date) == y_num
        ).scalar() or 0.0

        m_exp = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == "DESPESA",
            Transaction.status == "PAGA",
            extract('month', Transaction.date) == m_num,
            extract('year', Transaction.date) == y_num
        ).scalar() or 0.0

        evolution_data.append({
            "month_num": m_num,
            "year": y_num,
            "label": f"{MONTH_NAMES_PT.get(m_num, '')[:3]}/{str(y_num)[2:]}",
            "receitas": round(m_inc, 2),
            "despesas": round(m_exp, 2),
            "saldo": round(m_inc - m_exp, 2)
        })

    # 5. Distribuição de gastos por categoria
    category_distribution = []
    cat_query = db.query(
        Transaction.category_id,
        func.sum(Transaction.amount).label("total")
    ).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        extract('month', Transaction.date) == sel_month,
        extract('year', Transaction.date) == sel_year
    ).group_by(Transaction.category_id).all()

    total_exp_all = sum(item.total for item in cat_query) or 1.0
    for item in cat_query:
        cat = db.query(Category).filter(Category.id == item.category_id).first()
        if cat:
            category_distribution.append({
                "category_id": cat.id,
                "name": cat.name,
                "color": cat.color or "#D83A6F",
                "icon": cat.icon or "Tag",
                "amount": round(item.total, 2),
                "percentage": round((item.total / total_exp_all) * 100, 1)
            })

    # 6. Distribuição de status dos compromissos
    status_distribution = [
        {"name": "Pagos", "count": len([t for t in month_txs if t.status == "PAGA"]), "amount": round(expense_paid, 2), "color": "#10B981"},
        {"name": "Pendentes", "count": len([t for t in month_txs if t.status == "PENDENTE"]), "amount": round(expense_pending, 2), "color": "#F59E0B"},
        {"name": "Atrasados", "count": len([t for t in month_txs if t.status == "ATRASADA" or (t.status == "PENDENTE" and t.date < today)]), "amount": round(overdue_val, 2), "color": "#EF4444"},
    ]

    # 7. Cartões de crédito e uso
    cards = db.query(CreditCard).filter(CreditCard.user_id == user.id).all()
    cards_usage = []
    for c in cards:
        avail, inv = calculate_card_metrics(db, c, sel_month, sel_year)
        cards_usage.append({
            "id": c.id,
            "name": c.name,
            "brand": c.brand,
            "color": c.color,
            "limit_total": c.limit_total,
            "available_limit": avail,
            "invoice_amount": inv,
            "used_percentage": round(((c.limit_total - avail) / c.limit_total) * 100, 1) if c.limit_total > 0 else 0
        })

    return {
        "selected_period": f"{MONTH_NAMES_PT.get(sel_month, '')}/{sel_year}",
        "current_balance": round(total_current_balance, 2),
        "projected_balance": round(total_projected_balance, 2),
        "total_income_received": round(income_received, 2),
        "total_income_expected": round(income_expected, 2),
        "total_expense_paid": round(expense_paid, 2),
        "total_expense_pending": round(expense_pending, 2),
        "total_overdue": round(overdue_val, 2),
        "future_commitments_total": round(future_commitments, 2),
        "category_distribution": category_distribution,
        "monthly_evolution": evolution_data,
        "status_distribution": status_distribution,
        "accounts_balance": accounts_balance,
        "cards_usage": cards_usage
    }
