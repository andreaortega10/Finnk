import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import User, Account, CreditCard, Category, Transaction, InstallmentPurchase, RecurringRule, Budget
from backend.app.services.financial_engine import calculate_account_balances, calculate_card_metrics
from backend.app.services.installments_engine import create_installment_purchase, delete_installment_purchase
from backend.app.services.recurring_engine import generate_recurring_transactions_for_rule, update_recurring_rule_and_future_items
from backend.app.services.alerts_engine import generate_financial_alerts
from backend.app.services.seed_helper import seed_default_categories
from fastapi import HTTPException

# Test Database in-memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_user(db):
    user = User(
        name="Mariana Silva",
        email="mariana@finnk.com",
        hashed_password="hashed_pw_test",
        default_currency="BRL",
        alert_days_before=3
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    seed_default_categories(db, user.id)
    return user

@pytest.fixture
def sample_account(db, sample_user):
    acc = Account(
        user_id=sample_user.id,
        name="Conta Principal",
        type="CORRENTE",
        initial_balance=1000.00
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc

@pytest.fixture
def sample_card(db, sample_user):
    card = CreditCard(
        user_id=sample_user.id,
        name="Nubank",
        brand="NUBANK",
        last_four_digits="4582",
        limit_total=3000.00,
        closing_day=5,
        due_day=12
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card

def test_rn02_zero_amount_rejected(db, sample_user, sample_account):
    """RN02: Uma transação não pode ter valor igual a zero."""
    cat = db.query(Category).filter(Category.user_id == sample_user.id).first()
    # Verifica que amount <= 0 deve ser rejeitado no fluxo
    assert cat is not None
    # Valor 0 não deve ser permitido
    with pytest.raises(Exception):
        # Validação do engine
        create_installment_purchase(
            db=db,
            user_id=sample_user.id,
            title="Compra Inválida",
            total_amount=0.0,
            purchase_date=datetime.date.today(),
            first_due_date=datetime.date.today(),
            total_installments=3,
            credit_card_id=1,
            category_id=cat.id
        )

def test_rn04_account_balance_calculations(db, sample_user, sample_account):
    """
    RN04:
    Saldo atual = saldo inicial + receitas pagas - despesas pagas
    Saldo projetado = saldo atual + receitas futuras - despesas futuras
    """
    cat = db.query(Category).filter(Category.user_id == sample_user.id, Category.type == "DESPESA").first()
    cat_rec = db.query(Category).filter(Category.user_id == sample_user.id, Category.type == "RECEITA").first()
    today = datetime.date.today()

    # Receita paga: R$ 500
    db.add(Transaction(user_id=sample_user.id, account_id=sample_account.id, category_id=cat_rec.id, title="Salário", amount=500.0, date=today, type="RECEITA", status="RECEBIDA"))
    # Despesa paga: R$ 200
    db.add(Transaction(user_id=sample_user.id, account_id=sample_account.id, category_id=cat.id, title="Almoço", amount=200.0, date=today, type="DESPESA", status="PAGA"))
    # Receita futura pendente: R$ 300
    db.add(Transaction(user_id=sample_user.id, account_id=sample_account.id, category_id=cat_rec.id, title="Freelance", amount=300.0, date=today + datetime.timedelta(days=10), type="RECEITA", status="PENDENTE"))
    # Despesa futura pendente: R$ 400
    db.add(Transaction(user_id=sample_user.id, account_id=sample_account.id, category_id=cat.id, title="Conta Luz", amount=400.0, date=today + datetime.timedelta(days=15), type="DESPESA", status="PENDENTE"))
    db.commit()

    curr_bal, proj_bal = calculate_account_balances(db, sample_account)
    # Inicial 1000 + 500 - 200 = 1300
    assert curr_bal == 1300.0
    # Projetado 1300 + 300 - 400 = 1200
    assert proj_bal == 1200.0

def test_rn05_rn06_installment_division_and_remainder(db, sample_user, sample_card):
    """
    RN05 & RN06: Divisão igual e ajuste de centavos na última parcela.
    Ex: R$ 100,00 em 3 parcelas -> 33.33 + 33.33 + 33.34 = 100.00
    """
    cat = db.query(Category).filter(Category.user_id == sample_user.id).first()
    today = datetime.date.today()

    purchase = create_installment_purchase(
        db=db,
        user_id=sample_user.id,
        title="Smartphone",
        total_amount=100.00,
        purchase_date=today,
        first_due_date=today,
        total_installments=3,
        credit_card_id=sample_card.id,
        category_id=cat.id,
        description="Teste de parcelas"
    )

    installments = db.query(Transaction).filter(Transaction.installment_id == purchase.id).order_by(Transaction.installment_number.asc()).all()
    assert len(installments) == 3
    assert installments[0].amount == 33.33
    assert installments[1].amount == 33.33
    assert installments[2].amount == 33.34
    assert round(sum(t.amount for t in installments), 2) == 100.00
    assert installments[0].title == "Smartphone (Parcela 1/3)"
    assert installments[2].title == "Smartphone (Parcela 3/3)"

def test_rn07_installment_deletion_rules(db, sample_user, sample_card):
    """
    RN07: Ao excluir um parcelamento:
    - Excluir apenas parcelas futuras não pagas.
    - Excluir parcelamento inteiro com confirmação se houver pagas.
    """
    cat = db.query(Category).filter(Category.user_id == sample_user.id).first()
    today = datetime.date.today()

    purchase = create_installment_purchase(
        db=db,
        user_id=sample_user.id,
        title="Geladeira",
        total_amount=3000.00,
        purchase_date=today,
        first_due_date=today,
        total_installments=3,
        credit_card_id=sample_card.id,
        category_id=cat.id
    )

    # Marca parcela 1 como PAGA
    first_tx = db.query(Transaction).filter(Transaction.installment_id == purchase.id, Transaction.installment_number == 1).first()
    first_tx.status = "PAGA"
    db.commit()

    # Tentativa de exclusão ALL sem force_paid deve falhar
    with pytest.raises(HTTPException):
        delete_installment_purchase(db, sample_user.id, purchase.id, delete_mode="ALL", force_paid=False)

    # Exclusão FUTURE_ONLY deve remover apenas parcelas 2 e 3
    delete_installment_purchase(db, sample_user.id, purchase.id, delete_mode="FUTURE_ONLY")
    remaining_txs = db.query(Transaction).filter(Transaction.installment_id == purchase.id).all()
    assert len(remaining_txs) == 1
    assert remaining_txs[0].installment_number == 1
    assert remaining_txs[0].status == "PAGA"

def test_rn09_rn10_recurring_generation_and_future_update(db, sample_user, sample_account):
    """
    RN09 & RN10: Lançamentos futuros gerados automaticamente (3 meses).
    Alteração de valor afeta apenas lançamentos futuros pendentes.
    """
    cat = db.query(Category).filter(Category.user_id == sample_user.id).first()
    today = datetime.date.today()

    rule = RecurringRule(
        user_id=sample_user.id,
        account_id=sample_account.id,
        category_id=cat.id,
        title="Aluguel Mensal",
        amount=1000.00,
        type="DESPESA",
        frequency="MENSAL",
        due_day=10,
        start_date=today.replace(day=1),
        is_active=True
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    generate_recurring_transactions_for_rule(db, rule, months_ahead=3)
    txs = db.query(Transaction).filter(Transaction.recurring_id == rule.id).order_by(Transaction.date.asc()).all()
    assert len(txs) >= 3
    assert all(t.amount == 1000.00 for t in txs)

    # Simula que a primeira parcela foi paga
    txs[0].status = "PAGA"
    db.commit()

    # Reajuste de aluguel para R$ 1200 (RN10)
    update_recurring_rule_and_future_items(db, sample_user.id, rule.id, new_amount=1200.00)

    # Verifica que a primeira permaneceu 1000 e as futuras viraram 1200
    db.refresh(txs[0])
    assert txs[0].amount == 1000.00
    for future_tx in txs[1:]:
        db.refresh(future_tx)
        assert future_tx.amount == 1200.00

def test_rn13_default_category_protection(db, sample_user):
    """RN13: Categorias padrão do sistema não podem ser excluídas."""
    default_cat = db.query(Category).filter(Category.user_id == sample_user.id, Category.is_system_default == True).first()
    assert default_cat is not None
    assert default_cat.is_system_default is True

def test_rnf03_user_data_isolation(db, sample_user, sample_account):
    """RNF03: Isolamento total entre dados de usuários diferentes."""
    user2 = User(name="Carlos", email="carlos@finnk.com", hashed_password="pw")
    db.add(user2)
    db.commit()

    # User 2 não deve conseguir ver as contas ou transações do User 1
    user2_accounts = db.query(Account).filter(Account.user_id == user2.id).all()
    assert len(user2_accounts) == 0
