"""共用依賴注入（DB session、Redis、當前使用者等）。"""

from core.database import get_db
from core.redis import get_redis

__all__ = ["get_db", "get_redis"]
