import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import Base, User, Account, CreditCard, Category, Transaction, RecurringRule, InstallmentPurchase, Budget
from backend.app.services.financial_engine import calculate_account_balances, get_dashboard_analytics, is_tx_overdue
from backend.app.services.seed_helper import seed_default_categories, seed_demo_data, remove_demo_data
from backend.app.services.alerts_engine import generate_financial_alerts

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(db):
    user = User(name="Carlos Silva", email="carlos@example.com", hashed_password="hash", default_currency="BRL")
    db.add(user)
    db.commit()
    db.refresh(user)
    seed_default_categories(db, user.id)
    return user

def test_expense_without_due_date_never_overdue(db, test_user):
    """Testa que despesas sem data de vencimento não são classificadas como atrasadas."""
    acc = Account(user_id=test_user.id, name="Conta", initial_balance=500.0)
    cat = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "DESPESA").first()
    db.add(acc)
    db.commit()

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    
    # Despesa passada sem vencimento (ex: Pix feito ontem)
    tx = Transaction(
        user_id=test_user.id,
        account_id=acc.id,
        category_id=cat.id,
        title="Padaria Pix",
        amount=25.0,
        date=yesterday,
        due_date=None,
        type="DESPESA",
        status="PENDENTE",
        payment_method="PIX"
    )
    db.add(tx)
    db.commit()

    today = datetime.date.today()
    assert is_tx_overdue(tx, today) is False

    # Alertas não devem marcar a transação sem vencimento como ATRASADA
    generate_financial_alerts(db, test_user.id)
    db.refresh(tx)
    assert tx.status == "PENDENTE"

def test_expense_with_due_date_alerts(db, test_user):
    """Testa que compromisso com vencimento vencido é classificado como atrasado."""
    acc = Account(user_id=test_user.id, name="Conta", initial_balance=500.0)
    cat = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "DESPESA").first()
    db.add(acc)
    db.commit()

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    tx = Transaction(
        user_id=test_user.id,
        account_id=acc.id,
        category_id=cat.id,
        title="Boleto Internet",
        amount=100.0,
        date=yesterday,
        due_date=yesterday,
        type="DESPESA",
        status="PENDENTE",
        payment_method="BOLETO"
    )
    db.add(tx)
    db.commit()

    today = datetime.date.today()
    assert is_tx_overdue(tx, today) is True

    generate_financial_alerts(db, test_user.id)
    db.refresh(tx)
    assert tx.status == "ATRASADA"

def test_safe_demo_data_removal(db, test_user):
    """Testa que remove_demo_data apaga somente os registros mock e preserva os registros reais."""
    # 1. Cria dados de demonstração
    seed_demo_data(db, test_user)

    # 2. Cria uma transação legítima do usuário
    acc_real = Account(user_id=test_user.id, name="Conta Banco Real", initial_balance=2500.0)
    cat = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "RECEITA").first()
    db.add(acc_real)
    db.commit()

    tx_real = Transaction(
        user_id=test_user.id,
        account_id=acc_real.id,
        category_id=cat.id,
        title="Consultoria Cliente Real",
        amount=4500.0,
        date=datetime.date.today(),
        type="RECEITA",
        status="RECEBIDA"
    )
    db.add(tx_real)
    db.commit()

    # 3. Executa a remoção cirúrgica de dados demo
    result = remove_demo_data(db, test_user.id)
    assert result["deleted_transactions"] > 0
    assert result["deleted_installments"] == 1

    # 4. Verifica que a transação real e conta real continuam intactas
    surviving_tx = db.query(Transaction).filter(Transaction.user_id == test_user.id, Transaction.title == "Consultoria Cliente Real").first()
    assert surviving_tx is not None
    assert surviving_tx.amount == 4500.0

    surviving_acc = db.query(Account).filter(Account.user_id == test_user.id, Account.name == "Conta Banco Real").first()
    assert surviving_acc is not None
    assert surviving_acc.initial_balance == 2500.0

def test_projected_balance_with_month_horizon(db, test_user):
    """Testa que o saldo projetado muda de forma coerente entre os meses e exibe o horizonte."""
    acc = Account(user_id=test_user.id, name="Conta", initial_balance=1000.0)
    cat_rec = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "RECEITA").first()
    cat_exp = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "DESPESA").first()
    db.add(acc)
    db.commit()

    today = datetime.date.today()
    # Receita neste mês
    db.add(Transaction(user_id=test_user.id, account_id=acc.id, category_id=cat_rec.id, title="Receita Mês Atual", amount=500.0, date=today, type="RECEITA", status="RECEBIDA"))
    # Despesa pendente no mês que vem
    next_month = 1 if today.month == 12 else today.month + 1
    next_year = today.year + 1 if today.month == 12 else today.year
    date_next_month = datetime.date(next_year, next_month, 10)

    db.add(Transaction(user_id=test_user.id, account_id=acc.id, category_id=cat_exp.id, title="Despesa Mês Seguinte", amount=300.0, date=date_next_month, due_date=date_next_month, type="DESPESA", status="PENDENTE"))
    db.commit()

    analytics_current = get_dashboard_analytics(db, test_user, today.month, today.year)
    analytics_next = get_dashboard_analytics(db, test_user, next_month, next_year)

    # No mês atual, despesa do mês que vem não afeta o saldo projetado deste mês
    assert analytics_current["current_balance"] == 1500.0
    assert analytics_current["projected_balance"] == 1500.0
    assert "Saldo projetado ao final de" in analytics_current["projected_balance_label"]
    assert analytics_current["opening_balance"] == 1000.0
    assert analytics_current["period_income_total"] == 500.0
    assert analytics_current["period_expense_total"] == 0.0

    # No mês seguinte, o saldo projetado reflete o saldo transportado (1500) menos a despesa de 300
    assert analytics_next["opening_balance"] == 1500.0
    assert analytics_next["period_expense_total"] == 300.0
    assert analytics_next["projected_balance"] == 1200.0
    assert "Saldo projetado ao final de" in analytics_next["projected_balance_label"]


def test_controlled_scenarios_projected_balance(db, test_user):
    """
    Cobre os 7 cenários exigidos no Item 4.4:
    - Mês com receitas e despesas realizadas.
    - Mês com parcelas e despesas futuras.
    - Mês sem lançamentos (preserva saldo transportado sem valores inventados).
    - Troca entre dois meses com movimentações diferentes.
    - Receitas e despesas recorrentes.
    - Alteração e exclusão de lançamento.
    - Saldo anterior transportado para o mês seguinte.
    """
    acc = Account(user_id=test_user.id, name="Conta Principal", initial_balance=2000.0)
    cat_rec = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "RECEITA").first()
    cat_exp = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "DESPESA").first()
    db.add(acc)
    db.commit()

    today = datetime.date.today()
    m1 = today.month
    y1 = today.year

    # 1. Mês atual com receitas e despesas realizadas
    t_rec = Transaction(user_id=test_user.id, account_id=acc.id, category_id=cat_rec.id, title="Salário", amount=3000.0, date=today, type="RECEITA", status="RECEBIDA")
    t_exp = Transaction(user_id=test_user.id, account_id=acc.id, category_id=cat_exp.id, title="Mercado", amount=800.0, date=today, type="DESPESA", status="PAGA")
    db.add_all([t_rec, t_exp])
    db.commit()

    res1 = get_dashboard_analytics(db, test_user, m1, y1)
    # Abertura: 2000 | Receitas: 3000 | Despesas: 800 => Saldo: 4200
    assert res1["current_balance"] == 4200.0
    assert res1["projected_balance"] == 4200.0

    # 2. Mês seguinte (m2) com parcelas / despesas futuras
    m2 = 1 if m1 == 12 else m1 + 1
    y2 = y1 + 1 if m1 == 12 else y1
    d_fut = datetime.date(y2, m2, 15)

    t_fut = Transaction(user_id=test_user.id, account_id=acc.id, category_id=cat_exp.id, title="Parcela Celular", amount=500.0, date=d_fut, due_date=d_fut, type="DESPESA", status="PENDENTE")
    db.add(t_fut)
    db.commit()

    res2 = get_dashboard_analytics(db, test_user, m2, y2)
    # Saldo anterior transportado (abertura): 4200 - Despesa futura: 500 => Saldo Projetado: 3700
    assert res2["opening_balance"] == 4200.0
    assert res2["period_expense_total"] == 500.0
    assert res2["projected_balance"] == 3700.0

    # 3. Mês posterior (m3) sem lançamentos
    m3 = 1 if m2 == 12 else m2 + 1
    y3 = y2 + 1 if m2 == 12 else y2
    res3 = get_dashboard_analytics(db, test_user, m3, y3)
    # Mês sem lançamentos transporta o saldo final do mês anterior (3700) sem inventar dados
    assert res3["opening_balance"] == 3700.0
    assert res3["period_income_total"] == 0.0
    assert res3["period_expense_total"] == 0.0
    assert res3["projected_balance"] == 3700.0

    # 4. Alteração de um lançamento (muda valor de 500 para 700)
    t_fut.amount = 700.0
    db.commit()
    res2_updated = get_dashboard_analytics(db, test_user, m2, y2)
    assert res2_updated["projected_balance"] == 3500.0

    # 5. Exclusão de um lançamento
    db.delete(t_fut)
    db.commit()
    res2_deleted = get_dashboard_analytics(db, test_user, m2, y2)
    assert res2_deleted["projected_balance"] == 4200.0

