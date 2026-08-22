"""Entidade User: mapeamento, autenticação e acesso a dados."""
from werkzeug.security import check_password_hash, generate_password_hash

from src.config.constants import DEFAULT_ROLE
from src.infra.database import db
from src.utils.datetime_utils import utcnow


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    # --- serialização ---

    def to_dict(self):
        """`password` deliberadamente fora: não sai da camada de dados."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    # --- autenticação ---

    def set_password(self, raw_password):
        """Hash com salt (pbkdf2). O original usava MD5 sem salt."""
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        try:
            return check_password_hash(self.password, raw_password)
        except (ValueError, TypeError):
            # hash em formato legado/inválido: nega o acesso em vez de estourar
            return False

    def is_admin(self):
        return self.role == "admin"

    # --- acesso a dados ---

    @classmethod
    def get(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls)).scalars().all()

    @classmethod
    def get_by_email(cls, email):
        return db.session.execute(
            db.select(cls).filter_by(email=email)
        ).scalars().first()

    @classmethod
    def count(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()

    @classmethod
    def save(cls, user):
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def commit(cls):
        db.session.commit()

    @classmethod
    def delete(cls, user):
        db.session.delete(user)
        db.session.commit()
