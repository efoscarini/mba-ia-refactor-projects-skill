"""Entidade Task: mapeamento, invariantes e acesso a dados."""
from src.config.constants import (
    MAX_PRIORITY,
    MIN_PRIORITY,
    STATUS_FECHADOS,
    STATUS_PENDING,
    VALID_STATUSES,
)
from src.infra.database import db
from src.utils.datetime_utils import format_date, utcnow


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="tasks")
    category = db.relationship("Category", backref="tasks")

    # --- serialização ---

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "due_date": format_date(self.due_date),
            "tags": self.tags.split(",") if self.tags else [],
        }

    # --- invariantes da entidade ---

    def is_overdue(self):
        """Regra única de atraso. Antes estava reescrita em 6 lugares."""
        if not self.due_date:
            return False
        return self.due_date < utcnow() and self.status not in STATUS_FECHADOS

    @staticmethod
    def status_valido(status):
        return status in VALID_STATUSES

    @staticmethod
    def prioridade_valida(prioridade):
        return isinstance(prioridade, int) and MIN_PRIORITY <= prioridade <= MAX_PRIORITY

    # --- acesso a dados (API 2.0 do SQLAlchemy) ---

    @classmethod
    def get(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls)).scalars().all()

    @classmethod
    def list_by_user(cls, user_id):
        return db.session.execute(
            db.select(cls).filter_by(user_id=user_id)
        ).scalars().all()

    @classmethod
    def search(cls, termo=None, status=None, priority=None, user_id=None):
        consulta = db.select(cls)
        if termo:
            padrao = f"%{termo}%"
            consulta = consulta.filter(
                db.or_(cls.title.like(padrao), cls.description.like(padrao))
            )
        if status:
            consulta = consulta.filter(cls.status == status)
        if priority is not None:
            consulta = consulta.filter(cls.priority == priority)
        if user_id is not None:
            consulta = consulta.filter(cls.user_id == user_id)
        return db.session.execute(consulta).scalars().all()

    @classmethod
    def count(cls, **filtros):
        consulta = db.select(db.func.count(cls.id))
        if filtros:
            consulta = consulta.filter_by(**filtros)
        return db.session.execute(consulta).scalar_one()

    @classmethod
    def count_by(cls, coluna):
        """Uma query agregada em vez de um COUNT por valor possível."""
        linhas = db.session.execute(
            db.select(coluna, db.func.count(cls.id)).group_by(coluna)
        ).all()
        return {chave: total for chave, total in linhas}

    @classmethod
    def count_created_since(cls, momento):
        return db.session.execute(
            db.select(db.func.count(cls.id)).filter(cls.created_at >= momento)
        ).scalar_one()

    @classmethod
    def count_done_since(cls, momento):
        from src.config.constants import STATUS_DONE
        return db.session.execute(
            db.select(db.func.count(cls.id)).filter(
                cls.status == STATUS_DONE, cls.updated_at >= momento
            )
        ).scalar_one()

    @classmethod
    def count_by_category(cls):
        linhas = db.session.execute(
            db.select(cls.category_id, db.func.count(cls.id)).group_by(cls.category_id)
        ).all()
        return {categoria: total for categoria, total in linhas}

    # --- escrita ---

    @classmethod
    def save(cls, task):
        db.session.add(task)
        db.session.commit()
        return task

    @classmethod
    def commit(cls):
        db.session.commit()

    @classmethod
    def delete(cls, task):
        db.session.delete(task)
        db.session.commit()
