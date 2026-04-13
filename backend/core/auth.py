"""NextAuth.js v5 JWT 解碼 + FastAPI 依賴注入。

NextAuth v5 使用 JWE (dir + A256CBC-HS512) 加密 session token。
解密金鑰由 AUTH_SECRET 經 HKDF (RFC 5869) 衍生而來。
"""

from authlib.jose import JsonWebEncryption
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from fastapi import Request
from pydantic import BaseModel

from core.config import settings
from core.errors import AppError


class TokenPayload(BaseModel):
    """NextAuth JWT 解密後的 payload。"""

    sub: str  # user id (NextAuth 內部)
    email: str
    name: str
    picture: str | None = None
    google_id: str | None = None  # 自定 callback 寫入


def _derive_encryption_key(secret: str) -> bytes:
    """從 AUTH_SECRET 衍生 JWE 解密金鑰（與 NextAuth v5 一致）。

    NextAuth v5 使用 @panva/hkdf：HKDF-SHA256 (Extract + Expand)，
    salt=""，info="NextAuth.js Generated Encryption Key"，
    輸出 64 bytes（A256CBC-HS512 需要 512 bits）。
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=64,
        salt=b"",
        info=b"NextAuth.js Generated Encryption Key",
    )
    return hkdf.derive(secret.encode())


# 模組層級快取，避免每次 request 重複衍生
_encryption_key: bytes | None = None


def _get_encryption_key() -> bytes:
    """取得或建立 JWE 解密金鑰。"""
    global _encryption_key
    if _encryption_key is None:
        if not settings.NEXTAUTH_SECRET:
            raise AppError(500, "CONFIG_ERROR", "NEXTAUTH_SECRET 未設定")
        _encryption_key = _derive_encryption_key(settings.NEXTAUTH_SECRET)
    return _encryption_key


def decode_nextauth_token(token: str) -> TokenPayload:
    """解密 NextAuth v5 JWE token，回傳 payload。"""
    try:
        jwe = JsonWebEncryption()
        data = jwe.deserialize_compact(token, _get_encryption_key())
        payload = data["payload"]
    except Exception as exc:
        raise AppError(401, "INVALID_TOKEN", "Token 無效或已過期") from exc

    # payload 是 bytes，解碼為 dict
    import json
    claims = json.loads(payload)

    return TokenPayload(
        sub=claims.get("sub", ""),
        email=claims.get("email", ""),
        name=claims.get("name", ""),
        picture=claims.get("picture"),
        google_id=claims.get("googleId"),
    )


def get_token_from_request(request: Request) -> str:
    """從 request 中提取 NextAuth session token。

    NextAuth v5 將 token 存在 cookie 中：
    - 開發環境：authjs.session-token
    - 正式環境（HTTPS）：__Secure-authjs.session-token
    """
    token = request.cookies.get("__Secure-authjs.session-token")
    if not token:
        token = request.cookies.get("authjs.session-token")
    if not token:
        raise AppError(401, "UNAUTHORIZED", "未登入，請先完成身份驗證")
    return token


def get_current_user(request: Request) -> TokenPayload:
    """FastAPI 依賴注入 — 取得當前登入使用者。

    用法：
        @router.get("/me")
        def me(user: TokenPayload = Depends(get_current_user)):
            return user
    """
    token = get_token_from_request(request)
    return decode_nextauth_token(token)
