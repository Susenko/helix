"""
Импортируем ВСЕ SQLAlchemy модели здесь, чтобы Alembic видел metadata.

Важно: alembic/env.py должен импортировать этот модуль.
"""

from app.infra.db.models.google_oauth_token import GoogleOAuthToken  # noqa: F401
from app.infra.db.models.baseline_fields import BaselineField  # noqa: F401
from app.infra.db.models.tensions import Tension  # noqa: F401
from app.infra.db.models.tension_events import TensionEvent  # noqa: F401
