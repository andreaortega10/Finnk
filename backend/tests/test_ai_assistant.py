import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Account, CreditCard, Category, Transaction, InstallmentPurchase, AIChatMessage
from backend.app.services.seed_helper import seed_default_categories
from backend.app.auth import create_access_token

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def user_a(db):
    u = User(name="Ana Maria", email="ana@example.com", hashed_password="hash", default_currency="BRL")
    db.add(u)
    db.commit()
    db.refresh(u)
    seed_default_categories(db, u.id)
    return u

@pytest.fixture
def user_b(db):
    u = User(name="Bruno Souza", email="bruno@example.com", hashed_password="hash", default_currency="BRL")
    db.add(u)
    db.commit()
    db.refresh(u)
    seed_default_categories(db, u.id)
    return u

def get_auth_headers(user: User):
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}

def test_ai_status_endpoint(client, user_a):
    headers = get_auth_headers(user_a)
    response = client.get("/api/ai/status", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "model" in data
    assert data["free_tier"] is True

def test_ai_chat_indicators_and_history(client, db, user_a):
    headers = get_auth_headers(user_a)
    
    # 1. Popula dados financeiros para Ana
    acc = Account(user_id=user_a.id, name="Conta Corrente", initial_balance=2000.0)
    cat_rec = db.query(Category).filter(Category.user_id == user_a.id, Category.type == "RECEITA").first()
    cat_moradia = db.query(Category).filter(Category.user_id == user_a.id, Category.name == "Moradia").first()
    db.add(acc)
    db.commit()

    today = datetime.date.today()
    tx_rec = Transaction(user_id=user_a.id, account_id=acc.id, category_id=cat_rec.id, title="Salário", amount=4000.0, date=today, type="RECEITA", status="RECEBIDA")
    tx_exp = Transaction(user_id=user_a.id, account_id=acc.id, category_id=cat_moradia.id, title="Aluguel", amount=1200.0, date=today, type="DESPESA", status="PAGA")
    db.add_all([tx_rec, tx_exp])
    db.commit()

    # 2. Pergunta sobre despesas do mês
    response = client.post(
        "/api/ai/chat",
        headers=headers,
        json={"message": "Quanto gastei neste mês?", "period_month": today.month, "period_year": today.year}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "1.200,00" in data["reply"]
    assert data["period_analyzed"] is not None

    # 3. Verifica persistência no histórico de chat
    hist_resp = client.get("/api/ai/history", headers=headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 2  # 1 user + 1 assistant
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Quanto gastei neste mês?"
    assert history[1]["role"] == "assistant"

def test_ai_user_isolation(client, db, user_a, user_b):
    # Ana envia uma mensagem
    headers_a = get_auth_headers(user_a)
    client.post("/api/ai/chat", headers=headers_a, json={"message": "Mensagem confidencial da Ana"})

    # Bruno busca o histórico dele
    headers_b = get_auth_headers(user_b)
    resp_b = client.get("/api/ai/history", headers=headers_b)
    assert resp_b.status_code == 200
    history_b = resp_b.json()
    # Histórico do Bruno DEVE estar vazio e NUNCA conter dados da Ana
    assert len(history_b) == 0

def test_ai_categories_and_balance_explanation(client, db, user_a):
    headers = get_auth_headers(user_a)
    acc = Account(user_id=user_a.id, name="Banco", initial_balance=1000.0)
    cat_lazer = db.query(Category).filter(Category.user_id == user_a.id, Category.name == "Lazer").first()
    db.add(acc)
    db.commit()

    today = datetime.date.today()
    tx = Transaction(user_id=user_a.id, account_id=acc.id, category_id=cat_lazer.id, title="Cinema", amount=85.0, date=today, type="DESPESA", status="PAGA")
    db.add(tx)
    db.commit()

    # Pergunta sobre categorias
    resp_cat = client.post("/api/ai/chat", headers=headers, json={"message": "Quais categorias concentram meus gastos?"})
    assert resp_cat.status_code == 200
    assert "Lazer" in resp_cat.json()["reply"]

    # Pergunta sobre saldo projetado vs saldo atual
    resp_saldo = client.post("/api/ai/chat", headers=headers, json={"message": "Explique meu saldo projetado e meu saldo atual"})
    assert resp_saldo.status_code == 200
    reply_saldo = resp_saldo.json()["reply"]
    assert "Saldo Atual" in reply_saldo
    assert "Saldo Projetado" in reply_saldo

def test_ai_clear_history(client, user_a):
    headers = get_auth_headers(user_a)
    client.post("/api/ai/chat", headers=headers, json={"message": "Olá assistente!"})

    # Limpa histórico
    del_resp = client.delete("/api/ai/history", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] >= 2

    # Verifica que histórico agora está vazio
    hist_resp = client.get("/api/ai/history", headers=headers)
    assert len(hist_resp.json()) == 0

def test_ai_input_validation(client, user_a):
    headers = get_auth_headers(user_a)
    # Mensagem vazia
    res_empty = client.post("/api/ai/chat", headers=headers, json={"message": "   "})
    assert res_empty.status_code == 400

    # Mensagem excessivamente longa (> 1000 caracteres)
    long_msg = "A" * 1050
    res_long = client.post("/api/ai/chat", headers=headers, json={"message": long_msg})
    assert res_long.status_code == 400

def test_ai_read_only_nature(client, db, user_a):
    headers = get_auth_headers(user_a)
    acc = Account(user_id=user_a.id, name="Conta Fixa", initial_balance=500.0)
    db.add(acc)
    db.commit()

    initial_tx_count = db.query(Transaction).filter(Transaction.user_id == user_a.id).count()

    # Usuário pede para cadastrar ou alterar algo
    client.post("/api/ai/chat", headers=headers, json={"message": "Cadastre uma despesa de R$ 50 para mim"})

    # Verifica que NENHUMA transação foi criada ou modificada pela IA
    final_tx_count = db.query(Transaction).filter(Transaction.user_id == user_a.id).count()
    assert final_tx_count == initial_tx_count
    
    # Saldo da conta continua inalterado
    db.refresh(acc)
    assert acc.initial_balance == 500.0
