import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from ..models import RecurringRule, Transaction
from .audit_engine import log_audit

def generate_recurring_transactions_for_rule(
    db: Session,
    rule: RecurringRule
):
    """
    Gera lanamentos automǭticos at a data limite (end_date) definida pelo usuǭrio.
    O usuǭrio tem controle total do intervalo.
    """
    if not rule.is_active:
        return

    today = datetime.date.today()
    if not rule.end_date:
        # Se por algum motivo histrico nǜo tiver end_date, consideramos inativa ou evitamos loop infinito.
        return

    limit_date = rule.end_date
    current_date = rule.start_date
    
    # Se a frequǦncia  MENSAL e existe um dia de alerta/vencimento
    # O current_date baseia-se no start_date.
    # O vencimento/alerta sǜo resolvidos depois.

    while current_date <= limit_date:
        # Verifica se jǭ existe transaǜo criada para esta regra nesta data de ciclo exata
        existing = db.query(Transaction).filter(
            Transaction.recurring_id == rule.id,
            Transaction.date == current_date,
            Transaction.user_id == rule.user_id
        ).first()

        if not existing:
            # Calcula data de vencimento e alerta baseados neste mǦs/ciclo
            current_due_date = None
            if rule.due_day:
                try:
                    current_due_date = current_date.replace(day=rule.due_day)
                except ValueError:
                    current_due_date = current_date.replace(day=28)
            
            # Status e atraso s importam se houver data de vencimento
            status = "PENDENTE"
            if current_due_date and current_due_date < today:
                status = "ATRASADA"
            elif not current_due_date and current_date < today:
                # Se nǜo tem vencimento, nǜo consideramos atrasado, apenas efetuado ou pendente.
                status = "PENDENTE" 

            new_tx = Transaction(
                user_id=rule.user_id,
                account_id=rule.account_id,
                category_id=rule.category_id,
                title=rule.title,
                description=rule.description or f"Lanamento recorrente ({rule.frequency.lower()})",
                amount=rule.amount,
                date=current_date, # Data de registro/movimentaǜo do ciclo
                due_date=current_due_date, # Data de vencimento (opcional)
                type=rule.type,
                status=status,
                payment_method="OUTRO",
                is_recurring=True,
                recurring_id=rule.id
            )
            db.add(new_tx)

        # Avana para o prximo perodo
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
    """Sincroniza todas as recorrǦncias ativas do usuǭrio."""
    rules = db.query(RecurringRule).filter(
        RecurringRule.user_id == user_id,
        RecurringRule.is_active == True
    ).all()
    today = datetime.date.today()
    for rule in rules:
        if rule.end_date and rule.end_date < today:
            # Marca como inativa se jǭ passou
            rule.is_active = False
            db.commit()
        else:
            generate_recurring_transactions_for_rule(db, rule)


def update_recurring_rule_and_future_items(
    db: Session,
    user_id: int,
    rule_id: int,
    new_title: str = None,
    new_amount: float = None,
    new_due_day: int = None,
    new_alert_day: int = None,
    new_end_date: datetime.date = None,
    is_active: bool = None
):
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
    if new_alert_day is not None:
        rule.alert_day = new_alert_day
    if new_end_date is not None:
        rule.end_date = new_end_date
    if is_active is not None:
        rule.is_active = is_active

    today = datetime.date.today()

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
                tx.due_date = tx.date.replace(day=new_due_day)
            except ValueError:
                tx.due_date = tx.date.replace(day=28)

    db.commit()
    db.refresh(rule)

    log_audit(db, user_id, "RECURRING_RULE", rule_id, "UPDATE", {"new_amount": new_amount, "is_active": is_active})
    return rule
