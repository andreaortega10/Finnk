import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Alert, Transaction, Budget, Category, User

def generate_financial_alerts(db: Session, user_id: int):
    """
    RN11, RN12 & Budget Alerts:
    Varre compromissos e orçamentos do usuário e gera notificações automáticas.
    Executa de forma segura e não bloqueante.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        today = datetime.date.today()
        alert_days = user.alert_days_before or 3

        # 1. Pendências próximas do vencimento (RN11: ex: daqui a 3 dias ou 1 dia)
        target_dates = [today + datetime.timedelta(days=d) for d in [alert_days, 1]]
        upcoming_pending = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.status == "PENDENTE",
            Transaction.date.in_(target_dates)
        ).all()

        for tx in upcoming_pending:
            days_diff = (tx.date - today).days
            title = f"Vencimento Próximo: {tx.title}"
            msg = f"O compromisso '{tx.title}' no valor de R$ {tx.amount:.2f} vence em {days_diff} dia{'s' if days_diff > 1 else ''} ({tx.date.strftime('%d/%m/%Y')})."
            
            # Evita duplicar o mesmo alerta hoje
            exists = db.query(Alert).filter(
                Alert.user_id == user_id,
                Alert.type == "VENCIMENTO_PROXIMO",
                Alert.related_id == tx.id,
                func.date(Alert.created_at) == today
            ).first()

            if not exists:
                new_alert = Alert(
                    user_id=user_id,
                    type="VENCIMENTO_PROXIMO",
                    title=title,
                    message=msg,
                    related_id=tx.id
                )
                db.add(new_alert)

        # 2. Pendências vencidas e não pagas (RN12: dia seguinte e semanalmente)
        overdue_txs = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.status.in_(["PENDENTE", "ATRASADA"]),
            Transaction.date < today
        ).all()

        for tx in overdue_txs:
            days_overdue = (today - tx.date).days
            # Atualiza status para ATRASADA se ainda estava como PENDENTE
            if tx.status == "PENDENTE":
                tx.status = "ATRASADA"

            # Notificar no dia seguinte (days_overdue == 1) ou a cada 7 dias
            if days_overdue == 1 or (days_overdue % 7 == 0 and days_overdue > 0):
                title = f"Compromisso Atrasado: {tx.title}"
                msg = f"O compromisso '{tx.title}' no valor de R$ {tx.amount:.2f} venceu em {tx.date.strftime('%d/%m/%Y')} e está em atraso há {days_overdue} dia(s)."
                
                exists = db.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.type == "COMPROMISSO_VENCIDO",
                    Alert.related_id == tx.id,
                    func.date(Alert.created_at) == today
                ).first()

                if not exists:
                    new_alert = Alert(
                        user_id=user_id,
                        type="COMPROMISSO_VENCIDO",
                        title=title,
                        message=msg,
                        related_id=tx.id
                    )
                    db.add(new_alert)

        # 3. Orçamento mensal por categoria (RF21, RF22)
        current_month = today.month
        current_year = today.year
        budgets = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.month == current_month,
            Budget.year == current_year
        ).all()

        for b in budgets:
            # Calcula total gasto na categoria no mês
            spent_query = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == b.category_id,
                Transaction.type == "DESPESA",
                func.extract('month', Transaction.date) == current_month,
                func.extract('year', Transaction.date) == current_year
            ).scalar() or 0.0

            cat = db.query(Category).filter(Category.id == b.category_id).first()
            cat_name = cat.name if cat else "Categoria"

            if spent_query >= b.monthly_limit:
                # Limite ultrapassado ou 100%
                title = f"Orçamento Ultrapassado: {cat_name}"
                msg = f"Você ultrapassou o limite mensal estipulado para {cat_name}. Gasto: R$ {spent_query:.2f} / Limite: R$ {b.monthly_limit:.2f}."
                exists = db.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.type == "ORCAMENTO_ULTRAPASSADO",
                    Alert.related_id == b.id,
                    func.date(Alert.created_at) == today
                ).first()
                if not exists:
                    db.add(Alert(user_id=user_id, type="ORCAMENTO_ULTRAPASSADO", title=title, message=msg, related_id=b.id))
            elif spent_query >= (b.monthly_limit * 0.8):
                # Limite atingindo alerta (>= 80%)
                title = f"Orçamento em Atenção: {cat_name}"
                msg = f"Você atingiu {int((spent_query / b.monthly_limit) * 100)}% do orçamento de {cat_name} (R$ {spent_query:.2f} de R$ {b.monthly_limit:.2f})."
                exists = db.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.type == "ORCAMENTO_ATINGIDO",
                    Alert.related_id == b.id,
                    func.date(Alert.created_at) == today
                ).first()
                if not exists:
                    db.add(Alert(user_id=user_id, type="ORCAMENTO_ATINGIDO", title=title, message=msg, related_id=b.id))

        db.commit()
    except Exception as e:
        print(f"Erro silencioso ao gerar alertas (RNF11 garantido): {e}")
        db.rollback()
