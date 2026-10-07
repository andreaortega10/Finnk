import re

with open("backend/app/schemas.py", "r", encoding="utf-8") as f:
    content = f.read()

# Update TransactionCreate
content = re.sub(
    r'date: datetime\.date\n    type: str',
    r'date: datetime.date\n    due_date: Optional[datetime.date] = None\n    type: str',
    content
)

# Update TransactionUpdate
content = re.sub(
    r'date: Optional\[datetime\.date\] = None\n    type: Optional\[str\] = None',
    r'date: Optional[datetime.date] = None\n    due_date: Optional[datetime.date] = None\n    type: Optional[str] = None',
    content
)

# Update TransactionOut
content = re.sub(
    r'date: datetime\.date\n    type: str\n    status: str',
    r'date: datetime.date\n    due_date: Optional[datetime.date] = None\n    type: str\n    status: str',
    content
)

# Update RecurringRuleCreate
content = re.sub(
    r'due_day: int = Field\(10, ge=1, le=31\)',
    r'due_day: Optional[int] = Field(None, ge=1, le=31)\n    alert_day: Optional[int] = Field(None, ge=1, le=31)',
    content
)

# Update RecurringRuleUpdate
content = re.sub(
    r'due_day: Optional\[int\] = None',
    r'due_day: Optional[int] = None\n    alert_day: Optional[int] = None',
    content
)

# Update RecurringRuleOut
content = re.sub(
    r'frequency: str\n    due_day: int',
    r'frequency: str\n    due_day: Optional[int] = None\n    alert_day: Optional[int] = None',
    content
)

with open("backend/app/schemas.py", "w", encoding="utf-8") as f:
    f.write(content)
