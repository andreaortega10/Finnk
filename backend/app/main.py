from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import (
    auth_router,
    accounts_router,
    cards_router,
    categories_router,
    transactions_router,
    installments_router,
    recurring_router,
    budgets_router,
    alerts_router,
    dashboard_router,
    user_router
)

# Cria todas as tabelas no banco relacional
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FINNK – Organizador Financeiro API",
    description="Backend completo para gestão financeira pessoal, compromissos, cartões, parcelamentos e previsibilidade.",
    version="1.0.0"
)

# Habilita CORS para o frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os routers
app.include_router(auth_router.router)
app.include_router(accounts_router.router)
app.include_router(cards_router.router)
app.include_router(categories_router.router)
app.include_router(transactions_router.router)
app.include_router(installments_router.router)
app.include_router(recurring_router.router)
app.include_router(budgets_router.router)
app.include_router(alerts_router.router)
app.include_router(dashboard_router.router)
app.include_router(user_router.router)

@app.get("/")
def root():
    return {
        "app": "FINNK – Organizador Financeiro",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }
