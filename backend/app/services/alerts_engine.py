import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Alert, Transaction, Budget, Category, User


def generate_financial_alerts(db: Session, user_id: int):
    """
    RN11, RN12 & Budget Alerts:
    Varre compromissos e orçamentos do usuário em lote (sem queries N+1) e gera notificações automáticas.
    Executa de forma segura e não bloqueante.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        today = datetime.date.today()
        alert_days = user.alert_days_before or 3

        # Pre-carrega alertas gerados hoje para este usuário em uma única query
        today_alerts = db.query(Alert).filter(
            Alert.user_id == user_id,
            func.date(Alert.created_at) == today
        ).all()
        existing_alert_keys = {(a.type, a.related_id) for a in today_alerts}

        dirty = False

        # 1. Pendências próximas do vencimento (somente despesas com due_date informado)
        target_dates = [today + datetime.timedelta(days=d) for d in [alert_days, 1]]
        upcoming_pending = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == "DESPESA",
            Transaction.status.in_(["PENDENTE", "PREVISTA"]),
            Transaction.is_adjustment == False,
            Transaction.due_date.isnot(None),
            Transaction.due_date.in_(target_dates)
        ).all()

        for tx in upcoming_pending:
            if ("VENCIMENTO_PROXIMO", tx.id) not in existing_alert_keys:
                days_diff = (tx.due_date - today).days
                title = f"Vencimento Próximo: {tx.title}"
                msg = f"O compromisso '{tx.title}' no valor de R$ {tx.amount:.2f} vence em {days_diff} dia{'s' if days_diff > 1 else ''} ({tx.due_date.strftime('%d/%m/%Y')})."
                db.add(Alert(
                    user_id=user_id,
                    type="VENCIMENTO_PROXIMO",
                    title=title,
                    message=msg,
                    related_id=tx.id
                ))
                existing_alert_keys.add(("VENCIMENTO_PROXIMO", tx.id))
                dirty = True

        # 2. Pendências vencidas e não pagas (somente se houver due_date e due_date < today)
        overdue_txs = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == "DESPESA",
            Transaction.status.in_(["PENDENTE", "PREVISTA", "ATRASADA"]),
            Transaction.is_adjustment == False,
            Transaction.due_date.isnot(None),
            Transaction.due_date < today
        ).all()

        for tx in overdue_txs:
            days_overdue = (today - tx.due_date).days
            if tx.status in ["PENDENTE", "PREVISTA"]:
                tx.status = "ATRASADA"
                dirty = True

            if days_overdue == 1 or (days_overdue % 7 == 0 and days_overdue > 0):
                if ("COMPROMISSO_VENCIDO", tx.id) not in existing_alert_keys:
                    title = f"Compromisso Atrasado: {tx.title}"
                    msg = f"O compromisso '{tx.title}' no valor de R$ {tx.amount:.2f} venceu em {tx.due_date.strftime('%d/%m/%Y')} e está em atraso há {days_overdue} dia(s)."
                    db.add(Alert(
                        user_id=user_id,
                        type="COMPROMISSO_VENCIDO",
                        title=title,
                        message=msg,
                        related_id=tx.id
                    ))
                    existing_alert_keys.add(("COMPROMISSO_VENCIDO", tx.id))
                    dirty = True

        # 3. Orçamento mensal por categoria (RF21, RF22) - Otimizado em lote
        current_month = today.month
        current_year = today.year
        budgets = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.month == current_month,
            Budget.year == current_year
        ).all()

        if budgets:
            cat_ids = [b.category_id for b in budgets]
            cats_map = {
                c.id: c.name
                for c in db.query(Category).filter(Category.id.in_(cat_ids)).all()
            }

            spent_rows = db.query(
                Transaction.category_id,
                func.sum(Transaction.amount).label("total")
            ).filter(
                Transaction.user_id == user_id,
                Transaction.category_id.in_(cat_ids),
                Transaction.type == "DESPESA",
                Transaction.status != "CANCELADA",
                Transaction.is_adjustment == False,
                Transaction.payment_method != "TRANSFERENCIA",
                func.extract('month', Transaction.date) == current_month,
                func.extract('year', Transaction.date) == current_year
            ).group_by(Transaction.category_id).all()

            spent_map = {r.category_id: float(r.total or 0.0) for r in spent_rows}

            for b in budgets:
                spent_val = spent_map.get(b.category_id, 0.0)
                cat_name = cats_map.get(b.category_id, "Categoria")

                if spent_val >= b.monthly_limit:
                    if ("ORCAMENTO_ULTRAPASSADO", b.id) not in existing_alert_keys:
                        title = f"Orçamento Ultrapassado: {cat_name}"
                        msg = f"Você ultrapassou o limite mensal estipulado para {cat_name}. Gasto: R$ {spent_val:.2f} / Limite: R$ {b.monthly_limit:.2f}."
                        db.add(Alert(user_id=user_id, type="ORCAMENTO_ULTRAPASSADO", title=title, message=msg, related_id=b.id))
                        existing_alert_keys.add(("ORCAMENTO_ULTRAPASSADO", b.id))
                        dirty = True
                elif spent_val >= (b.monthly_limit * 0.8):
                    if ("ORCAMENTO_ATINGIDO", b.id) not in existing_alert_keys:
                        title = f"Orçamento em Atenção: {cat_name}"
                        msg = f"Você atingiu {int((spent_val / b.monthly_limit) * 100)}% do orçamento de {cat_name} (R$ {spent_val:.2f} de R$ {b.monthly_limit:.2f})."
                        db.add(Alert(user_id=user_id, type="ORCAMENTO_ATINGIDO", title=title, message=msg, related_id=b.id))
                        existing_alert_keys.add(("ORCAMENTO_ATINGIDO", b.id))
                        dirty = True

        if dirty:
            db.commit()
    except Exception as e:
        print(f"Erro silencioso ao gerar alertas (RNF11 garantido): {e}")
        db.rollback()
