from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import InstallmentPurchase, User, Transaction, CreditCard, Category
from ..schemas import (
    InstallmentPurchaseCreate, InstallmentPurchaseOut, InstallmentDeleteOption, TransactionOut
)
from ..auth import get_current_user
from ..services.installments_engine import create_installment_purchase, delete_installment_purchase
from ..routers.transactions_router import format_transaction_out

router = APIRouter(prefix="/api/installments", tags=["Compras Parceladas"])

def format_installment_purchase(ip: InstallmentPurchase, db: Session) -> InstallmentPurchaseOut:
    card = db.query(CreditCard).filter(CreditCard.id == ip.credit_card_id).first()
    cat = db.query(Category).filter(Category.id == ip.category_id).first()
    
    installments_txs = db.query(Transaction).filter(
        Transaction.installment_id == ip.id,
        Transaction.user_id == ip.user_id
    ).order_by(Transaction.installment_number.asc()).all()

    paid_items = [t for t in installments_txs if t.status in ["PAGA", "RECEBIDA"]]
    pending_items = [t for t in installments_txs if t.status in ["PENDENTE", "ATRASADA"]]

    return InstallmentPurchaseOut(
        id=ip.id,
        title=ip.title,
        description=ip.description,
        total_amount=ip.total_amount,
        purchase_date=ip.purchase_date,
        first_due_date=ip.first_due_date,
        total_installments=ip.total_installments,
        credit_card_id=ip.credit_card_id,
        credit_card_name=card.name if card else None,
        category_id=ip.category_id,
        category_name=cat.name if cat else None,
        paid_count=len(paid_items),
        paid_amount=round(sum(t.amount for t in paid_items), 2),
        pending_count=len(pending_items),
        pending_amount=round(sum(t.amount for t in pending_items), 2),
        installments=[format_transaction_out(t, db) for t in installments_txs],
        created_at=ip.created_at
    )


@router.get("", response_model=List[InstallmentPurchaseOut])
def list_installments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    purchases = db.query(InstallmentPurchase).filter(
        InstallmentPurchase.user_id == current_user.id
    ).order_by(InstallmentPurchase.purchase_date.desc()).all()

    return [format_installment_purchase(p, db) for p in purchases]


@router.post("", response_model=InstallmentPurchaseOut)
def create_installment(
    data: InstallmentPurchaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    purchase = create_installment_purchase(
        db=db,
        user_id=current_user.id,
        title=data.title,
        total_amount=data.total_amount,
        purchase_date=data.purchase_date,
        first_due_date=data.first_due_date,
        total_installments=data.total_installments,
        credit_card_id=data.credit_card_id,
        category_id=data.category_id,
        description=data.description
    )
    return format_installment_purchase(purchase, db)


@router.get("/{purchase_id}", response_model=InstallmentPurchaseOut)
def get_installment(
    purchase_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    purchase = db.query(InstallmentPurchase).filter(
        InstallmentPurchase.id == purchase_id,
        InstallmentPurchase.user_id == current_user.id
    ).first()

    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelamento não encontrado.")

    return format_installment_purchase(purchase, db)


@router.delete("/{purchase_id}")
def delete_installment(
    purchase_id: int,
    delete_mode: str = Query("FUTURE_ONLY", description="FUTURE_ONLY ou ALL"),
    force_paid: bool = Query(False, description="Confirmação explícita para exclusão total com parcelas pagas"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return delete_installment_purchase(
        db=db,
        user_id=current_user.id,
        installment_id=purchase_id,
        delete_mode=delete_mode,
        force_paid=force_paid
    )
