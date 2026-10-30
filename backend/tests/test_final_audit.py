import pytest
import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Account, Category, Transaction, RecurringRule, Budget
from backend.app.services.financial_engine import (
    calculate_account_balances,
    get_accounts_projections,
    get_home_summary,
    get_dashboard_analytics,
    calculate_budgets_metrics
)
from backend.app.services.recurring_engine import (
    generate_recurring_transactions_for_rule,
    sync_all_active_recurring_rules,
    update_recurring_rule_and_future_items
)
from backend.app.services.seed_helper import seed_default_categories

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
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


def test_scenario_a_current_and_projected_balance_by_dates(db):
    """
    Cenário A:
    Saldo R$ 2.000, salário previsto R$ 3.000 dia 5 e despesa prevista R$ 500 dia 8.
    - Saldo atual antes do dia 5 = R$ 2.000,00
    - Projeção após dia 5 (ex: dia 5 ou 6) = R$ 5.000,00
    - Projeção após dia 8 (ex: dia 8 ou fim do mês) = R$ 4.500,00
    """
    user = User(name="Teste A", email="testea@finnk.com", hashed_password="pw")
    db.add(user)
    db.commit()
    seed_default_categories(db, user.id)

    acc = Account(user_id=user.id, name="Conta Corrente", type="CORRENTE", initial_balance=2000.0)
    db.add(acc)
    db.commit()

    cat_inc = db.query(Category).filter(Category.user_id == user.id, Category.type == "RECEITA").first()
    cat_exp = db.query(Category).filter(Category.user_id == user.id, Category.type == "DESPESA").first()

    ref_date = datetime.date(2026, 11, 1)  # Antes do dia 5
    day_5 = datetime.date(2026, 11, 5)
    day_8 = datetime.date(2026, 11, 8)

    db.add(Transaction(
        user_id=user.id,
        account_id=acc.id,
        category_id=cat_inc.id,
        title="Salário Previsto",
        amount=3000.0,
        date=day_5,
        type="RECEITA",
        status="PENDENTE"
    ))
    db.add(Transaction(
        user_id=user.id,
        account_id=acc.id,
        category_id=cat_exp.id,
        title="Despesa Prevista",
        amount=500.0,
        date=day_8,
        due_date=day_8,
        type="DESPESA",
        status="PENDENTE"
    ))
    db.commit()

    # 1. Antes do dia 5 e projeção no dia 5
    curr_before_5, proj_after_5 = calculate_account_balances(
        db, acc, target_date=day_5, reference_date=ref_date
    )
    assert curr_before_5 == 2000.0
    assert proj_after_5 == 5000.0

    # 2. Projeção após o dia 8
    curr_still_2000, proj_after_8 = calculate_account_balances(
        db, acc, target_date=day_8, reference_date=ref_date
    )
    assert curr_still_2000 == 2000.0
    assert proj_after_8 == 4500.0


def test_scenario_b_account_isolation_and_transfers(db, client):
    """
    Cenário B:
    Corrente R$ 1.000, Poupança R$ 2.000 e receita prevista de R$ 500 na Corrente:
    - Corrente atual = R$ 1.000,00 | Corrente projetada = R$ 1.500,00 após recebimento
    - Poupança permanece inalterada em R$ 2.000,00 (atual e projetada)
    - Transferências reduzem origem e aumentam destino sem virar receita/despesa consolidada.
    """
    reg = client.post("/api/auth/register", json={
        "name": "Teste B",
        "email": "testeb@finnk.com",
        "password": "password123"
    }).json()
    headers = {"Authorization": f"Bearer {reg['access_token']}"}
    user_id = reg["user"]["id"]

    # Ajusta a Conta Corrente inicial para R$ 1.000,00
    accs = client.get("/api/accounts", headers=headers).json()
    corrente_id = accs[0]["id"]
    client.put(f"/api/accounts/{corrente_id}", json={"initial_balance": 1000.0}, headers=headers)

    # Cria Conta Poupança com R$ 2.000,00
    poup_resp = client.post("/api/accounts", json={
        "name": "Conta Poupança",
        "type": "POUPANCA",
        "color": "#10B981",
        "initial_balance": 2000.0
    }, headers=headers).json()
    poupanca_id = poup_resp["id"]

    # Cadastra receita prevista de R$ 500,00 vinculada à Conta Corrente
    cats_inc = client.get("/api/categories?type=RECEITA", headers=headers).json()
    today = datetime.date.today()
    future_in_month = today + datetime.timedelta(days=2)

    client.post("/api/transactions", json={
        "title": "Salário Previsto",
        "amount": 500.0,
        "date": future_in_month.isoformat(),
        "type": "RECEITA",
        "category_id": cats_inc[0]["id"],
        "account_id": corrente_id,
        "status": "PENDENTE"
    }, headers=headers)

    proj = client.get("/api/accounts/projections?horizon_days=30", headers=headers).json()
    acc_map = {a["id"]: a for a in proj["accounts"]}

    assert acc_map[corrente_id]["current_balance"] == 1000.0
    assert acc_map[corrente_id]["projected_balance"] == 1500.0
    assert acc_map[poupanca_id]["current_balance"] == 2000.0
    assert acc_map[poupanca_id]["projected_balance"] == 2000.0

    # Testa transferência de R$ 300,00 da Corrente para a Poupança
    tr_resp = client.post("/api/accounts/transfer", json={
        "origin_account_id": corrente_id,
        "destination_account_id": poupanca_id,
        "amount": 300.0,
        "date": today.isoformat(),
        "description": "Aplicação na poupança"
    }, headers=headers)
    assert tr_resp.status_code == 200
    tr_data = tr_resp.json()
    assert tr_data["origin_account"]["current_balance"] == 700.0
    assert tr_data["destination_account"]["current_balance"] == 2300.0

    # Verifica que a transferência NÃO inflou receitas ou despesas consolidadas na Análise Geral
    analytics = client.get(f"/api/dashboard/analytics?month={today.month}&year={today.year}", headers=headers).json()
    assert analytics["total_income_received"] == 0.0
    assert analytics["total_expense_paid"] == 0.0
    assert analytics["current_balance"] == 3000.0  # 700 + 2300


def test_scenario_c_recurring_rules_prediction_confirmation_and_no_duplication(db):
    """
    Cenário C:
    Recorrência respeita periodicidade, encerramento, previsão (nunca nasce como efetivada),
    confirmação sem duplicar e exclusão/cancelamento sem recriar.
    """
    user = User(name="Teste C", email="testec@finnk.com", hashed_password="pw")
    db.add(user)
    db.commit()
    seed_default_categories(db, user.id)

    acc = Account(user_id=user.id, name="Conta Principal", type="CORRENTE", initial_balance=1000.0)
    db.add(acc)
    db.commit()

    cat_inc = db.query(Category).filter(Category.user_id == user.id, Category.type == "RECEITA").first()
    today = datetime.date.today()
    start_dt = today.replace(day=1)
    end_dt = (start_dt + datetime.timedelta(days=75)).replace(day=1)  # Exatamente 3 ocorrências mensais

    rule = RecurringRule(
        user_id=user.id,
        account_id=acc.id,
        category_id=cat_inc.id,
        title="Salário Recorrente",
        amount=4000.0,
        type="RECEITA",
        frequency="MENSAL",
        due_day=5,
        start_date=start_dt,
        end_date=end_dt,
        is_active=True
    )
    db.add(rule)
    db.commit()

    generate_recurring_transactions_for_rule(db, rule)
    txs = db.query(Transaction).filter(Transaction.recurring_id == rule.id).order_by(Transaction.date.asc()).all()

    # 1. Respeita end_date (3 ocorrências) e todas nascem como PENDENTE (previsão)
    assert len(txs) == 3
    assert all(t.status == "PENDENTE" for t in txs)

    # 2. Saldo atual não foi inflado pelas previsões da recorrência!
    curr_bal, _ = calculate_account_balances(db, acc, today.month, today.year)
    assert curr_bal == 1000.0

    # 3. Confirma a primeira ocorrência (status -> RECEBIDA) e sincroniza novamente: não pode duplicar!
    txs[0].status = "RECEBIDA"
    db.commit()

    sync_all_active_recurring_rules(db, user.id)
    txs_after_sync = db.query(Transaction).filter(Transaction.recurring_id == rule.id).all()
    assert len(txs_after_sync) == 3

    # Agora que a 1ª ocorrência foi confirmada, o saldo atual passa para 1000 + 4000 = 5000
    curr_bal_after, _ = calculate_account_balances(db, acc, today.month, today.year)
    assert curr_bal_after == 5000.0

    # 4. Edição de valor da recorrência atualiza apenas as ocorrências pendentes futuras
    update_recurring_rule_and_future_items(db, user.id, rule.id, new_amount=4500.0)
    db.refresh(txs[0])
    db.refresh(txs[1])
    assert txs[0].amount == 4000.0
    assert txs[1].amount == 4500.0


def test_scenario_d_budget_calculation_and_eligibility(db):
    """
    Cenário D:
    Orçamento R$ 800,00 e despesas elegíveis R$ 600,00:
    - 75.0% utilizado e R$ 200,00 disponíveis.
    """
    user = User(name="Teste D", email="tested@finnk.com", hashed_password="pw")
    db.add(user)
    db.commit()
    seed_default_categories(db, user.id)

    acc = Account(user_id=user.id, name="Conta", initial_balance=2000.0)
    db.add(acc)
    db.commit()

    cat_alim = db.query(Category).filter(Category.user_id == user.id, Category.name.ilike("%Alimenta%")).first()
    today = datetime.date.today()

    budget = Budget(
        user_id=user.id,
        category_id=cat_alim.id,
        month=today.month,
        year=today.year,
        monthly_limit=800.0
    )
    db.add(budget)

    # Despesas elegíveis somando R$ 600,00 (400 paga + 200 pendente)
    db.add(Transaction(
        user_id=user.id, account_id=acc.id, category_id=cat_alim.id,
        title="Supermercado", amount=400.0, date=today, type="DESPESA", status="PAGA"
    ))
    db.add(Transaction(
        user_id=user.id, account_id=acc.id, category_id=cat_alim.id,
        title="Feira Mensal", amount=200.0, date=today, type="DESPESA", status="PENDENTE"
    ))
    # Uma transação CANCELADA não deve ser contabilizada
    db.add(Transaction(
        user_id=user.id, account_id=acc.id, category_id=cat_alim.id,
        title="Compra Estornada", amount=150.0, date=today, type="DESPESA", status="CANCELADA"
    ))
    db.commit()

    metrics = calculate_budgets_metrics(db, user.id, today.month, today.year)
    assert len(metrics) == 1
    b_out = metrics[0]
    assert b_out["monthly_limit"] == 800.0
    assert b_out["spent_amount"] == 600.0
    assert b_out["percentage_used"] == 75.0
    assert b_out["remaining_amount"] == 200.0
    assert b_out["is_warning"] is False
    assert b_out["is_exceeded"] is False


def test_scenario_e_and_f_cross_screen_consistency_persistence_and_isolation(client):
    """
    Cenários E & F:
    - Consistência estrita entre Início, Contas Financeiras, Transações, Análise Geral e Orçamentos.
    - Persistência após novo login e isolamento absoluto entre usuários distintos.
    """
    # Cria Usuário 1
    r1 = client.post("/api/auth/register", json={
        "name": "Usuária Consistência",
        "email": "consistencia@finnk.com",
        "password": "password123"
    }).json()
    h1 = {"Authorization": f"Bearer {r1['access_token']}"}

    accs1 = client.get("/api/accounts", headers=h1).json()
    acc1_id = accs1[0]["id"]
    client.put(f"/api/accounts/{acc1_id}", json={"initial_balance": 2000.0}, headers=h1)

    cats_inc = client.get("/api/categories?type=RECEITA", headers=h1).json()
    cats_exp = client.get("/api/categories?type=DESPESA", headers=h1).json()
    cat_inc_id = cats_inc[0]["id"]
    cat_exp_id = cats_exp[0]["id"]

    today = datetime.date.today()

    # Cadastra Receita Recebida (R$ 3.000), Despesa Paga (R$ 500) e Despesa Pendente no mês (R$ 300)
    client.post("/api/transactions", json={
        "title": "Salário Recebido",
        "amount": 3000.0,
        "date": today.isoformat(),
        "type": "RECEITA",
        "category_id": cat_inc_id,
        "account_id": acc1_id,
        "status": "RECEBIDA"
    }, headers=h1)

    client.post("/api/transactions", json={
        "title": "Conta Paga",
        "amount": 500.0,
        "date": today.isoformat(),
        "type": "DESPESA",
        "category_id": cat_exp_id,
        "account_id": acc1_id,
        "status": "PAGA"
    }, headers=h1)

    client.post("/api/transactions", json={
        "title": "Conta Pendente",
        "amount": 300.0,
        "date": today.isoformat(),
        "due_date": (today + datetime.timedelta(days=1)).isoformat() if today.day < 28 else today.isoformat(),
        "type": "DESPESA",
        "category_id": cat_exp_id,
        "account_id": acc1_id,
        "status": "PENDENTE"
    }, headers=h1)

    client.post("/api/budgets", json={
        "category_id": cat_exp_id,
        "month": today.month,
        "year": today.year,
        "monthly_limit": 1000.0
    }, headers=h1)

    # Novo Login (Cenário F - Persistência após novo login)
    login_res = client.post("/api/auth/login", json={
        "email": "consistencia@finnk.com",
        "password": "password123"
    }).json()
    h1_relogin = {"Authorization": f"Bearer {login_res['access_token']}"}

    # Consulta as 5 telas (Cenário E)
    home = client.get(f"/api/dashboard/home-summary?month={today.month}&year={today.year}", headers=h1_relogin).json()
    analytics = client.get(f"/api/dashboard/analytics?month={today.month}&year={today.year}", headers=h1_relogin).json()
    accounts = client.get(f"/api/accounts?month={today.month}&year={today.year}", headers=h1_relogin).json()
    txs = client.get(f"/api/transactions?month={today.month}&year={today.year}", headers=h1_relogin).json()
    budgets = client.get(f"/api/budgets?month={today.month}&year={today.year}", headers=h1_relogin).json()

    # Saldo atual esperado: 2000 + 3000 - 500 = 4500.0
    # Saldo projetado no mês: 4500 - 300 = 4200.0
    assert accounts[0]["current_balance"] == 4500.0
    assert accounts[0]["projected_balance"] == 4200.0
    assert analytics["current_balance"] == 4500.0
    assert analytics["projected_balance"] == 4200.0

    # Total de despesas do mês (500 paga + 300 pendente = 800.0) idêntico em todas as telas
    tx_expenses_sum = sum(t["amount"] for t in txs if t["type"] == "DESPESA")
    assert home["total_expenses_period"] == 800.0
    assert analytics["period_expense_total"] == 800.0
    assert tx_expenses_sum == 800.0
    assert budgets[0]["spent_amount"] == 800.0
    assert budgets[0]["percentage_used"] == 80.0
    assert budgets[0]["remaining_amount"] == 200.0

    # Cria Usuário 2 e verifica isolamento total (Cenário F)
    r2 = client.post("/api/auth/register", json={
        "name": "Usuário Isolado",
        "email": "isolado@finnk.com",
        "password": "password123"
    }).json()
    h2 = {"Authorization": f"Bearer {r2['access_token']}"}

    analytics2 = client.get(f"/api/dashboard/analytics?month={today.month}&year={today.year}", headers=h2).json()
    txs2 = client.get(f"/api/transactions?month={today.month}&year={today.year}", headers=h2).json()
    budgets2 = client.get(f"/api/budgets?month={today.month}&year={today.year}", headers=h2).json()

    assert analytics2["current_balance"] == 0.0
    assert analytics2["projected_balance"] == 0.0
    assert len(txs2) == 0
    assert len(budgets2) == 0
