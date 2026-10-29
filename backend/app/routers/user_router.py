from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime
from ..database import get_db
from ..models import User, AuditLog, Transaction, Account, CreditCard, Category, Budget, RecurringRule, InstallmentPurchase, Alert, AIChatMessage
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
    Reseta todos os dados financeiros do usuário (transações, faturas, compromissos, contas, cartões e regras),
    preservando estritamente a conta cadastral, a autenticação e as credenciais.
    Recria uma conta corrente zerada padrão e as categorias do sistema limpas.
    """
    from ..services.seed_helper import seed_default_categories
    from ..services.audit_engine import log_audit

    try:
        # 1. Exclui alertas, orçamentos e histórico de chat da IA vinculados
        db.query(Alert).filter(Alert.user_id == current_user.id).delete(synchronize_session=False)
        db.query(Budget).filter(Budget.user_id == current_user.id).delete(synchronize_session=False)
        db.query(AIChatMessage).filter(AIChatMessage.user_id == current_user.id).delete(synchronize_session=False)
        
        # 2. Exclui todas as transações (despesas, receitas, parcelas)
        db.query(Transaction).filter(Transaction.user_id == current_user.id).delete(synchronize_session=False)
        
        # 3. Exclui compras-mãe parceladas e regras recorrentes
        db.query(InstallmentPurchase).filter(InstallmentPurchase.user_id == current_user.id).delete(synchronize_session=False)
        db.query(RecurringRule).filter(RecurringRule.user_id == current_user.id).delete(synchronize_session=False)
        
        # 4. Exclui cartões e contas
        db.query(CreditCard).filter(CreditCard.user_id == current_user.id).delete(synchronize_session=False)
        db.query(Account).filter(Account.user_id == current_user.id).delete(synchronize_session=False)
        
        # 5. Exclui categorias personalizadas criadas pelo usuário
        db.query(Category).filter(Category.user_id == current_user.id).delete(synchronize_session=False)
        
        # 6. Recria uma Conta Corrente inicial zerada padrão para o usuário
        clean_account = Account(
            user_id=current_user.id,
            name="Conta Corrente",
            type="CORRENTE",
            color="#3B82F6",
            initial_balance=0.0,
            is_active=True
        )
        db.add(clean_account)
        
        # 7. Recria as categorias padrão do sistema limpas
        seed_default_categories(db, current_user.id)
        
        # 8. Registra log de auditoria
        log_audit(db, current_user.id, "USER", current_user.id, "RESET_DATA", {"action": "clean_reset"})
        
        # 9. Executa o commit atômico no banco de dados relacional
        db.commit()
        
        return {
            "message": "Todos os dados financeiros foram resetados com sucesso. Sua conta está limpa e pronta para uso.",
            "status": "success"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao resetar dados financeiros: {str(e)}"
        )


@router.post("/remove-demo-data")
def remove_demo_data_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove de forma cirúrgica e segura apenas os dados de demonstração (Mariana),
    preservando totalmente contas bancárias, credenciais e lançamentos legítimos.
    """
    from ..services.seed_helper import remove_demo_data
    from ..services.audit_engine import log_audit

    result = remove_demo_data(db, current_user.id)
    log_audit(db, current_user.id, "USER", current_user.id, "REMOVE_DEMO_DATA")
    return result

