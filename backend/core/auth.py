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


# Auth.js v5 cookie 名（dev / prod 兩種）
DEV_COOKIE_NAME = "authjs.session-token"
PROD_COOKIE_NAME = "__Secure-authjs.session-token"


def _derive_encryption_key(secret: str, cookie_name: str = DEV_COOKIE_NAME) -> bytes:
    """從 AUTH_SECRET 衍生 JWE 解密金鑰（與 Auth.js v5 一致）。

    Auth.js v5（@auth/core）使用 @panva/hkdf：HKDF-SHA256 (Extract + Expand)，
    salt = cookie name，
    info = `Auth.js Generated Encryption Key (<cookie_name>)`，
    輸出 64 bytes（A256CBC-HS512 需要 512 bits）。

    註：較舊的 NextAuth v4 / v5-early-beta 用固定 info `"NextAuth.js Generated Encryption Key"`，
    本函式對齊現行 v5 GA 行為，info 內含 cookie name，dev/prod 衍生的 key 不同。
    """
    info = f"Auth.js Generated Encryption Key ({cookie_name})".encode()
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=64,
        salt=cookie_name.encode(),
        info=info,
    )
    return hkdf.derive(secret.encode())


# 模組層級快取（per cookie_name），避免每次 request 重複衍生
_encryption_keys: dict[str, bytes] = {}


def _get_encryption_key(cookie_name: str) -> bytes:
    """取得或建立 JWE 解密金鑰（依 cookie_name 快取）。"""
    if cookie_name not in _encryption_keys:
        if not settings.NEXTAUTH_SECRET:
            raise AppError(500, "CONFIG_ERROR", "NEXTAUTH_SECRET 未設定")
        _encryption_keys[cookie_name] = _derive_encryption_key(
            settings.NEXTAUTH_SECRET, cookie_name
        )
    return _encryption_keys[cookie_name]


def decode_nextauth_token(token: str, cookie_name: str = DEV_COOKIE_NAME) -> TokenPayload:
    """解密 Auth.js v5 JWE token，回傳 payload。

    cookie_name 必須與簽發此 token 時使用的相同（dev/prod 不同），否則 HKDF info 不一致解密失敗。
    """
    try:
        jwe = JsonWebEncryption()
        data = jwe.deserialize_compact(token, _get_encryption_key(cookie_name))
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


def get_token_from_request(request: Request) -> tuple[str, str]:
    """從 request 中提取 Auth.js session token + 對應 cookie name。

    - 正式環境（HTTPS）：__Secure-authjs.session-token
    - 開發環境：authjs.session-token

    回傳 (token, cookie_name)，cookie_name 用於 key derivation 的 HKDF info。
    """
    token = request.cookies.get(PROD_COOKIE_NAME)
    if token:
        return token, PROD_COOKIE_NAME
    token = request.cookies.get(DEV_COOKIE_NAME)
    if token:
        return token, DEV_COOKIE_NAME
    raise AppError(401, "UNAUTHORIZED", "未登入，請先完成身份驗證")


def get_current_user(request: Request) -> TokenPayload:
    """FastAPI 依賴注入 — 取得當前登入使用者。

    用法：
        @router.get("/me")
        def me(user: TokenPayload = Depends(get_current_user)):
            return user
    """
    token, cookie_name = get_token_from_request(request)
    return decode_nextauth_token(token, cookie_name)
