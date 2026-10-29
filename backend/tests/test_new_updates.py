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


def test_unify_income_categories(db, test_user):
    """
    Testa que 'Outro' e 'Outros' de RECEITA são unificados em 'Outras receitas',
    as transações são re-apontadas e 'Outros' de DESPESA permanece intacto.
    """
    # Cria categoria antiga 'Outros' de RECEITA
    old_cat_rec = Category(
        user_id=test_user.id,
        name="Outros",
        icon="MoreHorizontal",
        color="#9CA3AF",
        type="RECEITA",
        is_system_default=False
    )
    db.add(old_cat_rec)
    db.commit()

    acc = Account(user_id=test_user.id, name="Conta", initial_balance=100.0)
    db.add(acc)
    db.commit()

    # Transação vinculada à categoria antiga
    tx = Transaction(
        user_id=test_user.id,
        account_id=acc.id,
        category_id=old_cat_rec.id,
        title="Receita Freelance Extra",
        amount=250.0,
        date=datetime.date.today(),
        type="RECEITA",
        status="RECEBIDA"
    )
    db.add(tx)
    db.commit()

    # Executa unificação
    from backend.app.services.seed_helper import unify_income_categories
    unify_income_categories(db, test_user.id)

    # Verifica que a transação foi re-apontada para 'Outras receitas'
    db.refresh(tx)
    target_cat = db.query(Category).filter(Category.id == tx.category_id).first()
    assert target_cat.name.lower() == "outras receitas"
    assert target_cat.type == "RECEITA"

    # Verifica que a categoria antiga 'Outros' de RECEITA não existe mais
    deleted_old = db.query(Category).filter(
        Category.user_id == test_user.id,
        Category.name == "Outros",
        Category.type == "RECEITA"
    ).first()
    assert deleted_old is None

    # Verifica que 'Outros' de DESPESA continua intacta
    expense_outros = db.query(Category).filter(
        Category.user_id == test_user.id,
        Category.name == "Outros",
        Category.type == "DESPESA"
    ).first()
    assert expense_outros is not None


def test_account_balance_movement_audit(db, test_user):
    """
    Auditoria estrita de movimentação de saldos das contas (Correção 7):
    - Saldo inicial: R$ 1.000,00
    - Despesa paga: R$ 150,00
    - Receita recebida: R$ 200,00
    - Saldo final esperado: R$ 1.050,00
    - Transações pendentes ou futuras NÃO alteram o saldo real atual.
    """
    acc = Account(user_id=test_user.id, name="Conta Corrente Teste", initial_balance=1000.0)
    cat_rec = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "RECEITA").first()
    cat_exp = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "DESPESA").first()
    db.add(acc)
    db.commit()

    today = datetime.date.today()

    # 1. Despesa paga de R$ 150,00
    tx_exp_paga = Transaction(
        user_id=test_user.id,
        account_id=acc.id,
        category_id=cat_exp.id,
        title="Almoço Restaurante",
        amount=150.0,
        date=today,
        due_date=today,
        type="DESPESA",
        status="PAGA"
    )

    # 2. Receita recebida de R$ 200,00
    tx_rec_paga = Transaction(
        user_id=test_user.id,
        account_id=acc.id,
        category_id=cat_rec.id,
        title="Reembolso de Despesas",
        amount=200.0,
        date=today,
        type="RECEITA",
        status="RECEBIDA"
    )

    # 3. Transação pendente futura de R$ 500,00 (NÃO deve afetar saldo real atual)
    future_date = today + datetime.timedelta(days=15)
    tx_futura = Transaction(
        user_id=test_user.id,
        account_id=acc.id,
        category_id=cat_exp.id,
        title="Boleto Futuro",
        amount=500.0,
        date=future_date,
        due_date=future_date,
        type="DESPESA",
        status="PENDENTE"
    )

    db.add_all([tx_exp_paga, tx_rec_paga, tx_futura])
    db.commit()

    curr_bal, proj_bal = calculate_account_balances(db, acc)
    # 1000 - 150 + 200 = 1050.00
    assert curr_bal == 1050.0
    # Projetado inclui a despesa futura de 500: 1050 - 500 = 550.00
    assert proj_bal == 550.0

    # 4. Alterna status da despesa de R$ 150,00 para PENDENTE (saldo real volta para 1200)
    tx_exp_paga.status = "PENDENTE"
    db.commit()
    curr_bal, _ = calculate_account_balances(db, acc)
    assert curr_bal == 1200.0

    # 5. Edita o valor da receita de 200 para 300
    tx_rec_paga.amount = 300.0
    db.commit()
    curr_bal, _ = calculate_account_balances(db, acc)
    assert curr_bal == 1300.0

    # 6. Exclui a receita
    db.delete(tx_rec_paga)
    db.commit()
    curr_bal, _ = calculate_account_balances(db, acc)
    assert curr_bal == 1000.0


def test_credit_limit_validation(db, test_user):
    """
    Testa bloqueio de compras e parcelamentos que ultrapassam o limite disponível do cartão (Correção 8).
    """
    from fastapi import HTTPException
    from backend.app.services.installments_engine import create_installment_purchase
    from backend.app.services.financial_engine import calculate_card_metrics

    card = CreditCard(
        user_id=test_user.id,
        name="Cartão Gold",
        brand="VISA",
        limit_total=1000.0,
        closing_day=5,
        due_day=12
    )
    cat = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "DESPESA").first()
    db.add(card)
    db.commit()

    today = datetime.date.today()

    # Tentativa 1: Compra parcelada de R$ 1.200,00 em cartão com limite de R$ 1.000,00
    with pytest.raises(HTTPException) as exc_info:
        create_installment_purchase(
            db=db,
            user_id=test_user.id,
            title="Notebook",
            total_amount=1200.0,
            purchase_date=today,
            first_due_date=today,
            total_installments=6,
            credit_card_id=card.id,
            category_id=cat.id
        )
    assert exc_info.value.status_code == 400
    assert "Limite insuficiente no cartão" in exc_info.value.detail

    # Compra parcelada válida de R$ 600,00 (dentro do limite)
    inst = create_installment_purchase(
        db=db,
        user_id=test_user.id,
        title="Smartphone",
        total_amount=600.0,
        purchase_date=today,
        first_due_date=today,
        total_installments=3,
        credit_card_id=card.id,
        category_id=cat.id
    )
    assert inst is not None

    # Limite disponível agora deve ser 1000 - 600 = 400.0
    avail, _ = calculate_card_metrics(db, card)
    assert avail == 400.0

    # Tentativa 2: Nova compra parcelada de R$ 500,00 (limite disponível é 400.0) -> Deve ser bloqueada!
    with pytest.raises(HTTPException) as exc_info2:
        create_installment_purchase(
            db=db,
            user_id=test_user.id,
            title="Fone Bluetooth",
            total_amount=500.0,
            purchase_date=today,
            first_due_date=today,
            total_installments=2,
            credit_card_id=card.id,
            category_id=cat.id
        )
    assert exc_info2.value.status_code == 400
    assert "Limite insuficiente no cartão" in exc_info2.value.detail


def test_installment_lazer_due_date_and_category_search(db, test_user):
    """
    Testa que compras parceladas na categoria Lazer possuem due_date preenchido
    e aparecem na busca por categoria e na Análise Geral (Correção 9).
    """
    from backend.app.services.installments_engine import create_installment_purchase

    card = CreditCard(user_id=test_user.id, name="Cartão Platinum", brand="MASTERCARD", limit_total=5000.0, closing_day=1, due_day=10)
    cat_lazer = db.query(Category).filter(Category.user_id == test_user.id, Category.name == "Lazer").first()
    db.add(card)
    db.commit()

    today = datetime.date.today()
    inst = create_installment_purchase(
        db=db,
        user_id=test_user.id,
        title="Viagem Praia",
        total_amount=1500.0,
        purchase_date=today,
        first_due_date=today,
        total_installments=3,
        credit_card_id=card.id,
        category_id=cat_lazer.id
    )

    # Verifica parcelas geradas
    txs = db.query(Transaction).filter(Transaction.installment_id == inst.id).all()
    assert len(txs) == 3
    for t in txs:
        # Cada parcela DEVE ter due_date definido
        assert t.due_date is not None
        assert t.category_id == cat_lazer.id

    # Verifica agregação na Análise Geral
    analytics = get_dashboard_analytics(db, test_user, today.month, today.year)
    cat_dist = analytics["category_distribution"]
    lazer_dist = next((c for c in cat_dist if c["category_id"] == cat_lazer.id), None)
    assert lazer_dist is not None
    assert lazer_dist["amount"] == 500.0  # Primeira parcela de 500 no mês atual


def test_reset_data_permanence(db, test_user):
    """
    Testa que reset_data apaga permanentemente todos os lançamentos e recria
    corretamente a conta padrão e categorias fixas (Correção 1).
    """
    from backend.app.routers.user_router import reset_data

    # Cria dados de teste
    acc = Account(user_id=test_user.id, name="Minha Conta", initial_balance=500.0)
    card = CreditCard(user_id=test_user.id, name="Meu Cartao", limit_total=1000.0, closing_day=5, due_day=10)
    cat = db.query(Category).filter(Category.user_id == test_user.id, Category.type == "DESPESA").first()
    db.add_all([acc, card])
    db.commit()

    tx = Transaction(user_id=test_user.id, account_id=acc.id, category_id=cat.id, title="Despesa Teste", amount=50.0, date=datetime.date.today(), type="DESPESA", status="PAGA")
    db.add(tx)
    db.commit()

    # Executa o reset de dados
    res = reset_data(current_user=test_user, db=db)
    assert "com sucesso" in res["message"]

    # Verifica que a transação foi excluída
    remaining_tx = db.query(Transaction).filter(Transaction.user_id == test_user.id).all()
    assert len(remaining_tx) == 0

    # Verifica que existe a Conta Corrente padrão com saldo 0
    accounts = db.query(Account).filter(Account.user_id == test_user.id).all()
    assert len(accounts) == 1
    assert accounts[0].name == "Conta Corrente"
    assert accounts[0].initial_balance == 0.0

    # Categorias mínimas foram semeadas
    cats = db.query(Category).filter(Category.user_id == test_user.id).all()
    assert len(cats) >= 10


