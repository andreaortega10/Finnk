from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Category, User, Transaction
from ..schemas import CategoryCreate, CategoryUpdate, CategoryOut
from ..auth import get_current_user
from ..services.audit_engine import log_audit

router = APIRouter(prefix="/api/categories", tags=["Categorias"])

@router.get("", response_model=List[CategoryOut])
def list_categories(
    type: Optional[str] = Query(None),
    include_hidden: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Category).filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
        Category.parent_id.is_(None)
    )

    if type:
        query = query.filter(Category.type == type.upper())
    if not include_hidden:
        query = query.filter(Category.is_hidden == False)

    return query.order_by(Category.name.asc()).all()


@router.post("", response_model=CategoryOut)
def create_category(
    cat_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = Category(
        user_id=current_user.id,
        name=cat_data.name.strip(),
        icon=cat_data.icon or "Tag",
        color=cat_data.color or "#D83A6F",
        type=cat_data.type.upper(),
        parent_id=cat_data.parent_id,
        is_system_default=False,
        is_hidden=False
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    log_audit(db, current_user.id, "CATEGORY", category.id, "CREATE", {"name": category.name})
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    cat_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        (Category.user_id == current_user.id) | (Category.is_system_default == True)
    ).first()

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")

    # Se for padrão do sistema, só permite ocultar/desocultar
    if category.is_system_default:
        if cat_data.is_hidden is not None:
            category.is_hidden = cat_data.is_hidden
    else:
        if cat_data.name is not None:
            category.name = cat_data.name.strip()
        if cat_data.icon is not None:
            category.icon = cat_data.icon
        if cat_data.color is not None:
            category.color = cat_data.color
        if cat_data.is_hidden is not None:
            category.is_hidden = cat_data.is_hidden

    db.commit()
    db.refresh(category)
    log_audit(db, current_user.id, "CATEGORY", category.id, "UPDATE", {"name": category.name})
    return category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RN13:
    Categorias padrões do sistema não podem ser excluídas, apenas ocultadas;
    categorias personalizadas só podem ser excluídas se não houver transações vinculadas.
    """
    category = db.query(Category).filter(
        Category.id == category_id,
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).first()

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")

    if category.is_system_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Categorias padrão do sistema não podem ser excluídas. Você pode ocultá-la nas configurações."
        )

    # Verifica se há transações vinculadas
    linked_tx_count = db.query(Transaction).filter(
        Transaction.category_id == category_id,
        Transaction.user_id == current_user.id
    ).count()

    if linked_tx_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não é possível excluir esta categoria pois existem {linked_tx_count} transação(ões) vinculada(s) a ela."
        )

    db.delete(category)
    db.commit()

    log_audit(db, current_user.id, "CATEGORY", category_id, "DELETE")
    return {"message": "Categoria excluída com sucesso."}
