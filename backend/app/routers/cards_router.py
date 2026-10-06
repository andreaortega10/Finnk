from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import datetime
from ..database import get_db
from ..models import CreditCard, User, Transaction, Category
from ..schemas import CreditCardCreate, CreditCardUpdate, CreditCardOut, InvoiceOut, TransactionOut
from ..auth import get_current_user
from ..services.financial_engine import calculate_card_metrics
from ..services.audit_engine import log_audit

router = APIRouter(prefix="/api/cards", tags=["Cartões de Crédito"])

@router.get("", response_model=List[CreditCardOut])
def list_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cards = db.query(CreditCard).filter(CreditCard.user_id == current_user.id).all()
    result = []
    for c in cards:
        avail, inv = calculate_card_metrics(db, c)
        result.append(CreditCardOut(
            id=c.id,
            name=c.name,
            brand=c.brand,
            color=c.color,
            last_four_digits=c.last_four_digits,
            limit_total=c.limit_total,
            available_limit=avail,
            current_invoice_amount=inv,
            closing_day=c.closing_day,
            due_day=c.due_day,
            created_at=c.created_at
        ))
    return result


@router.post("", response_model=CreditCardOut)
def create_card(
    card_data: CreditCardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = CreditCard(
        user_id=current_user.id,
        name=card_data.name.strip(),
        brand=card_data.brand,
        color=card_data.color or "#D83A6F",
        last_four_digits=card_data.last_four_digits,
        limit_total=card_data.limit_total,
        closing_day=card_data.closing_day,
        due_day=card_data.due_day
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    log_audit(db, current_user.id, "CREDIT_CARD", card.id, "CREATE", {"name": card.name, "limit": card.limit_total})

    avail, inv = calculate_card_metrics(db, card)
    return CreditCardOut(
        id=card.id,
        name=card.name,
        brand=card.brand,
        color=card.color,
        last_four_digits=card.last_four_digits,
        limit_total=card.limit_total,
        available_limit=avail,
        current_invoice_amount=inv,
        closing_day=card.closing_day,
        due_day=card.due_day,
        created_at=card.created_at
    )


@router.put("/{card_id}", response_model=CreditCardOut)
def update_card(
    card_id: int,
    card_data: CreditCardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(CreditCard).filter(
        CreditCard.id == card_id,
        CreditCard.user_id == current_user.id
    ).first()

    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartão de crédito não encontrado.")

    if card_data.name is not None:
        card.name = card_data.name.strip()
    if card_data.brand is not None:
        card.brand = card_data.brand
    if card_data.color is not None:
        card.color = card_data.color
    if card_data.last_four_digits is not None:
        card.last_four_digits = card_data.last_four_digits
    if card_data.limit_total is not None:
        card.limit_total = card_data.limit_total
    if card_data.closing_day is not None:
        card.closing_day = card_data.closing_day
    if card_data.due_day is not None:
        card.due_day = card_data.due_day

    db.commit()
    db.refresh(card)

    log_audit(db, current_user.id, "CREDIT_CARD", card.id, "UPDATE", {"name": card.name})

    avail, inv = calculate_card_metrics(db, card)
    return CreditCardOut(
        id=card.id,
        name=card.name,
        brand=card.brand,
        color=card.color,
        last_four_digits=card.last_four_digits,
        limit_total=card.limit_total,
        available_limit=avail,
        current_invoice_amount=inv,
        closing_day=card.closing_day,
        due_day=card.due_day,
        created_at=card.created_at
    )


@router.delete("/{card_id}")
def delete_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(CreditCard).filter(
        CreditCard.id == card_id,
        CreditCard.user_id == current_user.id
    ).first()

    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartão de crédito não encontrado.")

    db.delete(card)
    db.commit()

    log_audit(db, current_user.id, "CREDIT_CARD", card_id, "DELETE")
    return {"message": "Cartão excluído com sucesso."}


@router.get("/{card_id}/invoices", response_model=InvoiceOut)
def get_card_invoice(
    card_id: int,
    month: int = Query(None),
    year: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(CreditCard).filter(
        CreditCard.id == card_id,
        CreditCard.user_id == current_user.id
    ).first()

    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartão não encontrado.")

    today = datetime.date.today()
    sel_month = month or today.month
    sel_year = year or today.year

    # Data de fechamento e vencimento estimadas
    try:
        closing_date = datetime.date(sel_year, sel_month, card.closing_day)
        due_date = datetime.date(sel_year, sel_month, card.due_day)
    except ValueError:
        closing_date = datetime.date(sel_year, sel_month, 28)
        due_date = datetime.date(sel_year, sel_month, 28)

    # Transações lançadas no cartão neste mês de vencimento
    txs = db.query(Transaction).filter(
        Transaction.credit_card_id == card.id,
        Transaction.user_id == current_user.id,
        Transaction.type == "DESPESA"
    ).all()

    # Filtra transações correspondentes a este ciclo
    invoice_items = [t for t in txs if t.date.month == sel_month and t.date.year == sel_year]
    total_invoice = sum(t.amount for t in invoice_items)

    all_paid = len(invoice_items) > 0 and all(t.status == "PAGA" for t in invoice_items)
    status_str = "PAGA" if all_paid else ("FECHADA" if today >= closing_date else "ABERTA")

    def format_t(t: Transaction):
        cat = db.query(Category).filter(Category.id == t.category_id).first()
        return TransactionOut(
            id=t.id,
            user_id=t.user_id,
            account_id=t.account_id,
            credit_card_id=t.credit_card_id,
            category_id=t.category_id,
            category_name=cat.name if cat else "Geral",
            category_color=cat.color if cat else "#D83A6F",
            category_icon=cat.icon if cat else "Tag",
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

    return InvoiceOut(
        card_id=card.id,
        card_name=card.name,
        brand=card.brand,
        color=card.color,
        last_four_digits=card.last_four_digits,
        month=sel_month,
        year=sel_year,
        closing_date=closing_date,
        due_date=due_date,
        total_amount=round(total_invoice, 2),
        status=status_str,
        items=[format_t(t) for t in invoice_items]
    )
