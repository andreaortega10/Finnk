from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List
import datetime
from ..database import get_db
from ..models import Budget, User, Category, Transaction
from ..schemas import BudgetCreate, BudgetUpdate, BudgetOut
from ..auth import get_current_user
from ..services.audit_engine import log_audit

router = APIRouter(prefix="/api/budgets", tags=["Orçamentos"])

def format_budget_out(b: Budget, db: Session) -> BudgetOut:
    cat = db.query(Category).filter(Category.id == b.category_id).first()
    
    # Soma de despesas reais na categoria no mês/ano do orçamento
    spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == b.user_id,
        Transaction.category_id == b.category_id,
        Transaction.type == "DESPESA",
        extract('month', Transaction.date) == b.month,
        extract('year', Transaction.date) == b.year
    ).scalar() or 0.0

    remaining = max(0.0, round(b.monthly_limit - spent, 2))
    pct = round((spent / b.monthly_limit) * 100, 1) if b.monthly_limit > 0 else 0.0

    return BudgetOut(
        id=b.id,
        category_id=b.category_id,
        category_name=cat.name if cat else "Categoria",
        category_color=cat.color if cat else "#D83A6F",
        category_icon=cat.icon if cat else "Tag",
        month=b.month,
        year=b.year,
        monthly_limit=b.monthly_limit,
        spent_amount=round(spent, 2),
        remaining_amount=remaining,
        percentage_used=pct,
        is_warning=(pct >= 80.0 and pct < 100.0),
        is_exceeded=(pct >= 100.0),
        created_at=b.created_at
    )


@router.get("", response_model=List[BudgetOut])
def list_budgets(
    month: int = Query(None),
    year: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = datetime.date.today()
    sel_month = month or today.month
    sel_year = year or today.year

    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.month == sel_month,
        Budget.year == sel_year
    ).all()

    return [format_budget_out(b, db) for b in budgets]


@router.post("", response_model=BudgetOut)
def set_budget(
    data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verifica se a categoria existe
    cat = db.query(Category).filter(
        Category.id == data.category_id,
        (Category.user_id == current_user.id) | (Category.is_system_default == True)
    ).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")

    # Se já existir orçamento para categoria/mês/ano, atualiza
    existing = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.category_id == data.category_id,
        Budget.month == data.month,
        Budget.year == data.year
    ).first()

    if existing:
        existing.monthly_limit = round(data.monthly_limit, 2)
        budget = existing
    else:
        budget = Budget(
            user_id=current_user.id,
            category_id=data.category_id,
            month=data.month,
            year=data.year,
            monthly_limit=round(data.monthly_limit, 2)
        )
        db.add(budget)

    db.commit()
    db.refresh(budget)

    log_audit(db, current_user.id, "BUDGET", budget.id, "SET", {"limit": budget.monthly_limit, "cat": cat.name})
    return format_budget_out(budget, db)


@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    b = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()

    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado.")

    db.delete(b)
    db.commit()

    log_audit(db, current_user.id, "BUDGET", budget_id, "DELETE")
    return {"message": "Orçamento excluído com sucesso."}
