from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Transaction, Account, CreditCard, Category, Budget, Alert, AuditLog, RecurringRule, InstallmentPurchase
from ..schemas import (
    UserCreate, UserLogin, UserOut, Token, UserProfileUpdate,
    UserPasswordChange, PasswordResetRequest, PasswordResetConfirm
)
from ..auth import verify_password, get_password_hash, create_access_token, get_current_user
from ..services.seed_helper import seed_default_categories, seed_demo_data
from ..services.audit_engine import log_audit

router = APIRouter(prefix="/api/auth", tags=["Autenticação e Perfil"])

@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Verifica se email já existe
    existing = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este e-mail já está cadastrado no FINNK.")

    new_user = User(
        name=user_data.name.strip(),
        email=user_data.email.lower().strip(),
        hashed_password=get_password_hash(user_data.password),
        default_currency=user_data.default_currency or "BRL"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Cria categorias padrão
    seed_default_categories(db, new_user.id)

    # Cria conta bancária inicial padrão (ex: Conta Corrente)
    default_acc = Account(
        user_id=new_user.id,
        name="Conta Corrente",
        type="CORRENTE",
        color="#3B82F6",
        initial_balance=0.0
    )
    db.add(default_acc)
    db.commit()

    log_audit(db, new_user.id, "USER", new_user.id, "REGISTER")

    access_token = create_access_token(data={"sub": str(new_user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": new_user}


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos."
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username.lower().strip()).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas."
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/forgot-password")
def forgot_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user:
        # Por segurança, retorna mensagem genérica
        return {"message": "Se o e-mail estiver cadastrado, as instruções para redefinição foram enviadas."}
    
    # Simula envio de token/instruções para o e-mail cadastrado (RF03)
    return {
        "message": f"Instruções para redefinição de senha foram enviadas para {user.email}.",
        "demo_reset_token": "DEMO-RESET-TOKEN-1234"
    }


@router.post("/reset-password")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    
    user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    log_audit(db, user.id, "USER", user.id, "PASSWORD_RESET")
    return {"message": "Senha redefinida com sucesso! Você já pode fazer login."}


@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile_data.email and profile_data.email.lower() != current_user.email:
        exists = db.query(User).filter(User.email == profile_data.email.lower()).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este e-mail já está em uso.")
        current_user.email = profile_data.email.lower().strip()

    if profile_data.name:
        current_user.name = profile_data.name.strip()
    if profile_data.default_currency:
        current_user.default_currency = profile_data.default_currency
    if profile_data.alert_days_before is not None:
        current_user.alert_days_before = profile_data.alert_days_before

    db.commit()
    db.refresh(current_user)
    log_audit(db, current_user.id, "USER", current_user.id, "UPDATE_PROFILE")
    return current_user


@router.post("/change-password")
def change_password(
    data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A senha atual informada está incorreta.")

    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    log_audit(db, current_user.id, "USER", current_user.id, "CHANGE_PASSWORD")
    return {"message": "Senha alterada com sucesso!"}


@router.post("/seed-demo")
def seed_demo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Popula os dados demonstrativos no perfil atual (Mariana / Mockup)"""
    seed_demo_data(db, current_user)
    return {"message": "Dados de demonstração populados com sucesso!"}
