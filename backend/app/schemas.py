from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
import datetime

# --- User & Auth ---
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    default_currency: Optional[str] = "BRL"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6)

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    default_currency: Optional[str] = None
    alert_days_before: Optional[int] = None

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    default_currency: str
    alert_days_before: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# --- Category ---
class CategoryBase(BaseModel):
    name: str
    icon: Optional[str] = "Tag"
    color: Optional[str] = "#D83A6F"
    type: str = "DESPESA"  # DESPESA, RECEITA
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_hidden: Optional[bool] = None

class CategoryOut(CategoryBase):
    id: int
    user_id: Optional[int] = None
    is_system_default: bool
    is_hidden: bool
    created_at: datetime.datetime
    subcategories: Optional[List["CategoryOut"]] = []

    class Config:
        from_attributes = True

CategoryOut.model_rebuild()


# --- Account ---
class AccountCreate(BaseModel):
    name: str
    type: str = "CORRENTE"  # CORRENTE, CARTEIRA, POUPANCA, OUTROS
    color: Optional[str] = "#D83A6F"
    initial_balance: float = 0.0

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    color: Optional[str] = None
    initial_balance: Optional[float] = None
    is_active: Optional[bool] = None

class AccountOut(BaseModel):
    id: int
    name: str
    type: str
    color: str
    initial_balance: float
    current_balance: float = 0.0
    projected_balance: float = 0.0
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Credit Card ---
class CreditCardCreate(BaseModel):
    name: str
    brand: str = "MASTERCARD"  # NUBANK, ELO, MASTERCARD, VISA, INTER, OUTROS
    color: Optional[str] = "#D83A6F"
    last_four_digits: str = "0000"
    limit_total: float = Field(..., gt=0)
    closing_day: int = Field(5, ge=1, le=31)
    due_day: int = Field(12, ge=1, le=31)

class CreditCardUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    last_four_digits: Optional[str] = None
    limit_total: Optional[float] = None
    closing_day: Optional[int] = None
    due_day: Optional[int] = None
    alert_day: Optional[int] = None

class CreditCardOut(BaseModel):
    id: int
    name: str
    brand: str
    color: str
    last_four_digits: str
    limit_total: float
    available_limit: float = 0.0
    current_invoice_amount: float = 0.0
    closing_day: int
    due_day: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Transaction ---
class TransactionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    amount: float = Field(..., gt=0, description="O valor não pode ser zero (RN02)")
    date: datetime.date
    due_date: Optional[datetime.date] = None
    type: str = Field("DESPESA", description="RECEITA ou DESPESA")
    category_id: int
    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    status: Optional[str] = None  # Se não enviado, calculado via RN03
    payment_method: Optional[str] = "OUTRO"

class TransactionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[datetime.date] = None
    due_date: Optional[datetime.date] = None
    type: Optional[str] = None
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    status: Optional[str] = None
    payment_method: Optional[str] = None

class TransactionStatusUpdate(BaseModel):
    status: str  # PAGA, RECEBIDA, PENDENTE, ATRASADA

class TransactionOut(BaseModel):
    id: int
    user_id: int
    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    category_id: int
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    category_icon: Optional[str] = None
    account_name: Optional[str] = None
    credit_card_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    amount: float
    date: datetime.date
    due_date: Optional[datetime.date] = None
    type: str
    status: str
    payment_method: str
    is_installment: bool
    installment_id: Optional[int] = None
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None
    is_recurring: bool
    recurring_id: Optional[int] = None
    is_adjustment: bool
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

# --- Installment Purchase ---
class InstallmentPurchaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    total_amount: float = Field(..., gt=0, description="Valor total da compra parcelada")
    purchase_date: datetime.date
    first_due_date: datetime.date
    total_installments: int = Field(..., ge=2, le=96, description="Quantidade de parcelas")
    credit_card_id: int
    category_id: int

class InstallmentDeleteOption(BaseModel):
    delete_mode: str = "FUTURE_ONLY"  # "FUTURE_ONLY" ou "ALL"
    force_paid: bool = False  # Confirmação explícita se houver parcelas pagas

class InstallmentPurchaseOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    total_amount: float
    purchase_date: datetime.date
    first_due_date: datetime.date
    total_installments: int
    credit_card_id: int
    credit_card_name: Optional[str] = None
    category_id: int
    category_name: Optional[str] = None
    paid_count: int = 0
    paid_amount: float = 0.0
    pending_count: int = 0
    pending_amount: float = 0.0
    installments: List[TransactionOut] = []
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Recurring Rule ---
class RecurringRuleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    type: str = "DESPESA"  # DESPESA, RECEITA
    frequency: str = "MENSAL"  # MENSAL, SEMANAL, ANUAL
    due_day: Optional[int] = Field(None, ge=1, le=31)
    alert_day: Optional[int] = Field(None, ge=1, le=31)
    start_date: datetime.date
    end_date: Optional[datetime.date] = None
    category_id: int
    account_id: Optional[int] = None

class RecurringRuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    due_day: Optional[int] = None
    alert_day: Optional[int] = None
    end_date: Optional[datetime.date] = None
    is_active: Optional[bool] = None

class RecurringRuleOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    amount: float
    type: str
    frequency: str
    due_day: Optional[int] = None
    alert_day: Optional[int] = None
    start_date: datetime.date
    end_date: Optional[datetime.date] = None
    is_active: bool
    category_id: int
    category_name: Optional[str] = None
    account_id: Optional[int] = None
    account_name: Optional[str] = None
    next_due_date: Optional[datetime.date] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Budget ---
class BudgetCreate(BaseModel):
    category_id: int
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2100)
    monthly_limit: float = Field(..., gt=0)

class BudgetUpdate(BaseModel):
    monthly_limit: float = Field(..., gt=0)

class BudgetOut(BaseModel):
    id: int
    category_id: int
    category_name: str
    category_color: str
    category_icon: str
    month: int
    year: int
    monthly_limit: float
    spent_amount: float = 0.0
    remaining_amount: float = 0.0
    percentage_used: float = 0.0
    is_warning: bool = False   # >= 80%
    is_exceeded: bool = False  # >= 100%
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Alert ---
class AlertOut(BaseModel):
    id: int
    type: str
    title: str
    message: str
    related_id: Optional[int] = None
    is_read: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Dashboard & Summaries ---
class HomeSummary(BaseModel):
    user_name: str
    selected_month: int
    selected_year: int
    month_name: str
    total_commitments_amount: float
    total_commitments_count: int
    paid_amount: float
    paid_count: int
    pending_amount: float
    pending_count: int
    overdue_amount: float
    overdue_count: int
    next_due_item: Optional[dict] = None
    category_expenses: List[dict] = []
    total_expenses_period: float = 0.0
    cards_summary: List[dict] = []
    upcoming_commitments: List[TransactionOut] = []
    recent_transactions: List[TransactionOut] = []
    unread_alerts_count: int = 0

class DashboardAnalytics(BaseModel):
    selected_period: str
    current_balance: float
    projected_balance: float
    total_income_received: float
    total_income_expected: float
    total_expense_paid: float
    total_expense_pending: float
    total_overdue: float
    future_commitments_total: float
    category_distribution: List[dict] = []
    monthly_evolution: List[dict] = []
    status_distribution: List[dict] = []
    accounts_balance: List[dict] = []
    cards_usage: List[dict] = []

# --- Invoice Out ---
class InvoiceOut(BaseModel):
    card_id: int
    card_name: str
    brand: str
    color: str
    last_four_digits: str
    month: int
    year: int
    closing_date: datetime.date
    due_date: datetime.date
    total_amount: float
    status: str  # ABERTA, FECHADA, PAGA
    items: List[TransactionOut] = []

# --- Audit Log Out ---
class AuditLogOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    details_json: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
