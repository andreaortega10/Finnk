from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, or_
from typing import List, Optional
import datetime
from ..database import get_db
from ..models import Transaction, User, Account, CreditCard, Category
from ..schemas import TransactionCreate, TransactionUpdate, TransactionStatusUpdate, TransactionOut
from ..auth import get_current_user
from ..services.audit_engine import log_audit
from ..services.alerts_engine import generate_financial_alerts

router = APIRouter(prefix="/api/transactions", tags=["Transações e Compromissos"])

def format_transaction_out(t: Transaction, db: Session) -> TransactionOut:
    cat = db.query(Category).filter(Category.id == t.category_id).first()
    acc = db.query(Account).filter(Account.id == t.account_id).first() if t.account_id else None
    crd = db.query(CreditCard).filter(CreditCard.id == t.credit_card_id).first() if t.credit_card_id else None
    return TransactionOut(
        id=t.id,
        user_id=t.user_id,
        account_id=t.account_id,
        credit_card_id=t.credit_card_id,
        category_id=t.category_id,
        category_name=cat.name if cat else "Geral",
        category_color=cat.color if cat else "#D83A6F",
        category_icon=cat.icon if cat else "Tag",
        account_name=acc.name if acc else None,
        credit_card_name=crd.name if crd else None,
        title=t.title,
        description=t.description,
        amount=t.amount,
        date=t.date,
        type=t.type,
        status=t.status,
        payment_method=t.payment_method,
        is_installment=t.is_installment,
        installment_id=t.installment_id,
        installment_number=t.installment_number,
        total_installments=t.total_installments,
        is_recurring=t.is_recurring,
        recurring_id=t.recurring_id,
        is_adjustment=t.is_adjustment,
        created_at=t.created_at,
        updated_at=t.updated_at
    )


@router.get("", response_model=List[TransactionOut])
def list_transactions(
    type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    account_id: Optional[int] = Query(None),
    credit_card_id: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    is_compromisso: Optional[bool] = Query(None),
    start_date: Optional[datetime.date] = Query(None),
    end_date: Optional[datetime.date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    if type:
        query = query.filter(Transaction.type == type.upper())
    if status_filter:
        if status_filter.upper() == "ATRASADA":
            today = datetime.date.today()
            from sqlalchemy import and_
            query = query.filter(
                or_(
                    Transaction.status == "ATRASADA",
                    and_(Transaction.status == "PENDENTE", Transaction.date < today)
                )
            )
        else:
            query = query.filter(Transaction.status == status_filter.upper())
            if status_filter.upper() == "PENDENTE":
                today = datetime.date.today()
                query = query.filter(Transaction.date >= today)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if credit_card_id:
        query = query.filter(Transaction.credit_card_id == credit_card_id)
    if month:
        query = query.filter(extract('month', Transaction.date) == month)
    if year:
        query = query.filter(extract('year', Transaction.date) == year)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(Transaction.title.ilike(s), Transaction.description.ilike(s)))
    if is_compromisso is True:
        # Compromissos são despesas a pagar ou a vencer
        query = query.filter(Transaction.type == "DESPESA")

    txs = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
    return [format_transaction_out(t, db) for t in txs]


@router.post("", response_model=TransactionOut)
def create_transaction(
    tx_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # RN02: Valor não pode ser zero
    if tx_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor da transação não pode ser igual ou menor que zero (RN02)."
        )

    # RN01: Deve pertencer a uma categoria e a uma conta financeira ou cartão
    category = db.query(Category).filter(
        Category.id == tx_data.category_id,
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria obrigatória e válida não informada (RN01).")

    if not tx_data.account_id and not tx_data.credit_card_id:
        # Se não informado, associa à primeira conta ativa do usuário
        user_acc = db.query(Account).filter(Account.user_id == current_user.id, Account.is_active == True).first()
        if user_acc:
            tx_data.account_id = user_acc.id
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta financeira ou cartão obrigatório (RN01).")

    # RN03: Transações futuras entram como PENDENTE; atuais/passadas podem ser pagas
    today = datetime.date.today()
    assigned_status = tx_data.status
    if tx_data.date > today:
        assigned_status = "PENDENTE"
    elif not assigned_status:
        # Se na data de hoje ou passada e não especificado
        if tx_data.type.upper() == "RECEITA":
            assigned_status = "RECEBIDA"
        else:
            assigned_status = "PENDENTE"

    tx = Transaction(
        user_id=current_user.id,
        account_id=tx_data.account_id,
        credit_card_id=tx_data.credit_card_id,
        category_id=tx_data.category_id,
        title=tx_data.title.strip(),
        description=tx_data.description.strip() if tx_data.description else None,
        amount=round(tx_data.amount, 2),
        date=tx_data.date,
        type=tx_data.type.upper(),
        status=assigned_status.upper(),
        payment_method=tx_data.payment_method or "OUTRO",
        is_installment=False
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    log_audit(db, current_user.id, "TRANSACTION", tx.id, "CREATE", {"title": tx.title, "amount": tx.amount, "type": tx.type})
    generate_financial_alerts(db, current_user.id)

    return format_transaction_out(tx, db)


@router.get("/{tx_id}", response_model=TransactionOut)
def get_transaction(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id == tx_id,
        Transaction.user_id == current_user.id
    ).first()

    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada.")
    return format_transaction_out(tx, db)


@router.put("/{tx_id}", response_model=TransactionOut)
def update_transaction(
    tx_id: int,
    tx_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id == tx_id,
        Transaction.user_id == current_user.id
    ).first()

    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada.")

    # RN08: Uma parcela já paga não pode ter valor ou data alterados diretamente
    if tx.is_installment and tx.status in ["PAGA", "RECEBIDA"]:
        if (tx_data.amount is not None and tx_data.amount != tx.amount) or (tx_data.date is not None and tx_data.date != tx.date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uma parcela já paga não pode ter valor ou data alterados diretamente (RN08). Registre um lançamento de estorno/ajuste para preservar a integridade histórica."
            )

    if tx_data.amount is not None:
        if tx_data.amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O valor da transação não pode ser zero (RN02).")
        tx.amount = round(tx_data.amount, 2)

    if tx_data.title is not None:
        tx.title = tx_data.title.strip()
    if tx_data.description is not None:
        tx.description = tx_data.description.strip()
    if tx_data.date is not None:
        tx.date = tx_data.date
    if tx_data.type is not None:
        tx.type = tx_data.type.upper()
    if tx_data.category_id is not None:
        tx.category_id = tx_data.category_id
    if tx_data.account_id is not None:
        tx.account_id = tx_data.account_id
    if tx_data.credit_card_id is not None:
        tx.credit_card_id = tx_data.credit_card_id
    if tx_data.status is not None:
        tx.status = tx_data.status.upper()
    if tx_data.payment_method is not None:
        tx.payment_method = tx_data.payment_method

    db.commit()
    db.refresh(tx)

    log_audit(db, current_user.id, "TRANSACTION", tx.id, "UPDATE", {"title": tx.title, "amount": tx.amount})
    generate_financial_alerts(db, current_user.id)

    return format_transaction_out(tx, db)


@router.patch("/{tx_id}/status", response_model=TransactionOut)
def update_transaction_status(
    tx_id: int,
    status_data: TransactionStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id == tx_id,
        Transaction.user_id == current_user.id
    ).first()

    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada.")

    new_status = status_data.status.upper()
    tx.status = new_status
    db.commit()
    db.refresh(tx)

    log_audit(db, current_user.id, "TRANSACTION", tx.id, "STATUS_CHANGE", {"new_status": new_status})
    generate_financial_alerts(db, current_user.id)

    return format_transaction_out(tx, db)


@router.delete("/{tx_id}")
def delete_transaction(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id == tx_id,
        Transaction.user_id == current_user.id
    ).first()

    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada.")

    # Se for parcela, alertar sobre parcelamento
    if tx.is_installment:
        pass  # O usuário pode excluir a parcela avulsa ou pelo endpoint de parcelamentos

    db.delete(tx)
    db.commit()

    log_audit(db, current_user.id, "TRANSACTION", tx_id, "DELETE", {"title": tx.title, "amount": tx.amount})
    return {"message": "Transação excluída com sucesso."}
