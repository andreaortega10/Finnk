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


def is_tx_canceled(t: Transaction) -> bool:
    """Verifica se a transação foi cancelada."""
    return t.status == "CANCELADA"


def is_tx_transfer(t: Transaction) -> bool:
    """Verifica se a transação é uma transferência entre contas ou ajuste interno."""
    return bool(t.is_adjustment) or (t.payment_method == "TRANSFERENCIA")


def is_tx_overdue(t: Transaction, today: datetime.date = None) -> bool:
    """Classifica se uma despesa está vencida/atrasada."""
    if today is None:
        today = datetime.date.today()
    if t.type != "DESPESA" or is_tx_canceled(t):
        return False
    if t.status == "ATRASADA":
        return True
    if t.status in ["PENDENTE", "PREVISTA"] and t.due_date is not None and t.due_date < today:
        return True
    return False


def is_tx_pending(t: Transaction, today: datetime.date = None) -> bool:
    """Classifica se uma transação está pendente/prevista (e não atrasada nem cancelada)."""
    if today is None:
        today = datetime.date.today()
    if t.status not in ["PENDENTE", "PREVISTA"]:
        return False
    return not is_tx_overdue(t, today)


def is_tx_paid(t: Transaction, reference_date: datetime.date = None) -> bool:
    """Classifica se uma transação foi efetivada (paga ou recebida)."""
    if t.status not in ["PAGA", "RECEBIDA"]:
        return False
    if reference_date is not None and t.date > reference_date:
        return False
    return True


def calculate_account_balances(
    db: Session,
    account: Account,
    target_month: int = None,
    target_year: int = None,
    target_date: datetime.date = None,
    reference_date: datetime.date = None
) -> tuple[float, float]:
    """
    Fonte Única de Verdade Contábil por Conta Financeira:
    1. Saldo Atual (Real na data de referência `today`):
       Saldo inicial da conta + receitas efetivadas na conta até hoje - despesas efetivadas na conta até hoje.
       NÃO inclui receitas futuras, despesas previstas ou parcelas de cartão não quitadas.
    2. Saldo Projetado em `target_date` ou ao final de `(target_month, target_year)`:
       Parte do Saldo Atual e considera todas as movimentações previstas/pendentes vinculadas a esta conta
       até a data limite da projeção.
    """
    today = reference_date or datetime.date.today()

    # 1. Saldo Atual Real (disponível em conta na data de referência)
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

    # 2. Determinação da data limite (horizon_date) para o Saldo Projetado
    horizon_date = None
    period_start = None
    if target_date is not None:
        horizon_date = target_date
        period_start = datetime.date(today.year, today.month, 1)
    elif target_month is not None:
        sel_year = target_year or today.year
        last_day = calendar.monthrange(sel_year, target_month)[1]
        period_start = datetime.date(sel_year, target_month, 1)
        horizon_date = datetime.date(sel_year, target_month, last_day)

    if horizon_date is None:
        # Horizonte aberto (todas as pendências futuras registradas na conta)
        future_inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "RECEITA",
            or_(
                and_(Transaction.status.in_(["PENDENTE", "PREVISTA"]), Transaction.date >= today),
                and_(Transaction.status.in_(["PAGA", "RECEBIDA"]), Transaction.date > today)
            )
        ).scalar() or 0.0

        future_exp = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "DESPESA",
            or_(
                and_(
                    Transaction.status.in_(["PENDENTE", "PREVISTA", "ATRASADA"]),
                    or_(
                        Transaction.due_date >= today,
                        and_(Transaction.due_date.is_(None), Transaction.date >= today)
                    )
                ),
                and_(Transaction.status.in_(["PAGA", "RECEBIDA"]), Transaction.date > today)
            )
        ).scalar() or 0.0

        projected_balance = round(current_balance + future_inc - future_exp, 2)
    elif horizon_date < today:
        # Período passado encerrado: saldo efetivamente realizado até horizon_date
        past_inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "RECEITA",
            Transaction.status.in_(["PAGA", "RECEBIDA"]),
            Transaction.date <= horizon_date
        ).scalar() or 0.0

        past_exp = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "DESPESA",
            Transaction.status.in_(["PAGA", "RECEBIDA"]),
            Transaction.date <= horizon_date
        ).scalar() or 0.0

        projected_balance = round(account.initial_balance + past_inc - past_exp, 2)
    else:
        # Horizonte presente ou futuro (horizon_date >= today):
        # Considera pendências desde o início do mês atual (ou today) até horizon_date
        min_date = min(today, period_start) if period_start else today

        exp_inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "RECEITA",
            or_(
                and_(
                    Transaction.status.in_(["PENDENTE", "PREVISTA"]),
                    Transaction.date >= min_date,
                    Transaction.date <= horizon_date
                ),
                and_(
                    Transaction.status.in_(["PAGA", "RECEBIDA"]),
                    Transaction.date > today,
                    Transaction.date <= horizon_date
                )
            )
        ).scalar() or 0.0

        exp_out = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "DESPESA",
            or_(
                and_(
                    Transaction.status.in_(["PENDENTE", "PREVISTA", "ATRASADA"]),
                    func.coalesce(Transaction.due_date, Transaction.date) >= min_date,
                    func.coalesce(Transaction.due_date, Transaction.date) <= horizon_date
                ),
                and_(
                    Transaction.status.in_(["PAGA", "RECEBIDA"]),
                    Transaction.date > today,
                    Transaction.date <= horizon_date
                )
            )
        ).scalar() or 0.0

        projected_balance = round(current_balance + exp_inc - exp_out, 2)

    return current_balance, projected_balance


def get_accounts_projections(
    db: Session,
    user: User,
    horizon_days: int = None,
    start_date: datetime.date = None,
    end_date: datetime.date = None,
    target_date: datetime.date = None,
    month: int = None,
    year: int = None,
    reference_date: datetime.date = None
) -> dict:
    """
    Calcula projeções detalhadas por conta e consolidadas para horizontes de:
    - 7, 30, 90 dias (horizon_days)
    - Data específica (target_date)
    - Período personalizado (start_date a end_date)
    - Mês/Ano (month, year)
    Retorna: data de referência, período, saldo atual, entradas previstas, saídas previstas,
    quantidade de compromissos e saldo final projetado por conta e consolidado.
    """
    sync_all_active_recurring_rules(db, user.id)

    today = reference_date or datetime.date.today()
    ref_start = start_date or datetime.date(today.year, today.month, 1)

    if target_date is not None:
        horizon_end = target_date
        period_label = f"Até {horizon_end.strftime('%d/%m/%Y')}"
    elif end_date is not None:
        horizon_end = end_date
        s_lbl = (start_date or today).strftime('%d/%m/%Y')
        e_lbl = horizon_end.strftime('%d/%m/%Y')
        period_label = f"Período personalizado ({s_lbl} a {e_lbl})"
    elif horizon_days is not None:
        ref_start = today
        horizon_end = today + datetime.timedelta(days=int(horizon_days))
        period_label = f"Próximos {int(horizon_days)} dias (até {horizon_end.strftime('%d/%m/%Y')})"
    else:
        sel_m = month or today.month
        sel_y = year or today.year
        last_d = calendar.monthrange(sel_y, sel_m)[1]
        ref_start = datetime.date(sel_y, sel_m, 1)
        horizon_end = datetime.date(sel_y, sel_m, last_d)
        period_label = f"{MONTH_NAMES_PT.get(sel_m, '')}/{sel_y} (até {horizon_end.strftime('%d/%m/%Y')})"

    accounts = db.query(Account).filter(
        Account.user_id == user.id,
        Account.is_active == True
    ).order_by(Account.id.asc()).all()

    min_bound = min(today, ref_start)

    accounts_out = []
    total_curr = 0.0
    total_proj = 0.0
    total_inc_expected = 0.0
    total_exp_expected = 0.0
    total_commitments_count = 0

    for acc in accounts:
        curr, proj = calculate_account_balances(
            db, acc, target_date=horizon_end, reference_date=today
        )

        # Entradas e saídas previstas para compor a explicação transparente da projeção
        if horizon_end >= today:
            inc_expected = db.query(func.sum(Transaction.amount)).filter(
                Transaction.account_id == acc.id,
                Transaction.type == "RECEITA",
                or_(
                    and_(
                        Transaction.status.in_(["PENDENTE", "PREVISTA"]),
                        Transaction.date >= min_bound,
                        Transaction.date <= horizon_end
                    ),
                    and_(
                        Transaction.status.in_(["PAGA", "RECEBIDA"]),
                        Transaction.date > today,
                        Transaction.date <= horizon_end
                    )
                )
            ).scalar() or 0.0

            exp_expected_q = db.query(Transaction).filter(
                Transaction.account_id == acc.id,
                Transaction.type == "DESPESA",
                or_(
                    and_(
                        Transaction.status.in_(["PENDENTE", "PREVISTA", "ATRASADA"]),
                        func.coalesce(Transaction.due_date, Transaction.date) >= min_bound,
                        func.coalesce(Transaction.due_date, Transaction.date) <= horizon_end
                    ),
                    and_(
                        Transaction.status.in_(["PAGA", "RECEBIDA"]),
                        Transaction.date > today,
                        Transaction.date <= horizon_end
                    )
                )
            ).all()
            exp_expected = sum(t.amount for t in exp_expected_q)
            comm_count = len(exp_expected_q)
        else:
            inc_expected = 0.0
            exp_expected = 0.0
            comm_count = 0

        inc_expected = round(inc_expected, 2)
        exp_expected = round(exp_expected, 2)

        total_curr += curr
        total_proj += proj
        total_inc_expected += inc_expected
        total_exp_expected += exp_expected
        total_commitments_count += comm_count

        accounts_out.append({
            "id": acc.id,
            "name": acc.name,
            "type": acc.type,
            "color": acc.color,
            "initial_balance": round(acc.initial_balance, 2),
            "current_balance": curr,
            "projected_incomes": inc_expected,
            "projected_expenses": exp_expected,
            "projected_commitments_count": comm_count,
            "projected_balance": proj,
            "is_active": acc.is_active,
            "created_at": acc.created_at
        })

    return {
        "reference_date": today.isoformat(),
        "start_date": ref_start.isoformat(),
        "end_date": horizon_end.isoformat(),
        "period_label": period_label,
        "current_balance": round(total_curr, 2),
        "projected_incomes": round(total_inc_expected, 2),
        "projected_expenses": round(total_exp_expected, 2),
        "projected_commitments_count": total_commitments_count,
        "projected_balance": round(total_proj, 2),
        "accounts": accounts_out
    }


def calculate_card_metrics(db: Session, card: CreditCard, month: int = None, year: int = None) -> tuple[float, float]:
    """Calcula limite disponível e valor da fatura do mês selecionado do cartão."""
    today = datetime.date.today()
    target_month = month or today.month
    target_year = year or today.year

    # Despesas lançadas neste cartão no mês/ano de referência (exceto canceladas)
    invoice_amount = db.query(func.sum(Transaction.amount)).filter(
        Transaction.credit_card_id == card.id,
        Transaction.type == "DESPESA",
        Transaction.status != "CANCELADA",
        extract('month', Transaction.date) == target_month,
        extract('year', Transaction.date) == target_year
    ).scalar() or 0.0

    # Todas as parcelas/despesas não pagas no cartão reduzem o limite total disponível
    unpaid_on_card = db.query(func.sum(Transaction.amount)).filter(
        Transaction.credit_card_id == card.id,
        Transaction.type == "DESPESA",
        Transaction.status.in_(["PENDENTE", "PREVISTA", "ATRASADA"])
    ).scalar() or 0.0

    available_limit = max(0.0, round(card.limit_total - unpaid_on_card, 2))
    return available_limit, round(invoice_amount, 2)


def calculate_budgets_metrics(db: Session, user_id: int, month: int = None, year: int = None) -> list[dict]:
    """
    Calcula todos os orçamentos do usuário para o mês/ano em lote (zero N+1 queries),
    considerando apenas despesas elegíveis (não canceladas e não transferências/ajustes).
    """
    today = datetime.date.today()
    sel_month = month or today.month
    sel_year = year or today.year

    budgets = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.month == sel_month,
        Budget.year == sel_year
    ).order_by(Budget.id.asc()).all()

    if not budgets:
        return []

    cat_ids = list({b.category_id for b in budgets})
    cats_map = {
        c.id: c
        for c in db.query(Category).filter(Category.id.in_(cat_ids)).all()
    }

    spent_rows = db.query(
        Transaction.category_id,
        func.sum(Transaction.amount).label("total")
    ).filter(
        Transaction.user_id == user_id,
        Transaction.category_id.in_(cat_ids),
        Transaction.type == "DESPESA",
        Transaction.status != "CANCELADA",
        Transaction.is_adjustment == False,
        Transaction.payment_method != "TRANSFERENCIA",
        extract('month', Transaction.date) == sel_month,
        extract('year', Transaction.date) == sel_year
    ).group_by(Transaction.category_id).all()

    spent_map = {r.category_id: round(float(r.total or 0.0), 2) for r in spent_rows}

    result = []
    for b in budgets:
        cat = cats_map.get(b.category_id)
        spent = spent_map.get(b.category_id, 0.0)
        remaining = max(0.0, round(b.monthly_limit - spent, 2))
        pct = round((spent / b.monthly_limit) * 100, 1) if b.monthly_limit > 0 else 0.0

        result.append({
            "id": b.id,
            "category_id": b.category_id,
            "category_name": cat.name if cat else "Categoria",
            "category_color": (cat.color if cat and cat.color else "#D83A6F"),
            "category_icon": (cat.icon if cat and cat.icon else "Tag"),
            "month": b.month,
            "year": b.year,
            "monthly_limit": round(b.monthly_limit, 2),
            "spent_amount": spent,
            "remaining_amount": remaining,
            "percentage_used": pct,
            "is_warning": (pct >= 80.0 and pct < 100.0),
            "is_exceeded": (pct >= 100.0),
            "created_at": b.created_at
        })

    return result


def get_home_summary(db: Session, user: User, month: int = None, year: int = None) -> dict:
    """
    Retorna os dados consolidados para a tela Início a partir da mesma lógica centralizada.
    """
    today = datetime.date.today()
    sel_month = month or today.month
    sel_year = year or today.year

    sync_all_active_recurring_rules(db, user.id)
    generate_financial_alerts(db, user.id)

    # Transações elegíveis do mês selecionado (exclui canceladas e transferências entre contas)
    month_expenses = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        Transaction.status != "CANCELADA",
        Transaction.is_adjustment == False,
        Transaction.payment_method != "TRANSFERENCIA",
        extract('month', Transaction.date) == sel_month,
        extract('year', Transaction.date) == sel_year
    ).all()

    total_commitments_amount = sum(t.amount for t in month_expenses)
    total_commitments_count = len(month_expenses)

    paid_items = [t for t in month_expenses if is_tx_paid(t)]
    paid_amount = sum(t.amount for t in paid_items)
    paid_count = len(paid_items)

    overdue_items = [t for t in month_expenses if is_tx_overdue(t, today)]
    overdue_amount = sum(t.amount for t in overdue_items)
    overdue_count = len(overdue_items)

    pending_items = [t for t in month_expenses if is_tx_pending(t, today)]
    pending_amount = sum(t.amount for t in pending_items)
    pending_count = len(pending_items)

    next_due_tx = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        Transaction.status.in_(["PENDENTE", "PREVISTA"]),
        Transaction.is_adjustment == False,
        Transaction.payment_method != "TRANSFERENCIA",
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

    # Pre-fetch em memória para eliminar N+1
    user_cats = {
        c.id: c
        for c in db.query(Category).filter(
            or_(Category.user_id == user.id, Category.is_system_default == True)
        ).all()
    }
    user_accs = {a.id: a for a in db.query(Account).filter(Account.user_id == user.id).all()}
    user_cards = {c.id: c for c in db.query(CreditCard).filter(CreditCard.user_id == user.id).all()}

    category_expenses = []
    cat_totals = {}
    for t in month_expenses:
        cat_totals[t.category_id] = cat_totals.get(t.category_id, 0.0) + t.amount

    total_expense_val = sum(cat_totals.values()) or 1.0
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

    cards_summary = []
    for c in user_cards.values():
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

    upcoming_list = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        Transaction.status.in_(["PENDENTE", "PREVISTA", "ATRASADA"]),
        Transaction.is_adjustment == False,
        Transaction.payment_method != "TRANSFERENCIA",
        or_(
            and_(Transaction.due_date.isnot(None), Transaction.due_date >= today),
            and_(Transaction.due_date.is_(None), Transaction.date >= today)
        )
    ).order_by(func.coalesce(Transaction.due_date, Transaction.date).asc()).limit(4).all()

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

    recent_txs = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.status != "CANCELADA"
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
        "total_expenses_period": round(total_commitments_amount, 2),
        "cards_summary": cards_summary,
        "upcoming_commitments": [format_tx(t) for t in upcoming_list],
        "recent_transactions": [format_tx(t) for t in recent_txs],
        "unread_alerts_count": unread_alerts
    }


def get_dashboard_analytics(db: Session, user: User, month: int = None, year: int = None) -> dict:
    """Visão analítica consolidada do Dashboard (Análise Geral)."""
    today = datetime.date.today()
    sel_month = month or today.month
    sel_year = year or today.year

    sync_all_active_recurring_rules(db, user.id)

    # 1. Saldos consolidados de todas as contas ativas
    accounts = db.query(Account).filter(Account.user_id == user.id, Account.is_active == True).all()
    acc_ids = [a.id for a in accounts]
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

    # 2. Receitas e Despesas do mês selecionado (excluindo canceladas e transferências entre contas)
    month_txs = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.status != "CANCELADA",
        Transaction.is_adjustment == False,
        Transaction.payment_method != "TRANSFERENCIA",
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

    total_initial = sum(acc.initial_balance for acc in accounts)
    if acc_ids:
        if period_end < today or (period_start <= today <= period_end):
            past_inc_before = db.query(func.sum(Transaction.amount)).filter(
                Transaction.account_id.in_(acc_ids),
                Transaction.type == "RECEITA",
                Transaction.status.in_(["PAGA", "RECEBIDA"]),
                Transaction.date < period_start
            ).scalar() or 0.0
            past_exp_before = db.query(func.sum(Transaction.amount)).filter(
                Transaction.account_id.in_(acc_ids),
                Transaction.type == "DESPESA",
                Transaction.status.in_(["PAGA", "RECEBIDA"]),
                Transaction.date < period_start
            ).scalar() or 0.0
            opening_balance = total_initial + past_inc_before - past_exp_before
        else:
            inter_inc = db.query(func.sum(Transaction.amount)).filter(
                Transaction.account_id.in_(acc_ids),
                Transaction.type == "RECEITA",
                Transaction.status.in_(["PENDENTE", "PREVISTA"]),
                Transaction.date >= today,
                Transaction.date < period_start
            ).scalar() or 0.0
            inter_exp = db.query(func.sum(Transaction.amount)).filter(
                Transaction.account_id.in_(acc_ids),
                Transaction.type == "DESPESA",
                Transaction.status.in_(["PENDENTE", "PREVISTA", "ATRASADA"]),
                func.coalesce(Transaction.due_date, Transaction.date) >= today,
                func.coalesce(Transaction.due_date, Transaction.date) < period_start
            ).scalar() or 0.0
            opening_balance = total_current_balance + inter_inc - inter_exp
    else:
        opening_balance = 0.0

    opening_balance = round(opening_balance, 2)
    period_income_total = round(income_received + income_expected, 2)
    period_expense_total = round(expense_paid + expense_pending + overdue_val, 2)

    details_fmt = (
        f"Abertura: R$ {opening_balance:,.2f} + Receitas: R$ {period_income_total:,.2f} "
        f"- Despesas: R$ {period_expense_total:,.2f}"
    ).replace(",", "X").replace(".", ",").replace("X", ".")

    # 3. Compromissos futuros (a partir de amanhã)
    future_commitments = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == "DESPESA",
        Transaction.date > today,
        Transaction.status.in_(["PENDENTE", "PREVISTA"]),
        Transaction.is_adjustment == False,
        Transaction.payment_method != "TRANSFERENCIA"
    ).scalar() or 0.0

    # 4. Evolução mensal (últimos 6 meses até o mês selecionado)
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
        Transaction.status.in_(["PAGA", "RECEBIDA"]),
        Transaction.is_adjustment == False,
        Transaction.payment_method != "TRANSFERENCIA"
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

    # 5. Distribuição de gastos por categoria no mês selecionado
    user_cats_dash = {
        c.id: c
        for c in db.query(Category).filter(
            or_(Category.user_id == user.id, Category.is_system_default == True)
        ).all()
    }
    cat_totals = {}
    for t in month_txs:
        if t.type == "DESPESA":
            cat_totals[t.category_id] = cat_totals.get(t.category_id, 0.0) + t.amount

    total_exp_all = sum(cat_totals.values()) or 1.0
    category_distribution = []
    for cat_id, total_val in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
        cat = user_cats_dash.get(cat_id)
        if cat:
            category_distribution.append({
                "category_id": cat.id,
                "name": cat.name,
                "color": cat.color or "#D83A6F",
                "icon": cat.icon or "Tag",
                "amount": round(total_val, 2),
                "percentage": round((total_val / total_exp_all) * 100, 1)
            })

    # 6. Distribuição de status dos compromissos
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
