from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Account, User, Transaction
from ..schemas import AccountCreate, AccountUpdate, AccountOut
from ..auth import get_current_user
from ..services.financial_engine import calculate_account_balances
from ..services.audit_engine import log_audit

router = APIRouter(prefix="/api/accounts", tags=["Contas Financeiras"])

@router.get("", response_model=List[AccountOut])
def list_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    accounts = db.query(Account).filter(
        Account.user_id == current_user.id,
        Account.is_active == True
    ).all()

    result = []
    for acc in accounts:
        curr, proj = calculate_account_balances(db, acc)
        result.append(AccountOut(
            id=acc.id,
            name=acc.name,
            type=acc.type,
            color=acc.color,
            initial_balance=acc.initial_balance,
            current_balance=curr,
            projected_balance=proj,
            is_active=acc.is_active,
            created_at=acc.created_at
        ))
    return result


@router.post("", response_model=AccountOut)
def create_account(
    acc_data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = Account(
        user_id=current_user.id,
        name=acc_data.name.strip(),
        type=acc_data.type,
        color=acc_data.color or "#D83A6F",
        initial_balance=acc_data.initial_balance
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    log_audit(db, current_user.id, "ACCOUNT", account.id, "CREATE", {"name": account.name, "initial_balance": account.initial_balance})

    curr, proj = calculate_account_balances(db, account)
    return AccountOut(
        id=account.id,
        name=account.name,
        type=account.type,
        color=account.color,
        initial_balance=account.initial_balance,
        current_balance=curr,
        projected_balance=proj,
        is_active=account.is_active,
        created_at=account.created_at
    )


@router.put("/{account_id}", response_model=AccountOut)
def update_account(
    account_id: int,
    acc_data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta financeira não encontrada.")

    if acc_data.name is not None:
        account.name = acc_data.name.strip()
    if acc_data.type is not None:
        account.type = acc_data.type
    if acc_data.color is not None:
        account.color = acc_data.color
    if acc_data.initial_balance is not None:
        account.initial_balance = acc_data.initial_balance
    if acc_data.is_active is not None:
        account.is_active = acc_data.is_active

    db.commit()
    db.refresh(account)

    log_audit(db, current_user.id, "ACCOUNT", account.id, "UPDATE", {"name": account.name})

    curr, proj = calculate_account_balances(db, account)
    return AccountOut(
        id=account.id,
        name=account.name,
        type=account.type,
        color=account.color,
        initial_balance=account.initial_balance,
        current_balance=curr,
        projected_balance=proj,
        is_active=account.is_active,
        created_at=account.created_at
    )


@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta financeira não encontrada.")

    # Soft delete / inativa para preservar integridade
    account.is_active = False
    db.commit()

    log_audit(db, current_user.id, "ACCOUNT", account_id, "DELETE")
    return {"message": "Conta desativada com sucesso."}
