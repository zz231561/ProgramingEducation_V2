"""測試用共用工具 — DB engine、session factory、token 加密。"""

import json
import os
import tempfile

from authlib.jose import JsonWebEncryption
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.auth import DEV_COOKIE_NAME, _derive_encryption_key
from core.database import Base
import models.user  # noqa: F401 — 確保 User model 註冊至 Base.metadata

# === 測試 DB — file-based SQLite ===

_db_fd, DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)

test_engine = create_async_engine(
    f"sqlite+aiosqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)
TestSessionFactory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False,
)

# === Token 加密 ===

TEST_SECRET = "test-secret-shared"


def encrypt_test_token(
    payload: dict,
    secret: str | None = None,
    cookie_name: str = DEV_COOKIE_NAME,
) -> str:
    """模擬 Auth.js v5 加密 token（dir + A256CBC-HS512）。

    cookie_name 預設為 dev cookie；HKDF info 會帶入此值，與後端解密路徑一致。
    """
    s = secret or TEST_SECRET
    key = _derive_encryption_key(s, cookie_name)
    jwe = JsonWebEncryption()
    header = {"alg": "dir", "enc": "A256CBC-HS512"}
    token = jwe.serialize_compact(header, json.dumps(payload).encode(), key)
    return token.decode() if isinstance(token, bytes) else token
