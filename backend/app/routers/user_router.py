from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime
from ..database import get_db
from ..models import User, AuditLog, Transaction, Account, CreditCard, Category, Budget, RecurringRule, InstallmentPurchase, Alert
from ..schemas import AuditLogOut
from ..auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["Auditoria e LGPD"])

@router.get("/audit-logs", response_model=List[AuditLogOut])
def get_user_audit_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id
    ).order_by(AuditLog.created_at.desc()).limit(100).all()
    return logs


@router.get("/export-data")
def export_user_data_lgpd(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RNF04 - LGPD: Portabilidade total de dados.
    Exporta todos os dados financeiros e pessoais do usuário em formato JSON estruturado.
    """
    user_info = {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "default_currency": current_user.default_currency,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }

    accounts = [
        {"id": a.id, "name": a.name, "type": a.type, "initial_balance": a.initial_balance, "created_at": str(a.created_at)}
        for a in db.query(Account).filter(Account.user_id == current_user.id).all()
    ]

    cards = [
        {"id": c.id, "name": c.name, "brand": c.brand, "last_four_digits": c.last_four_digits, "limit_total": c.limit_total, "due_day": c.due_day}
        for c in db.query(CreditCard).filter(CreditCard.user_id == current_user.id).all()
    ]

    categories = [
        {"id": cat.id, "name": cat.name, "type": cat.type, "is_system_default": cat.is_system_default}
        for cat in db.query(Category).filter((Category.user_id == current_user.id) | (Category.user_id.is_(None))).all()
    ]

    transactions = [
        {
            "id": t.id,
            "title": t.title,
            "amount": t.amount,
            "date": str(t.date),
            "type": t.type,
            "status": t.status,
            "payment_method": t.payment_method,
            "is_installment": t.is_installment,
            "installment_number": t.installment_number,
            "is_recurring": t.is_recurring,
            "created_at": str(t.created_at)
        }
        for t in db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    ]

    installments = [
        {"id": p.id, "title": p.title, "total_amount": p.total_amount, "total_installments": p.total_installments, "purchase_date": str(p.purchase_date)}
        for p in db.query(InstallmentPurchase).filter(InstallmentPurchase.user_id == current_user.id).all()
    ]

    recurrings = [
        {"id": r.id, "title": r.title, "amount": r.amount, "frequency": r.frequency, "due_day": r.due_day, "is_active": r.is_active}
        for r in db.query(RecurringRule).filter(RecurringRule.user_id == current_user.id).all()
    ]

    budgets = [
        {"id": b.id, "category_id": b.category_id, "month": b.month, "year": b.year, "monthly_limit": b.monthly_limit}
        for b in db.query(Budget).filter(Budget.user_id == current_user.id).all()
    ]

    return {
        "export_date": str(datetime.date.today()),
        "user_profile": user_info,
        "accounts": accounts,
        "credit_cards": cards,
        "categories": categories,
        "transactions": transactions,
        "installment_purchases": installments,
        "recurring_rules": recurrings,
        "budgets": budgets
    }


@router.delete("/account")
def delete_account_lgpd(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RNF04 - LGPD: Direito de esquecimento.
    Exclui a conta e todos os dados financeiros vinculados ao usuário de forma definitiva.
    """
    db.delete(current_user)
    db.commit()
    return {"message": "Conta e todos os dados associados foram excluídos com sucesso em conformidade com a LGPD."}

@router.post("/reset-data")
def reset_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reseta apenas os dados da organização (transações, contas, etc), preservando a conta de usuário.
    """
    db.query(Alert).filter(Alert.user_id == current_user.id).delete()
    db.query(Budget).filter(Budget.user_id == current_user.id).delete()
    db.query(Transaction).filter(Transaction.user_id == current_user.id).delete()
    db.query(InstallmentPurchase).filter(InstallmentPurchase.user_id == current_user.id).delete()
    db.query(RecurringRule).filter(RecurringRule.user_id == current_user.id).delete()
    db.query(CreditCard).filter(CreditCard.user_id == current_user.id).delete()
    db.query(Account).filter(Account.user_id == current_user.id).delete()
    # Categorias personalizadas também são apagadas, mantendo só as padrão globais
    db.query(Category).filter(Category.user_id == current_user.id).delete()
    db.query(AuditLog).filter(AuditLog.user_id == current_user.id).delete()
    db.commit()

    return {"message": "Dados financeiros resetados com sucesso."}
