import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from ..models import RecurringRule, Transaction
from .audit_engine import log_audit

def generate_recurring_transactions_for_rule(
    db: Session,
    rule: RecurringRule,
    months_ahead: int = 3
):
    """
    RN09:
    Gera lançamentos automáticos mantendo antecedência configurável (padrão 3 meses).
    Verifica se já existe lançamento para a data para evitar duplicatas.
    """
    if not rule.is_active:
        return

    today = datetime.date.today()
    limit_date = today + relativedelta(months=months_ahead)
    
    # Data de início a considerar:
    current_date = rule.start_date
    if rule.frequency == "MENSAL":
        # Ajusta para o due_day especificado
        try:
            current_date = current_date.replace(day=rule.due_day)
        except ValueError:
            # Caso o mês não tenha o dia (ex: dia 31 em fevereiro)
            current_date = current_date.replace(day=28)

    while current_date <= limit_date:
        if rule.end_date and current_date > rule.end_date:
            break

        # Verifica se já existe transação criada para esta regra nesta data exata
        existing = db.query(Transaction).filter(
            Transaction.recurring_id == rule.id,
            Transaction.date == current_date,
            Transaction.user_id == rule.user_id
        ).first()

        if not existing:
            # RN03: Se data futura -> Pendente; se hoje ou passada -> pode ser pendente/atrasada
            status = "PENDENTE"
            if current_date < today:
                status = "ATRASADA"

            new_tx = Transaction(
                user_id=rule.user_id,
                account_id=rule.account_id,
                category_id=rule.category_id,
                title=rule.title,
                description=rule.description or f"Lançamento recorrente ({rule.frequency.lower()})",
                amount=rule.amount,
                date=current_date,
                type=rule.type,
                status=status,
                payment_method="OUTRO",
                is_recurring=True,
                recurring_id=rule.id
            )
            db.add(new_tx)

        # Avança para o próximo período
        if rule.frequency == "MENSAL":
            current_date = current_date + relativedelta(months=1)
        elif rule.frequency == "SEMANAL":
            current_date = current_date + relativedelta(weeks=1)
        elif rule.frequency == "ANUAL":
            current_date = current_date + relativedelta(years=1)
        else:
            break

    db.commit()


def sync_all_active_recurring_rules(db: Session, user_id: int):
    """Sincroniza todas as recorrências ativas do usuário garantindo 3 meses à frente."""
    rules = db.query(RecurringRule).filter(
        RecurringRule.user_id == user_id,
        RecurringRule.is_active == True
    ).all()
    for rule in rules:
        generate_recurring_transactions_for_rule(db, rule)


def update_recurring_rule_and_future_items(
    db: Session,
    user_id: int,
    rule_id: int,
    new_title: str = None,
    new_amount: float = None,
    new_due_day: int = None,
    new_end_date: datetime.date = None,
    is_active: bool = None
):
    """
    RN10:
    Alteração de valor ou detalhes em um item recorrente afeta apenas os lançamentos
    FUTUROS e PENDENTES a partir da data atual. Lançamentos pagos e históricos permanecem intactos.
    """
    rule = db.query(RecurringRule).filter(
        RecurringRule.id == rule_id,
        RecurringRule.user_id == user_id
    ).first()

    if not rule:
        return None

    if new_title is not None:
        rule.title = new_title
    if new_amount is not None:
        rule.amount = new_amount
    if new_due_day is not None:
        rule.due_day = new_due_day
    if new_end_date is not None:
        rule.end_date = new_end_date
    if is_active is not None:
        rule.is_active = is_active

    today = datetime.date.today()

    # Atualiza apenas lançamentos futuros pendentes
    future_pending = db.query(Transaction).filter(
        Transaction.recurring_id == rule_id,
        Transaction.user_id == user_id,
        Transaction.date >= today,
        Transaction.status.in_(["PENDENTE", "ATRASADA"])
    ).all()

    for tx in future_pending:
        if new_title:
            tx.title = new_title
        if new_amount is not None:
            tx.amount = new_amount
        if new_due_day and rule.frequency == "MENSAL":
            try:
                tx.date = tx.date.replace(day=new_due_day)
            except ValueError:
                tx.date = tx.date.replace(day=28)

    db.commit()
    db.refresh(rule)

    log_audit(db, user_id, "RECURRING_RULE", rule_id, "UPDATE", {"new_amount": new_amount, "is_active": is_active})
    return rule
