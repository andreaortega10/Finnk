import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models import InstallmentPurchase, Transaction, CreditCard, Category
from .audit_engine import log_audit

def create_installment_purchase(
    db: Session,
    user_id: int,
    title: str,
    total_amount: float,
    purchase_date: datetime.date,
    first_due_date: datetime.date,
    total_installments: int,
    credit_card_id: int,
    category_id: int,
    description: str = None
) -> InstallmentPurchase:
    """
    RN05 & RN06:
    Cria a compra-mãe e gera as N parcelas vinculadas.
    Calcula o valor base por parcela com 2 casas decimais e adiciona a diferença na última parcela.
    """
    if total_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor total da compra deve ser maior que zero."
        )
    if total_installments < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A compra parcelada deve ter no mínimo 2 parcelas."
        )
    
    # Valida cartão e categoria pertencentes ao usuário
    card = db.query(CreditCard).filter(CreditCard.id == credit_card_id, CreditCard.user_id == user_id).first()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartão de crédito não encontrado.")

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")

    # 1. Cria a compra-mãe
    mother_purchase = InstallmentPurchase(
        user_id=user_id,
        credit_card_id=credit_card_id,
        category_id=category_id,
        title=title,
        description=description,
        total_amount=round(total_amount, 2),
        purchase_date=purchase_date,
        first_due_date=first_due_date,
        total_installments=total_installments
    )
    db.add(mother_purchase)
    db.flush()

    # 2. Divisão com ajuste de centavos na última parcela (RN05)
    base_installment_amount = round(total_amount / total_installments, 2)
    sum_installments = base_installment_amount * (total_installments - 1)
    last_installment_amount = round(total_amount - sum_installments, 2)

    today = datetime.date.today()

    # 3. Gerar cada transação de parcela (RN06)
    for i in range(1, total_installments + 1):
        amount = last_installment_amount if i == total_installments else base_installment_amount
        
        # Incrementa mensalmente a partir de first_due_date
        # Para evitar problemas com meses de tamanhos diferentes, usamos relativedelta ou cálculo de dia
        installment_date = first_due_date + relativedelta(months=(i - 1))
        
        # RN03: Transação com data futura entra como Pendente; passada/atual pode ser paga
        initial_status = "PENDENTE"
        if installment_date < today:
            initial_status = "ATRASADA"

        installment_tx = Transaction(
            user_id=user_id,
            credit_card_id=credit_card_id,
            category_id=category_id,
            title=f"{title} (Parcela {i}/{total_installments})",
            description=f"Parcela {i} de {total_installments} referente a: {title}" + (f" - {description}" if description else ""),
            amount=amount,
            date=installment_date,
            type="DESPESA",
            status=initial_status,
            payment_method="CARTAO",
            is_installment=True,
            installment_id=mother_purchase.id,
            installment_number=i,
            total_installments=total_installments
        )
        db.add(installment_tx)

    db.commit()
    db.refresh(mother_purchase)

    log_audit(
        db=db,
        user_id=user_id,
        entity_type="INSTALLMENT_PURCHASE",
        entity_id=mother_purchase.id,
        action="CREATE",
        details={
            "title": title,
            "total_amount": total_amount,
            "total_installments": total_installments,
            "card_id": credit_card_id
        }
    )

    return mother_purchase


def delete_installment_purchase(
    db: Session,
    user_id: int,
    installment_id: int,
    delete_mode: str = "FUTURE_ONLY",  # "FUTURE_ONLY" ou "ALL"
    force_paid: bool = False
):
    """
    RN07:
    Ao excluir um parcelamento:
    - Permitir excluir somente parcelas futuras não pagas.
    - Permitir excluir o parcelamento inteiro (se existirem parcelas pagas, exige force_paid=True).
    """
    purchase = db.query(InstallmentPurchase).filter(
        InstallmentPurchase.id == installment_id,
        InstallmentPurchase.user_id == user_id
    ).first()

    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelamento não encontrado.")

    installments = db.query(Transaction).filter(
        Transaction.installment_id == installment_id,
        Transaction.user_id == user_id
    ).all()

    paid_installments = [tx for tx in installments if tx.status in ["PAGA", "RECEBIDA"]]
    pending_installments = [tx for tx in installments if tx.status in ["PENDENTE", "ATRASADA"]]

    if delete_mode == "FUTURE_ONLY":
        for tx in pending_installments:
            db.delete(tx)
        
        # Se não sobrar nenhuma parcela, deleta a compra-mãe
        remaining = db.query(Transaction).filter(
            Transaction.installment_id == installment_id,
            Transaction.user_id == user_id
        ).count()
        if remaining == 0:
            db.delete(purchase)
        
        db.commit()
        log_audit(db, user_id, "INSTALLMENT_PURCHASE", installment_id, "DELETE_FUTURE_ONLY")
        return {"message": f"{len(pending_installments)} parcelas pendentes foram excluídas."}

    elif delete_mode == "ALL":
        if paid_installments and not force_paid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Existem parcelas já pagas neste parcelamento. A exclusão completa requer confirmação explícita para não corromper o histórico financeiro."
            )
        
        for tx in installments:
            db.delete(tx)
        db.delete(purchase)
        db.commit()

        log_audit(db, user_id, "INSTALLMENT_PURCHASE", installment_id, "DELETE_ALL")
        return {"message": "Parcelamento e todas as parcelas foram excluídos com sucesso."}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Modo de exclusão inválido.")
