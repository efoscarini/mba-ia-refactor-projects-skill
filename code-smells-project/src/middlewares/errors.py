"""Exceções de domínio — traduzidas em resposta HTTP pelo error handler."""


class AppError(Exception):
    status = 500
    mensagem_padrao = "Erro interno"

    def __init__(self, mensagem=None, status=None):
        self.mensagem = mensagem or self.mensagem_padrao
        if status is not None:
            self.status = status
        super().__init__(self.mensagem)


class ValidationError(AppError):
    status = 400
    mensagem_padrao = "Dados inválidos"


class NotFoundError(AppError):
    status = 404
    mensagem_padrao = "Recurso não encontrado"


class BusinessError(AppError):
    """Regra de negócio violada (ex.: estoque insuficiente)."""
    status = 400
    mensagem_padrao = "Operação não permitida"


class UnauthorizedError(AppError):
    status = 401
    mensagem_padrao = "Credenciais inválidas"
