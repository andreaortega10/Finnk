from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import datetime
from ..database import get_db
from ..models import Budget, User, Category
from ..schemas import BudgetCreate, BudgetOut
from ..auth import get_current_user
from ..services.financial_engine import calculate_budgets_metrics
from ..services.audit_engine import log_audit

router = APIRouter(prefix="/api/budgets", tags=["Orçamentos"])


def format_budget_out(b: Budget, db: Session) -> BudgetOut:
    metrics = calculate_budgets_metrics(db, b.user_id, b.month, b.year)
    item = next((m for m in metrics if m["id"] == b.id), None)
    if item:
        return BudgetOut(**item)

    cat = db.query(Category).filter(Category.id == b.category_id).first()
    return BudgetOut(
        id=b.id,
        category_id=b.category_id,
        category_name=cat.name if cat else "Categoria",
        category_color=cat.color if cat else "#D83A6F",
        category_icon=cat.icon if cat else "Tag",
        month=b.month,
        year=b.year,
        monthly_limit=b.monthly_limit,
        spent_amount=0.0,
        remaining_amount=b.monthly_limit,
        percentage_used=0.0,
        is_warning=False,
        is_exceeded=False,
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

    items = calculate_budgets_metrics(db, current_user.id, sel_month, sel_year)
    return [BudgetOut(**item) for item in items]


@router.post("", response_model=BudgetOut)
def set_budget(
    data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cat = db.query(Category).filter(
        Category.id == data.category_id,
        (Category.user_id == current_user.id) | (Category.is_system_default == True)
    ).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")

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
