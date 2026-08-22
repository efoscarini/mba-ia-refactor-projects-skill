"""Helpers de cálculo compartilhados entre services."""
import re

from src.config.constants import EMAIL_REGEX, PERCENTAGE_DECIMALS

_EMAIL = re.compile(EMAIL_REGEX)


def calculate_percentage(part, total):
    if not total:
        return 0
    return round((part / total) * 100, PERCENTAGE_DECIMALS)


def is_valid_email(email):
    return bool(email) and _EMAIL.match(email) is not None


def sanitize_string(valor):
    return valor.strip() if isinstance(valor, str) else valor
