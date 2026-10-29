import datetime
import calendar
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, or_, and_
from ..models import Account, CreditCard, Transaction, Category, Budget, Alert, User
from .recurring_engine import sync_all_active_recurring_rules
from .alerts_engine import generate_financial_alerts

MONTH_NAMES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def calculate_account_balances(
    db: Session,
    account: Account,
    target_month: int = None,
    target_year: int = None
) -> tuple[float, float]:
    """
    Calcula com rigor contábil:
    1. Saldo Atual (Real no dia de hoje):
       Saldo inicial da conta + receitas realizadas até hoje - despesas pagas até hoje.
    2. Saldo Projetado ao final do período (RN 4.1):
       Saldo de abertura do período + receitas previstas para o período - despesas previstas para o período.
    """
    today = datetime.date.today()
    sel_month = target_month or today.month
    sel_year = target_year or today.year

    last_day = calendar.monthrange(sel_year, sel_month)[1]
    period_start = datetime.date(sel_year, sel_month, 1)
    period_end = datetime.date(sel_year, sel_month, last_day)

    # 1. Saldo Atual Real (no dia de hoje)
    paid_income_today = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account.id,
        Transaction.type == "RECEITA",
        Transaction.status.in_(["PAGA", "RECEBIDA"]),
        Transaction.date <= today
    ).scalar() or 0.0

    paid_expense_today = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account.id,
        Transaction.type == "DESPESA",
        Transaction.status.in_(["PAGA", "RECEBIDA"]),
        Transaction.date <= today
    ).scalar() or 0.0

    current_balance = round(account.initial_balance + paid_income_today - paid_expense_today, 2)

    # 2. Saldo Projetado
    if target_month is None:
        # Sem período específico: horizonte de todas as pendências futuras
        future_inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "RECEITA",
            Transaction.status == "PENDENTE",
            Transaction.date >= today
        ).scalar() or 0.0

        future_exp = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "DESPESA",
            Transaction.status.in_(["PENDENTE", "ATRASADA"]),
            or_(
                Transaction.due_date >= today,
                and_(Transaction.due_date.is_(None), Transaction.date >= today)
            )
        ).scalar() or 0.0

        projected_balance = round(current_balance + future_inc - future_exp, 2)
    elif period_end < today:
        # Período já encerrado no passado: saldo consolidado até o último dia daquele mês
        past_inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "RECEITA",
            Transaction.status.in_(["PAGA", "RECEBIDA"]),
            Transaction.date <= period_end
        ).scalar() or 0.0

        past_exp = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "DESPESA",
            Transaction.status == "PAGA",
            Transaction.date <= period_end
        ).scalar() or 0.0

        projected_balance = round(account.initial_balance + past_inc - past_exp, 2)
    elif period_start <= today <= period_end:
        # Mês atual: Saldo atual + pendências restantes dentro do mês
        rem_inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "RECEITA",
            Transaction.status == "PENDENTE",
            Transaction.date >= today,
            Transaction.date <= period_end
        ).scalar() or 0.0

        rem_exp = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "DESPESA",
            Transaction.status.in_(["PENDENTE", "ATRASADA"]),
            or_(
                and_(Transaction.due_date.isnot(None), Transaction.due_date >= today, Transaction.due_date <= period_end),
                and_(Transaction.due_date.is_(None), Transaction.date >= today, Transaction.date <= period_end)
            )
        ).scalar() or 0.0

        projected_balance = round(current_balance + rem_inc - rem_exp, 2)
    else:
        # Mês futuro (period_start > today):
        # Saldo de abertura = Saldo atual hoje + net pendente intermediário até period_start
        inter_inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "RECEITA",
            Transaction.status == "PENDENTE",
            Transaction.date >= today,
            Transaction.date < period_start
        ).scalar() or 0.0

        inter_exp = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "DESPESA",
            Transaction.status.in_(["PENDENTE", "ATRASADA"]),
            or_(
                and_(Transaction.due_date.isnot(None), Transaction.due_date >= today, Transaction.due_date < period_start),
                and_(Transaction.due_date.is_(None), Transaction.date >= today, Transaction.date < period_start)
            )
        ).scalar() or 0.0

        opening_balance = current_balance + inter_inc - inter_exp

        # Movimentações previstas para o mês selecionado
        month_inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "RECEITA",
            Transaction.status == "PENDENTE",
            Transaction.date >= period_start,
            Transaction.date <= period_end
        ).scalar() or 0.0

        month_exp = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "DESPESA",
            Transaction.status.in_(["PENDENTE", "ATRASADA"]),
            or_(
                and_(Transaction.due_date.isnot(None), Transaction.due_date >= period_start, Transaction.due_date <= period_end),
                and_(Transaction.due_date.is_(None), Transaction.date >= period_start, Transaction.date <= period_end)
            )
        ).scalar() or 0.0

        projected_balance = round(opening_balance + month_inc - month_exp, 2)

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


def is_tx_overdue(t: Transaction, today: datetime.date) -> bool:
    """Classifica se uma despesa está vencida/atrasada."""
    if t.type != "DESPESA":
        return False
    if t.status == "ATRASADA":
        return True
    if t.status == "PENDENTE" and t.due_date is not None and t.due_date < today:
        return True
    return False

def is_tx_pending(t: Transaction, today: datetime.date) -> bool:
    """Classifica se uma transação está pendente (e não atrasada)."""
    if t.status != "PENDENTE":
        return False
    return not is_tx_overdue(t, today)

def is_tx_paid(t: Transaction) -> bool:
    """Classifica se uma transação foi paga ou recebida."""
    return t.status in ["PAGA", "RECEBIDA"]

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
    paid_items = [t for t in month_expenses if is_tx_paid(t)]
    paid_amount = sum(t.amount for t in paid_items)
    paid_count = len(paid_items)

    # Atrasados (somente despesas com vencimento informado e vencimento < hoje, ou status ATRASADA)
    overdue_items = [t for t in month_expenses if is_tx_overdue(t, today)]
    overdue_amount = sum(t.amount for t in overdue_items)
    overdue_count = len(overdue_items)

    # Pendentes (somente as pendentes que NÃO estão atrasadas)
    pending_items = [t for t in month_expenses if is_tx_pending(t, today)]
    pending_amount = sum(t.amount for t in pending_items)
    pending_count = len(pending_items)

    # Próximo vencimento (o item pendente mais próximo a partir de hoje)
    next_due_tx = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        Transaction.status == "PENDENTE",
        or_(
            Transaction.due_date >= today,
            and_(Transaction.due_date.is_(None), Transaction.date >= today)
        )
    ).order_by(
        func.coalesce(Transaction.due_date, Transaction.date).asc()
    ).first()

    next_due_dict = None
    if next_due_tx:
        ref_date = next_due_tx.due_date or next_due_tx.date
        next_due_dict = {
            "date_formatted": ref_date.strftime("%d/%m"),
            "full_date": ref_date.strftime("%d/%m/%Y"),
            "title": next_due_tx.title,
            "amount": next_due_tx.amount
        }

    # Pre-fetch para eliminar consultas N+1 ao banco
    user_cats = {c.id: c for c in db.query(Category).filter(Category.user_id == user.id).all()}
    user_accs = {a.id: a for a in db.query(Account).filter(Account.user_id == user.id).all()}
    user_cards = {c.id: c for c in db.query(CreditCard).filter(CreditCard.user_id == user.id).all()}

    # Despesas por categoria
    category_expenses = []
    cat_totals = {}
    for t in month_expenses:
        cat_id = t.category_id
        cat_totals[cat_id] = cat_totals.get(cat_id, 0.0) + t.amount

    total_expense_val = sum(cat_totals.values()) or 1.0  # evitar divisão por zero
    for cat_id, amt in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
        cat = user_cats.get(cat_id)
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
    cards = list(user_cards.values())
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

    # Formata lista de transações com lookups em memória
    def format_tx(t: Transaction):
        cat = user_cats.get(t.category_id)
        acc = user_accs.get(t.account_id)
        crd = user_cards.get(t.credit_card_id)
        eff_status = t.status
        if is_tx_overdue(t, today):
            eff_status = "ATRASADA"
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
            "due_date": t.due_date,
            "type": t.type,
            "status": eff_status,
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

    last_day = calendar.monthrange(sel_year, sel_month)[1]
    horizon_date_obj = datetime.date(sel_year, sel_month, last_day)
    horizon_formatted = f"{last_day:02d}/{sel_month:02d}/{sel_year}"
    month_name_pt = MONTH_NAMES_PT.get(sel_month, '')
    if horizon_date_obj < today:
        horizon_label_global = f"Saldo realizado em {month_name_pt} de {sel_year}"
    else:
        horizon_label_global = f"Saldo projetado ao final de {month_name_pt} de {sel_year}"

    for acc in accounts:
        curr, proj = calculate_account_balances(db, acc, sel_month, sel_year)
        total_current_balance += curr
        total_projected_balance += proj
        accounts_balance.append({
            "id": acc.id,
            "name": acc.name,
            "type": acc.type,
            "color": acc.color,
            "current_balance": curr,
            "projected_balance": proj,
            "horizon_label": horizon_label_global
        })

    # 2. Receitas e Despesas do mês
    month_txs = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        extract('month', Transaction.date) == sel_month,
        extract('year', Transaction.date) == sel_year
    ).all()

    income_received = sum(t.amount for t in month_txs if t.type == "RECEITA" and is_tx_paid(t))
    income_expected = sum(t.amount for t in month_txs if t.type == "RECEITA" and is_tx_pending(t, today))
    expense_paid = sum(t.amount for t in month_txs if t.type == "DESPESA" and is_tx_paid(t))
    expense_pending = sum(t.amount for t in month_txs if t.type == "DESPESA" and is_tx_pending(t, today))
    overdue_val = sum(t.amount for t in month_txs if is_tx_overdue(t, today))

    period_start = datetime.date(sel_year, sel_month, 1)
    period_end = datetime.date(sel_year, sel_month, last_day)
    month_name_pt = MONTH_NAMES_PT.get(sel_month, '')

    total_initial = sum(acc.initial_balance for acc in accounts)
    if period_end < today or (period_start <= today <= period_end):
        past_inc_before = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == "RECEITA",
            Transaction.status.in_(["PAGA", "RECEBIDA"]),
            Transaction.date < period_start
        ).scalar() or 0.0
        past_exp_before = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == "DESPESA",
            Transaction.status == "PAGA",
            Transaction.date < period_start
        ).scalar() or 0.0
        opening_balance = total_initial + past_inc_before - past_exp_before
    else:
        inter_inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == "RECEITA",
            Transaction.status == "PENDENTE",
            Transaction.date >= today,
            Transaction.date < period_start
        ).scalar() or 0.0
        inter_exp = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == "DESPESA",
            Transaction.status.in_(["PENDENTE", "ATRASADA"]),
            or_(
                and_(Transaction.due_date.isnot(None), Transaction.due_date >= today, Transaction.due_date < period_start),
                and_(Transaction.due_date.is_(None), Transaction.date >= today, Transaction.date < period_start)
            )
        ).scalar() or 0.0
        opening_balance = total_current_balance + inter_inc - inter_exp

    opening_balance = round(opening_balance, 2)
    period_income_total = round(income_received + income_expected, 2)
    period_expense_total = round(expense_paid + expense_pending + overdue_val, 2)

    details_fmt = f"Abertura: R$ {opening_balance:,.2f} + Receitas: R$ {period_income_total:,.2f} - Despesas: R$ {period_expense_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # 3. Compromissos futuros (a partir de amanhã)
    future_commitments = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        Transaction.date > today,
        Transaction.status == "PENDENTE"
    ).scalar() or 0.0

    # 4. Evolução mensal (últimos 6 meses até o mês selecionado - Otimizado com consulta agregada única)
    target_months = []
    cy, cm = sel_year, sel_month
    for _ in range(6):
        target_months.append((cy, cm))
        cm -= 1
        if cm < 1:
            cm = 12
            cy -= 1
    target_months.reverse()

    min_y, min_m = target_months[0]
    min_date = datetime.date(min_y, min_m, 1)
    max_y, max_m = target_months[-1]
    _, max_d = calendar.monthrange(max_y, max_m)
    max_date = datetime.date(max_y, max_m, max_d)

    monthly_rows = db.query(
        extract('year', Transaction.date).label('y'),
        extract('month', Transaction.date).label('m'),
        Transaction.type.label('tp'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == user.id,
        Transaction.date >= min_date,
        Transaction.date <= max_date,
        Transaction.status.in_(["PAGA", "RECEBIDA"])
    ).group_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date),
        Transaction.type
    ).all()

    month_totals = {(int(r.y), int(r.m), str(r.tp).upper()): float(r.total) for r in monthly_rows}

    evolution_data = []
    for (y_num, m_num) in target_months:
        m_inc = month_totals.get((y_num, m_num, "RECEITA"), 0.0)
        m_exp = month_totals.get((y_num, m_num, "DESPESA"), 0.0)
        evolution_data.append({
            "month_num": m_num,
            "year": y_num,
            "label": f"{MONTH_NAMES_PT.get(m_num, '')[:3]}/{str(y_num)[2:]}",
            "receitas": round(m_inc, 2),
            "despesas": round(m_exp, 2),
            "saldo": round(m_inc - m_exp, 2)
        })

    # 5. Distribuição de gastos por categoria (ordenada descrescentemente)
    cat_query = db.query(
        Transaction.category_id,
        func.sum(Transaction.amount).label("total")
    ).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        extract('month', Transaction.date) == sel_month,
        extract('year', Transaction.date) == sel_year
    ).group_by(Transaction.category_id).all()

    # Ordena categorias do maior gasto para o menor
    sorted_cat_query = sorted(cat_query, key=lambda x: x.total or 0.0, reverse=True)

    user_cats_dash = {c.id: c for c in db.query(Category).filter(Category.user_id == user.id).all()}
    total_exp_all = sum(item.total for item in sorted_cat_query) or 1.0
    category_distribution = []
    for item in sorted_cat_query:
        cat = user_cats_dash.get(item.category_id)
        if cat:
            category_distribution.append({
                "category_id": cat.id,
                "name": cat.name,
                "color": cat.color or "#D83A6F",
                "icon": cat.icon or "Tag",
                "amount": round(item.total, 2),
                "percentage": round((item.total / total_exp_all) * 100, 1)
            })

    # 6. Distribuição de status dos compromissos (disjunta e perfeitamente equilibrada)
    paid_count = len([t for t in month_txs if t.type == "DESPESA" and is_tx_paid(t)])
    pending_count = len([t for t in month_txs if t.type == "DESPESA" and is_tx_pending(t, today)])
    overdue_count = len([t for t in month_txs if is_tx_overdue(t, today)])

    status_distribution = [
        {"name": "Pagos", "count": paid_count, "amount": round(expense_paid, 2), "color": "#10B981"},
        {"name": "Pendentes", "count": pending_count, "amount": round(expense_pending, 2), "color": "#F59E0B"},
        {"name": "Atrasados", "count": overdue_count, "amount": round(overdue_val, 2), "color": "#EF4444"},
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
        "selected_period": f"{month_name_pt}/{sel_year}",
        "current_balance": round(total_current_balance, 2),
        "projected_balance": round(total_projected_balance, 2),
        "projected_balance_date": horizon_formatted,
        "projected_balance_label": horizon_label_global,
        "has_reliable_projection": len(accounts) > 0,
        "opening_balance": opening_balance,
        "period_income_total": period_income_total,
        "period_expense_total": period_expense_total,
        "projection_details": details_fmt,
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
