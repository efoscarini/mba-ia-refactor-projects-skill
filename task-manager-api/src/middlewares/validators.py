"""Validação de entrada — uma função por entidade, usada por POST e PUT.

O projeto original repetia a validação entre criação e atualização em
`task_routes.py` e `user_routes.py`, e tinha um `process_task_data()` em
`utils/helpers.py` que nenhuma rota chegava a importar.
"""
from src.config.constants import (
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    VALID_ROLES,
    VALID_STATUSES,
)
from src.middlewares.errors import ValidationError
from src.utils.datetime_utils import parse_date
from src.utils.helpers import is_valid_email


def _corpo(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    return dados


def _titulo(valor, obrigatorio=True):
    if not valor and obrigatorio:
        raise ValidationError("Título é obrigatório")
    valor = valor or ""
    if len(valor) < MIN_TITLE_LENGTH:
        raise ValidationError("Título muito curto")
    if len(valor) > MAX_TITLE_LENGTH:
        raise ValidationError("Título muito longo")
    return valor


def _prioridade(valor):
    try:
        prioridade = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("Prioridade deve ser entre 1 e 5")
    if not MIN_PRIORITY <= prioridade <= MAX_PRIORITY:
        raise ValidationError("Prioridade deve ser entre 1 e 5")
    return prioridade


def _status(valor):
    if valor not in VALID_STATUSES:
        raise ValidationError("Status inválido")
    return valor


def _tags(valor):
    return ",".join(valor) if isinstance(valor, list) else valor


def validar_task(dados, parcial=False):
    """`parcial=True` para PUT: valida apenas os campos presentes."""
    dados = _corpo(dados)
    resultado = {}

    if not parcial:
        resultado["title"] = _titulo(dados.get("title"))
    elif "title" in dados:
        resultado["title"] = _titulo(dados["title"], obrigatorio=False)
    if "description" in dados:
        resultado["description"] = dados["description"]
    if "status" in dados:
        resultado["status"] = _status(dados["status"])
    if "priority" in dados:
        resultado["priority"] = _prioridade(dados["priority"])
    if "user_id" in dados:
        resultado["user_id"] = dados["user_id"]
    if "category_id" in dados:
        resultado["category_id"] = dados["category_id"]
    if "tags" in dados:
        resultado["tags"] = _tags(dados["tags"])

    if "due_date" in dados:
        if dados["due_date"]:
            data = parse_date(dados["due_date"])
            if data is None:
                mensagem = (
                    "Formato de data inválido"
                    if parcial
                    else "Formato de data inválido. Use YYYY-MM-DD"
                )
                raise ValidationError(mensagem)
            resultado["due_date"] = data
        else:
            resultado["due_date"] = None

    return resultado


def validar_usuario(dados, parcial=False):
    dados = _corpo(dados)
    resultado = {}

    if not parcial:
        if not dados.get("name"):
            raise ValidationError("Nome é obrigatório")
        if not dados.get("email"):
            raise ValidationError("Email é obrigatório")
        if not dados.get("password"):
            raise ValidationError("Senha é obrigatória")

    if "name" in dados:
        resultado["name"] = dados["name"]

    if "email" in dados:
        if not is_valid_email(dados["email"]):
            raise ValidationError("Email inválido")
        resultado["email"] = dados["email"]

    if "password" in dados:
        if len(dados["password"]) < MIN_PASSWORD_LENGTH:
            mensagem = (
                "Senha muito curta"
                if parcial
                else f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres"
            )
            raise ValidationError(mensagem)
        resultado["password"] = dados["password"]

    if "role" in dados:
        if dados["role"] not in VALID_ROLES:
            raise ValidationError("Role inválido")
        resultado["role"] = dados["role"]

    if "active" in dados:
        resultado["active"] = dados["active"]

    return resultado


def validar_login(dados):
    dados = _corpo(dados)
    email = dados.get("email")
    senha = dados.get("password")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return {"email": email, "password": senha}


def validar_categoria(dados, parcial=False):
    dados = _corpo(dados)
    resultado = {}

    if not parcial:
        if not dados.get("name"):
            raise ValidationError("Nome é obrigatório")

    for campo in ("name", "description", "color"):
        if campo in dados:
            resultado[campo] = dados[campo]

    return resultado


def filtros_de_busca(args):
    def _inteiro(chave):
        bruto = args.get(chave, "")
        if not bruto:
            return None
        try:
            return int(bruto)
        except (TypeError, ValueError):
            raise ValidationError(f"Parâmetro '{chave}' deve ser numérico")

    return {
        "termo": args.get("q", ""),
        "status": args.get("status", "") or None,
        "priority": _inteiro("priority"),
        "user_id": _inteiro("user_id"),
    }
