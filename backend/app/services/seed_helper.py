from sqlalchemy.orm import Session
from ..models import Category, User, Account, CreditCard, Transaction, InstallmentPurchase, RecurringRule, Budget
import datetime

DEFAULT_CATEGORIES = [
    # Despesas
    {"name": "Moradia", "icon": "Home", "color": "#E04D74", "type": "DESPESA"},
    {"name": "Alimentação", "icon": "Utensils", "color": "#F97316", "type": "DESPESA"},
    {"name": "Transporte", "icon": "Car", "color": "#3B82F6", "type": "DESPESA"},
    {"name": "Lazer", "icon": "Gamepad2", "color": "#8B5CF6", "type": "DESPESA"},
    {"name": "Contas", "icon": "Receipt", "color": "#EC4899", "type": "DESPESA"},
    {"name": "Saúde", "icon": "HeartPulse", "color": "#10B981", "type": "DESPESA"},
    {"name": "Educação", "icon": "GraduationCap", "color": "#6366F1", "type": "DESPESA"},
    {"name": "Outros", "icon": "MoreHorizontal", "color": "#9CA3AF", "type": "DESPESA"},
    # Receitas
    {"name": "Salário", "icon": "Briefcase", "color": "#10B981", "type": "RECEITA"},
    {"name": "Prestação de Serviços", "icon": "Wrench", "color": "#06B6D4", "type": "RECEITA"},
    {"name": "Vendas", "icon": "ShoppingBag", "color": "#F59E0B", "type": "RECEITA"},
    {"name": "Outras Receitas", "icon": "PlusCircle", "color": "#6B7280", "type": "RECEITA"},
]

def seed_default_categories(db: Session, user_id: int):
    """Cria categorias padrões do sistema para o novo usuário."""
    for cat in DEFAULT_CATEGORIES:
        exists = db.query(Category).filter(
            Category.user_id == user_id,
            Category.name == cat["name"],
            Category.type == cat["type"]
        ).first()
        if not exists:
            new_cat = Category(
                user_id=user_id,
                name=cat["name"],
                icon=cat["icon"],
                color=cat["color"],
                type=cat["type"],
                is_system_default=True,
                is_hidden=False
            )
            db.add(new_cat)
    db.commit()


def seed_demo_data(db: Session, user: User):
    """Popula dados demonstrativos realistas e consistentes com o protótipo da Mariana."""
    seed_default_categories(db, user.id)

    # Verifica se já existe a conta corrente para evitar duplicação
    existing_acc = db.query(Account).filter(Account.user_id == user.id, Account.name == "Conta Corrente").first()
    if existing_acc:
        return

    # 1. Contas
    acc_corrente = Account(user_id=user.id, name="Conta Corrente", type="CORRENTE", color="#3B82F6", initial_balance=1500.00)
    acc_carteira = Account(user_id=user.id, name="Carteira", type="CARTEIRA", color="#10B981", initial_balance=250.00)
    db.add_all([acc_corrente, acc_carteira])
    db.flush()

    # 2. Cartões
    card_nubank = CreditCard(user_id=user.id, name="Nubank", brand="NUBANK", color="#820AD1", last_four_digits="4582", limit_total=4000.0, closing_day=5, due_day=12)
    card_elo = CreditCard(user_id=user.id, name="Elo", brand="ELO", color="#1E293B", last_four_digits="7391", limit_total=2500.0, closing_day=10, due_day=18)
    db.add_all([card_nubank, card_elo])
    db.flush()

    # Categorias do usuário
    cat_moradia = db.query(Category).filter(Category.user_id == user.id, Category.name == "Moradia").first()
    cat_alimentacao = db.query(Category).filter(Category.user_id == user.id, Category.name == "Alimentação").first()
    cat_transporte = db.query(Category).filter(Category.user_id == user.id, Category.name == "Transporte").first()
    cat_lazer = db.query(Category).filter(Category.user_id == user.id, Category.name == "Lazer").first()
    cat_contas = db.query(Category).filter(Category.user_id == user.id, Category.name == "Contas").first()
    cat_salario = db.query(Category).filter(Category.user_id == user.id, Category.name == "Salário").first()
    cat_outros = db.query(Category).filter(Category.user_id == user.id, Category.name == "Outros").first()

    today = datetime.date.today()
    this_month = today.month
    this_year = today.year

    # 3. Transações de Receita
    tx_salario = Transaction(
        user_id=user.id,
        account_id=acc_corrente.id,
        category_id=cat_salario.id,
        title="Salário Mensal",
        description="Pagamento salário empresa",
        amount=3000.00,
        date=today.replace(day=2),
        type="RECEITA",
        status="RECEBIDA",
        payment_method="PIX"
    )
    db.add(tx_salario)

    # 4. Transações de Despesa / Compromissos (Exatamente como o protótipo da Mariana)
    # Aluguel (Pago)
    tx_aluguel = Transaction(
        user_id=user.id,
        account_id=acc_corrente.id,
        category_id=cat_moradia.id,
        title="Aluguel",
        description="Aluguel do apartamento",
        amount=1000.00,
        date=today.replace(day=12),
        type="DESPESA",
        status="PAGA",
        payment_method="PIX"
    )
    # Internet (Pendente)
    tx_internet = Transaction(
        user_id=user.id,
        account_id=acc_corrente.id,
        category_id=cat_contas.id,
        title="Internet",
        description="Internet residencial - Claro",
        amount=120.00,
        date=today.replace(day=10),
        type="DESPESA",
        status="PENDENTE",
        payment_method="BOLETO"
    )
    # Netflix (Pendente)
    tx_netflix = Transaction(
        user_id=user.id,
        credit_card_id=card_nubank.id,
        category_id=cat_lazer.id,
        title="Netflix",
        description="Assinatura mensal streaming",
        amount=40.00,
        date=today.replace(day=15),
        type="DESPESA",
        status="PENDENTE",
        payment_method="CARTAO"
    )
    # Mercado (Pago no cartão)
    tx_mercado = Transaction(
        user_id=user.id,
        credit_card_id=card_nubank.id,
        category_id=cat_alimentacao.id,
        title="Mercado",
        description="Compras de mantimentos do mês",
        amount=245.60,
        date=today.replace(day=5),
        type="DESPESA",
        status="PAGA",
        payment_method="CARTAO"
    )
    # Restaurante (Pago no cartão Elo)
    tx_restaurante = Transaction(
        user_id=user.id,
        credit_card_id=card_elo.id,
        category_id=cat_alimentacao.id,
        title="Restaurante",
        description="Jantar final de semana",
        amount=120.00,
        date=today.replace(day=1),
        type="DESPESA",
        status="PAGA",
        payment_method="CARTAO"
    )
    # Fatura Cartão Nubank (Pendente)
    tx_fatura = Transaction(
        user_id=user.id,
        account_id=acc_corrente.id,
        credit_card_id=card_nubank.id,
        category_id=cat_contas.id,
        title="Fatura Cartão Nubank",
        description="Pagamento fatura fechada",
        amount=580.00,
        date=today.replace(day=18),
        type="DESPESA",
        status="PENDENTE",
        payment_method="BOLETO"
    )
    # Conta de Luz Atrasada (Atrasada)
    tx_luz = Transaction(
        user_id=user.id,
        account_id=acc_corrente.id,
        category_id=cat_contas.id,
        title="Conta de Luz",
        description="Enel Energia Elétrica",
        amount=240.00,
        date=today - datetime.timedelta(days=3),
        type="DESPESA",
        status="ATRASADA",
        payment_method="BOLETO"
    )
    db.add_all([tx_aluguel, tx_internet, tx_netflix, tx_mercado, tx_restaurante, tx_fatura, tx_luz])

    # 5. Compra Parcelada (Ex: Notebook ou Celular em 6x)
    from .installments_engine import create_installment_purchase
    db.commit()
    
    create_installment_purchase(
        db=db,
        user_id=user.id,
        title="Smartphone Galaxy",
        total_amount=1200.00,
        purchase_date=today - datetime.timedelta(days=15),
        first_due_date=today.replace(day=12),
        total_installments=6,
        credit_card_id=card_nubank.id,
        category_id=cat_lazer.id,
        description="Compra parcelada no Nubank"
    )

    # 6. Recorrências
    rec_aluguel = RecurringRule(
        user_id=user.id,
        account_id=acc_corrente.id,
        category_id=cat_moradia.id,
        title="Aluguel",
        amount=1000.00,
        type="DESPESA",
        frequency="MENSAL",
        due_day=12,
        start_date=today.replace(day=1),
        is_active=True
    )
    rec_salario = RecurringRule(
        user_id=user.id,
        account_id=acc_corrente.id,
        category_id=cat_salario.id,
        title="Salário Empresa",
        amount=3000.00,
        type="RECEITA",
        frequency="MENSAL",
        due_day=2,
        start_date=today.replace(day=1),
        is_active=True
    )
    db.add_all([rec_aluguel, rec_salario])

    # 7. Orçamentos do Mês
    b_alimentacao = Budget(user_id=user.id, category_id=cat_alimentacao.id, month=this_month, year=this_year, monthly_limit=600.00)
    b_lazer = Budget(user_id=user.id, category_id=cat_lazer.id, month=this_month, year=this_year, monthly_limit=400.00)
    b_moradia = Budget(user_id=user.id, category_id=cat_moradia.id, month=this_month, year=this_year, monthly_limit=1200.00)
    db.add_all([b_alimentacao, b_lazer, b_moradia])

    db.commit()
