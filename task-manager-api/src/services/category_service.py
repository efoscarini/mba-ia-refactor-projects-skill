"""Casos de uso de Categoria."""
from src.middlewares.errors import NotFoundError
from src.models.category import Category
from src.models.task import Task


class CategoryService:
    def listar(self):
        """Contagem por categoria em 1 query agregada (antes: 1 por categoria)."""
        contagem = Task.count_by_category()
        return [
            {**categoria.to_dict(), "task_count": contagem.get(categoria.id, 0)}
            for categoria in Category.list_all()
        ]

    def criar(self, dados):
        categoria = Category()
        categoria.name = dados["name"]
        categoria.description = dados.get("description", "")
        categoria.color = dados.get("color", categoria.color)
        Category.save(categoria)
        return categoria.to_dict()

    def atualizar(self, categoria_id, dados):
        categoria = self._obter_ou_falhar(categoria_id)
        for campo, valor in dados.items():
            setattr(categoria, campo, valor)
        Category.commit()
        return categoria.to_dict()

    def deletar(self, categoria_id):
        Category.delete(self._obter_ou_falhar(categoria_id))

    def _obter_ou_falhar(self, categoria_id):
        categoria = Category.get(categoria_id)
        if categoria is None:
            raise NotFoundError("Categoria não encontrada")
        return categoria
