from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Alert, User
from ..schemas import AlertOut
from ..auth import get_current_user
from ..services.alerts_engine import generate_financial_alerts

router = APIRouter(prefix="/api/alerts", tags=["Central de Alertas e Notificações"])

@router.get("", response_model=List[AlertOut])
def list_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Gera notificações atualizadas
    generate_financial_alerts(db, current_user.id)

    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id
    ).order_by(Alert.is_read.asc(), Alert.created_at.desc()).all()

    return alerts


@router.patch("/{alert_id}/read", response_model=AlertOut)
def mark_alert_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()

    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta não encontrado.")

    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/mark-all-read")
def mark_all_alerts_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "Todos os alertas foram marcados como lidos."}


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()

    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta não encontrado.")

    db.delete(alert)
    db.commit()
    return {"message": "Alerta excluído com sucesso."}
