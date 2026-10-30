import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from ..models import RecurringRule, Transaction
from .audit_engine import log_audit

# Horizonte padrão limitado e documentado quando end_date não é informado (6 meses)
DEFAULT_RECURRING_HORIZON_MONTHS = 6


def _get_cycle_key(d: datetime.date, frequency: str):
    freq = (frequency or "MENSAL").upper()
    if freq == "MENSAL":
        return ("MENSAL", d.year, d.month)
    elif freq == "ANUAL":
        return ("ANUAL", d.year)
    elif freq == "SEMANAL":
        iso = d.isocalendar()
        return ("SEMANAL", iso[0], iso[1], d)
    return ("OUTRO", d)


def generate_recurring_transactions_for_rule(
    db: Session,
    rule: RecurringRule,
    months_ahead: int = DEFAULT_RECURRING_HORIZON_MONTHS,
    existing_txs: list = None,
    auto_commit: bool = True
) -> int:
    """
    Gera lançamentos previstos (PENDENTE) até a data limite (end_date) definida pelo usuário
    ou pelo horizonte padrão limitado (months_ahead = 6 meses).
    Recorrências são previsões: nunca nascem como RECEBIDA ou PAGA automaticamente.
    Retorna a quantidade de novos lançamentos gerados.
    """
    if not rule.is_active:
        return 0

    today = datetime.date.today()
    horizon_months = months_ahead if months_ahead is not None else DEFAULT_RECURRING_HORIZON_MONTHS

    if rule.end_date:
        limit_date = rule.end_date
    else:
        base_ref = max(today, rule.start_date)
        limit_date = base_ref + relativedelta(months=horizon_months)

    if existing_txs is None:
        existing_txs = db.query(Transaction).filter(
            Transaction.recurring_id == rule.id,
            Transaction.user_id == rule.user_id
        ).all()

    existing_dates = {t.date for t in existing_txs}
    existing_cycles = {_get_cycle_key(t.date, rule.frequency) for t in existing_txs}

    current_date = rule.start_date
    created_count = 0
    freq = (rule.frequency or "MENSAL").upper()

    while current_date <= limit_date:
        cycle_key = _get_cycle_key(current_date, freq)

        # Evita duplicidade mesmo que uma ocorrência do ciclo já tenha sido confirmada, editada ou cancelada
        if current_date not in existing_dates and cycle_key not in existing_cycles:
            current_due_date = None
            if rule.due_day:
                try:
                    current_due_date = current_date.replace(day=rule.due_day)
                except ValueError:
                    import calendar
                    last_d = calendar.monthrange(current_date.year, current_date.month)[1]
                    current_due_date = current_date.replace(day=min(rule.due_day, last_d))

            # Recorrências são previsões: nascem como PENDENTE (ou ATRASADA se despesa já vencida)
            if rule.type == "RECEITA":
                status = "PENDENTE"
            else:
                status = "PENDENTE"
                if current_due_date and current_due_date < today:
                    status = "ATRASADA"

            new_tx = Transaction(
                user_id=rule.user_id,
                account_id=rule.account_id,
                category_id=rule.category_id,
                title=rule.title,
                description=rule.description or f"Lançamento recorrente ({freq.lower()})",
                amount=round(rule.amount, 2),
                date=current_date,
                due_date=current_due_date,
                type=rule.type,
                status=status,
                payment_method="OUTRO",
                is_recurring=True,
                recurring_id=rule.id
            )
            db.add(new_tx)
            existing_dates.add(current_date)
            existing_cycles.add(cycle_key)
            created_count += 1

        if freq == "MENSAL":
            current_date = current_date + relativedelta(months=1)
        elif freq == "SEMANAL":
            current_date = current_date + relativedelta(weeks=1)
        elif freq == "ANUAL":
            current_date = current_date + relativedelta(years=1)
        else:
            break

    if auto_commit and created_count > 0:
        db.commit()

    return created_count


def sync_all_active_recurring_rules(db: Session, user_id: int):
    """
    Sincroniza todas as recorrências ativas do usuário em lote (sem queries N+1).
    """
    rules = db.query(RecurringRule).filter(
        RecurringRule.user_id == user_id,
        RecurringRule.is_active == True
    ).all()

    if not rules:
        return

    today = datetime.date.today()
    rule_ids = [r.id for r in rules]

    # Busca todas as transações recorrentes dessas regras em uma única query
    all_rec_txs = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.recurring_id.in_(rule_ids)
    ).all()

    txs_by_rule = {}
    for t in all_rec_txs:
        txs_by_rule.setdefault(t.recurring_id, []).append(t)

    dirty = False
    for rule in rules:
        if rule.end_date and rule.end_date < today:
            rule.is_active = False
            dirty = True
        else:
            added = generate_recurring_transactions_for_rule(
                db,
                rule,
                months_ahead=DEFAULT_RECURRING_HORIZON_MONTHS,
                existing_txs=txs_by_rule.get(rule.id, []),
                auto_commit=False
            )
            if added > 0:
                dirty = True

    if dirty:
        db.commit()


def update_recurring_rule_and_future_items(
    db: Session,
    user_id: int,
    rule_id: int,
    new_title: str = None,
    new_amount: float = None,
    new_due_day: int = None,
    new_alert_day: int = None,
    alert_day: int = None,
    new_end_date: datetime.date = None,
    is_active: bool = None
):
    rule = db.query(RecurringRule).filter(
        RecurringRule.id == rule_id,
        RecurringRule.user_id == user_id
    ).first()

    if not rule:
        return None

    effective_alert_day = new_alert_day if new_alert_day is not None else alert_day

    if new_title is not None:
        rule.title = new_title
    if new_amount is not None:
        rule.amount = round(new_amount, 2)
    if new_due_day is not None:
        rule.due_day = new_due_day
    if effective_alert_day is not None:
        rule.alert_day = effective_alert_day
    if new_end_date is not None:
        rule.end_date = new_end_date
    if is_active is not None:
        rule.is_active = is_active

    today = datetime.date.today()

    future_pending = db.query(Transaction).filter(
        Transaction.recurring_id == rule_id,
        Transaction.user_id == user_id,
        Transaction.date >= today,
        Transaction.status.in_(["PENDENTE", "PREVISTA", "ATRASADA"])
    ).all()

    for tx in future_pending:
        # Se a regra foi desativada ou a data ultrapassa o novo end_date, remove previsões futuras não efetivadas
        if (is_active is False and tx.date > today) or (rule.end_date and tx.date > rule.end_date):
            db.delete(tx)
            continue

        if new_title:
            tx.title = new_title
        if new_amount is not None:
            tx.amount = round(new_amount, 2)
        if new_due_day and rule.frequency == "MENSAL":
            try:
                tx.due_date = tx.date.replace(day=new_due_day)
            except ValueError:
                import calendar
                last_d = calendar.monthrange(tx.date.year, tx.date.month)[1]
                tx.due_date = tx.date.replace(day=min(new_due_day, last_d))

    db.commit()

    # Se continua ativa, garante geração dentro do horizonte atualizado
    if rule.is_active:
        generate_recurring_transactions_for_rule(db, rule)

    db.refresh(rule)
    log_audit(db, user_id, "RECURRING_RULE", rule_id, "UPDATE", {"new_amount": new_amount, "is_active": rule.is_active})
    return rule
