"""Constantes de domínio.

O projeto original já tinha essas constantes em `utils/helpers.py:110-116`, mas
nenhuma rota as importava — os literais estavam repetidos inline nos handlers.
"""

API_VERSION = "1.0"

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
STATUS_FECHADOS = (STATUS_DONE, STATUS_CANCELLED)

VALID_ROLES = ("user", "admin", "manager")
DEFAULT_ROLE = "user"

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

DEFAULT_COLOR = "#000000"
DATE_FORMAT = "%Y-%m-%d"

RECENT_ACTIVITY_DAYS = 7
PERCENTAGE_DECIMALS = 2
EMAIL_REGEX = r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
