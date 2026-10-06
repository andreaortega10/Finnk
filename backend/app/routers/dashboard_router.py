from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import HomeSummary, DashboardAnalytics
from ..auth import get_current_user
from ..services.financial_engine import get_home_summary, get_dashboard_analytics

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard e Painel Inicial"])

@router.get("/home-summary", response_model=HomeSummary)
def home_summary(
    month: int = Query(None),
    year: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_home_summary(db, current_user, month, year)


@router.get("/analytics", response_model=DashboardAnalytics)
def dashboard_analytics(
    month: int = Query(None),
    year: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_dashboard_analytics(db, current_user, month, year)
