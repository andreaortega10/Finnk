from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime
from ..database import get_db
from ..models import RecurringRule, User, Account, Category, Transaction
from ..schemas import RecurringRuleCreate, RecurringRuleUpdate, RecurringRuleOut
from ..auth import get_current_user
from ..services.recurring_engine import (
    generate_recurring_transactions_for_rule,
    update_recurring_rule_and_future_items
)
from ..services.audit_engine import log_audit

router = APIRouter(prefix="/api/recurring", tags=["Recorrências"])

def format_recurring_rule(rule: RecurringRule, db: Session) -> RecurringRuleOut:
    cat = db.query(Category).filter(Category.id == rule.category_id).first()
    acc = db.query(Account).filter(Account.id == rule.account_id).first() if rule.account_id else None

    # Encontra o próximo vencimento
    today = datetime.date.today()
    next_tx = db.query(Transaction).filter(
        Transaction.recurring_id == rule.id,
        Transaction.date >= today,
        Transaction.status.in_(["PENDENTE", "ATRASADA"])
    ).order_by(Transaction.date.asc()).first()

    return RecurringRuleOut(
        id=rule.id,
        title=rule.title,
        description=rule.description,
        amount=rule.amount,
        type=rule.type,
        frequency=rule.frequency,
        due_day=rule.due_day,
        start_date=rule.start_date,
        end_date=rule.end_date,
        is_active=rule.is_active,
        category_id=rule.category_id,
        category_name=cat.name if cat else None,
        account_id=rule.account_id,
        account_name=acc.name if acc else None,
        next_due_date=next_tx.date if next_tx else None,
        created_at=rule.created_at
    )


@router.get("", response_model=List[RecurringRuleOut])
def list_recurring_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rules = db.query(RecurringRule).filter(
        RecurringRule.user_id == current_user.id
    ).all()
    return [format_recurring_rule(r, db) for r in rules]


@router.post("", response_model=RecurringRuleOut)
def create_recurring_rule(
    data: RecurringRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rule = RecurringRule(
        user_id=current_user.id,
        account_id=data.account_id,
        category_id=data.category_id,
        title=data.title.strip(),
        description=data.description.strip() if data.description else None,
        amount=round(data.amount, 2),
        type=data.type.upper(),
        frequency=data.frequency.upper(),
        due_day=data.due_day,
        alert_day=data.alert_day,
        start_date=data.start_date,
        end_date=data.end_date,
        is_active=True
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # RN09: Gera lançamentos automáticos futuros (3 meses à frente)
    generate_recurring_transactions_for_rule(db, rule)

    log_audit(db, current_user.id, "RECURRING_RULE", rule.id, "CREATE", {"title": rule.title, "amount": rule.amount})
    return format_recurring_rule(rule, db)


@router.put("/{rule_id}", response_model=RecurringRuleOut)
def update_recurring(
    rule_id: int,
    data: RecurringRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # RN10: Atualiza a regra e reflete APENAS em lançamentos futuros pendentes
    rule = update_recurring_rule_and_future_items(
        db=db,
        user_id=current_user.id,
        rule_id=rule_id,
        new_title=data.title.strip() if data.title else None,
        new_amount=round(data.amount, 2) if data.amount else None,
        new_due_day=data.due_day,
        alert_day=data.alert_day,
        new_end_date=data.end_date,
        is_active=data.is_active
    )

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regra de recorrência não encontrada.")

    return format_recurring_rule(rule, db)


@router.patch("/{rule_id}/toggle", response_model=RecurringRuleOut)
def toggle_recurring_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rule = db.query(RecurringRule).filter(
        RecurringRule.id == rule_id,
        RecurringRule.user_id == current_user.id
    ).first()

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regra não encontrada.")

    rule.is_active = not rule.is_active
    db.commit()
    db.refresh(rule)

    if rule.is_active:
        generate_recurring_transactions_for_rule(db, rule)

    log_audit(db, current_user.id, "RECURRING_RULE", rule.id, "TOGGLE", {"is_active": rule.is_active})
    return format_recurring_rule(rule, db)


@router.delete("/{rule_id}")
def delete_recurring_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rule = db.query(RecurringRule).filter(
        RecurringRule.id == rule_id,
        RecurringRule.user_id == current_user.id
    ).first()

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regra não encontrada.")

    # Remove lançamentos futuros pendentes associados
    today = datetime.date.today()
    future_pending = db.query(Transaction).filter(
        Transaction.recurring_id == rule_id,
        Transaction.user_id == current_user.id,
        Transaction.date >= today,
        Transaction.status.in_(["PENDENTE", "ATRASADA"])
    ).all()

    for tx in future_pending:
        db.delete(tx)

    db.delete(rule)
    db.commit()

    log_audit(db, current_user.id, "RECURRING_RULE", rule_id, "DELETE")
    return {"message": "Recorrência encerrada e lançamentos futuros pendentes removidos."}


