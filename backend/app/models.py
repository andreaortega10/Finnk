import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    default_currency = Column(String(10), default="BRL")  # BRL, USD, EUR
    alert_days_before = Column(Integer, default=3)  # Dias de antecedência padrão para alertas
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    credit_cards = relationship("CreditCard", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    installment_purchases = relationship("InstallmentPurchase", back_populates="user", cascade="all, delete-orphan")
    recurring_rules = relationship("RecurringRule", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(50), default="CORRENTE")  # CORRENTE, CARTEIRA, POUPANCA, OUTROS
    color = Column(String(30), default="#D83A6F")
    initial_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
    recurring_rules = relationship("RecurringRule", back_populates="account")


class CreditCard(Base):
    __tablename__ = "credit_cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    brand = Column(String(50), default="MASTERCARD")  # NUBANK, ELO, MASTERCARD, VISA, INTER, OUTROS
    color = Column(String(30), default="#D83A6F")
    last_four_digits = Column(String(4), default="0000")
    limit_total = Column(Float, default=0.0)
    closing_day = Column(Integer, default=5)
    due_day = Column(Integer, default=12)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="credit_cards")
    transactions = relationship("Transaction", back_populates="credit_card")
    installment_purchases = relationship("InstallmentPurchase", back_populates="credit_card")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null se padrão global do sistema
    name = Column(String(100), nullable=False)
    icon = Column(String(50), default="Tag")
    color = Column(String(30), default="#D83A6F")
    type = Column(String(20), default="DESPESA")  # DESPESA, RECEITA
    is_system_default = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="categories")
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")


class InstallmentPurchase(Base):
    """Compra-mãe parcelada"""
    __tablename__ = "installment_purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credit_card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    total_amount = Column(Float, nullable=False)
    purchase_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    first_due_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    total_installments = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="installment_purchases")
    credit_card = relationship("CreditCard", back_populates="installment_purchases")
    category = relationship("Category")
    installments = relationship("Transaction", back_populates="installment_purchase", cascade="all, delete-orphan")


class RecurringRule(Base):
    """Regra de despesa ou receita recorrente"""
    __tablename__ = "recurring_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    type = Column(String(20), default="DESPESA")  # DESPESA, RECEITA
    frequency = Column(String(30), default="MENSAL")  # MENSAL, SEMANAL, ANUAL
    due_day = Column(Integer, nullable=True)
    alert_day = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="recurring_rules")
    account = relationship("Account", back_populates="recurring_rules")
    category = relationship("Category")
    transactions = relationship("Transaction", back_populates="recurring_rule")


class Transaction(Base):
    """Transação individual (receita, despesa, compromisso ou parcela)"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    credit_card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    type = Column(String(20), nullable=False)  # RECEITA, DESPESA
    status = Column(String(20), default="PENDENTE")  # PAGA, RECEBIDA, PENDENTE, ATRASADA
    payment_method = Column(String(50), default="OUTRO")  # PIX, CARTAO, DINHEIRO, BOLETO, OUTRO
    
    # Informações de parcelamento
    is_installment = Column(Boolean, default=False)
    installment_id = Column(Integer, ForeignKey("installment_purchases.id"), nullable=True)
    installment_number = Column(Integer, nullable=True)
    total_installments = Column(Integer, nullable=True)

    # Informações de recorrência
    is_recurring = Column(Boolean, default=False)
    recurring_id = Column(Integer, ForeignKey("recurring_rules.id"), nullable=True)

    # Lançamento corretivo/estorno
    is_adjustment = Column(Boolean, default=False)
    original_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    credit_card = relationship("CreditCard", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    installment_purchase = relationship("InstallmentPurchase", back_populates="installments")
    recurring_rule = relationship("RecurringRule", back_populates="transactions")


class Budget(Base):
    """Orçamento mensal por categoria"""
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    month = Column(Integer, nullable=False)  # 1 a 12
    year = Column(Integer, nullable=False)
    monthly_limit = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")


class Alert(Base):
    """Central de Alertas e Notificações"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # VENCIMENTO_PROXIMO, COMPROMISSO_VENCIDO, ORCAMENTO_ATINGIDO, ORCAMENTO_ULTRAPASSADO, SISTEMA
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    related_id = Column(Integer, nullable=True)  # ID da transação ou orçamento associado
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alerts")


class AuditLog(Base):
    """Registro de Auditoria para operações financeiras (RNF10 / LGPD)"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entity_type = Column(String(50), nullable=False)  # TRANSACTION, INSTALLMENT, RECURRING, ACCOUNT, CARD
    entity_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE, STATUS_CHANGE
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

