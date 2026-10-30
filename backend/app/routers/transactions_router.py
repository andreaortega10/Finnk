from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, or_, and_
from typing import List, Optional
import datetime
from ..database import get_db
from ..models import Transaction, User, Account, CreditCard, Category
from ..schemas import TransactionCreate, TransactionUpdate, TransactionStatusUpdate, TransactionOut
from ..auth import get_current_user
from ..services.audit_engine import log_audit
from ..services.alerts_engine import generate_financial_alerts
from ..services.recurring_engine import sync_all_active_recurring_rules
from ..services.financial_engine import is_tx_overdue, calculate_card_metrics

router = APIRouter(prefix="/api/transactions", tags=["Transações e Compromissos"])


def format_transaction_out(
    t: Transaction,
    db: Session,
    cats_map: dict = None,
    accs_map: dict = None,
    cards_map: dict = None,
    today: datetime.date = None
) -> TransactionOut:
    if cats_map is not None:
        cat = cats_map.get(t.category_id)
    else:
        cat = db.query(Category).filter(Category.id == t.category_id).first()

    if accs_map is not None:
        acc = accs_map.get(t.account_id) if t.account_id else None
    else:
        acc = db.query(Account).filter(Account.id == t.account_id).first() if t.account_id else None

    if cards_map is not None:
        crd = cards_map.get(t.credit_card_id) if t.credit_card_id else None
    else:
        crd = db.query(CreditCard).filter(CreditCard.id == t.credit_card_id).first() if t.credit_card_id else None

    if today is None:
        today = datetime.date.today()

    eff_status = t.status
    if is_tx_overdue(t, today):
        eff_status = "ATRASADA"

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
        due_date=t.due_date,
        type=t.type,
        status=eff_status,
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
    sync_all_active_recurring_rules(db, current_user.id)

    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if not status_filter or status_filter.upper() != "CANCELADA":
        query = query.filter(Transaction.status != "CANCELADA")

    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    if type:
        query = query.filter(Transaction.type == type.upper())

    today = datetime.date.today()
    if status_filter:
        sf = status_filter.upper()
        if sf in ["PAGA", "RECEBIDA"]:
            query = query.filter(Transaction.status.in_(["PAGA", "RECEBIDA"]))
        elif sf == "ATRASADA":
            query = query.filter(
                Transaction.type == "DESPESA",
                or_(
                    Transaction.status == "ATRASADA",
                    and_(Transaction.status.in_(["PENDENTE", "PREVISTA"]), Transaction.due_date.isnot(None), Transaction.due_date < today)
                )
            )
        elif sf in ["PENDENTE", "PREVISTA"]:
            query = query.filter(
                Transaction.status.in_(["PENDENTE", "PREVISTA"]),
                or_(
                    Transaction.type == "RECEITA",
                    Transaction.due_date.is_(None),
                    Transaction.due_date >= today
                )
            )
        else:
            query = query.filter(Transaction.status == sf)

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
        query = query.outerjoin(Category, Transaction.category_id == Category.id).filter(
            or_(
                Transaction.title.ilike(s),
                Transaction.description.ilike(s),
                Category.name.ilike(s)
            )
        )
    if is_compromisso is True:
        query = query.filter(Transaction.type == "DESPESA")

    txs = query.order_by(Transaction.date.desc(), Transaction.created_at.desc(), Transaction.id.desc()).all()
    if not txs:
        return []

    # Pre-fetch em memória para eliminar N+1 queries (3 queries fixas em vez de 3*N)
    cats_map = {
        c.id: c
        for c in db.query(Category).filter(
            or_(Category.user_id == current_user.id, Category.is_system_default == True)
        ).all()
    }
    accs_map = {a.id: a for a in db.query(Account).filter(Account.user_id == current_user.id).all()}
    cards_map = {c.id: c for c in db.query(CreditCard).filter(CreditCard.user_id == current_user.id).all()}

    return [format_transaction_out(t, db, cats_map, accs_map, cards_map, today) for t in txs]


@router.post("", response_model=TransactionOut)
def create_transaction(
    tx_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if tx_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor da transação não pode ser igual ou menor que zero (RN02)."
        )

    category = db.query(Category).filter(
        Category.id == tx_data.category_id,
        or_(Category.user_id == current_user.id, Category.user_id.is_(None), Category.is_system_default == True)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria obrigatória e válida não informada (RN01).")

    if tx_data.credit_card_id and tx_data.type.upper() == "DESPESA":
        card = db.query(CreditCard).filter(
            CreditCard.id == tx_data.credit_card_id,
            CreditCard.user_id == current_user.id
        ).first()
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartão de crédito não encontrado.")
        available_limit, _ = calculate_card_metrics(db, card)
        if tx_data.amount > available_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limite insuficiente no cartão '{card.name}'. Limite disponível: R$ {available_limit:.2f}, valor da compra: R$ {tx_data.amount:.2f}."
            )
        tx_data.account_id = None

    if not tx_data.account_id and not tx_data.credit_card_id:
        user_acc = db.query(Account).filter(Account.user_id == current_user.id, Account.is_active == True).first()
        if user_acc:
            tx_data.account_id = user_acc.id
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta financeira ou cartão obrigatório (RN01).")

    today = datetime.date.today()
    assigned_status = tx_data.status
    if tx_data.date > today:
        if not assigned_status or assigned_status.upper() in ["PAGA", "RECEBIDA"]:
            assigned_status = "PENDENTE"
    elif not assigned_status:
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
        due_date=tx_data.due_date,
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
    if tx_data.due_date is not None:
        tx.due_date = tx_data.due_date
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

    # Confirmação / alteração de status in-place (nunca duplica registros)
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

    # Se for ocorrência gerada por recorrência ativa, marca como CANCELADA para não ser recriada no sync
    if tx.is_recurring and tx.recurring_id is not None:
        tx.status = "CANCELADA"
        db.commit()
    else:
        db.delete(tx)
        db.commit()

    log_audit(db, current_user.id, "TRANSACTION", tx_id, "DELETE", {"title": tx.title, "amount": tx.amount})
    return {"message": "Transação excluída com sucesso."}
