"""Entidade Category: mapeamento e acesso a dados."""
from src.config.constants import DEFAULT_COLOR
from src.infra.database import db
from src.utils.datetime_utils import utcnow


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": str(self.created_at),
        }

    @classmethod
    def get(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls)).scalars().all()

    @classmethod
    def count(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()

    @classmethod
    def save(cls, category):
        db.session.add(category)
        db.session.commit()
        return category

    @classmethod
    def commit(cls):
        db.session.commit()

    @classmethod
    def delete(cls, category):
        db.session.delete(category)
        db.session.commit()
