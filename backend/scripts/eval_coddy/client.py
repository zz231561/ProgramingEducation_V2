"""HTTP client — mint Auth.js cookie + SSE interact + 一般 API 呼叫。"""

import json
from typing import Any

import httpx
from authlib.jose import JsonWebEncryption

from core.auth import DEV_COOKIE_NAME, _derive_encryption_key
from core.config import settings

BASE_URL = "http://localhost:8000"


def mint_cookie(email: str, name: str) -> dict[str, str]:
    """以後端同一把 NEXTAUTH_SECRET 鑄造合法 session cookie（同 tests/helpers）。"""
    payload = {
        "sub": f"eval-{email}",
        "email": email,
        "name": name,
        "googleId": f"g-eval-{email}",
    }
    key = _derive_encryption_key(settings.NEXTAUTH_SECRET, DEV_COOKIE_NAME)
    jwe = JsonWebEncryption()
    header = {"alg": "dir", "enc": "A256CBC-HS512"}
    token = jwe.serialize_compact(header, json.dumps(payload).encode(), key)
    return {DEV_COOKIE_NAME: token.decode() if isinstance(token, bytes) else token}


class PersonaClient:
    """一位模擬學生：帶 cookie 的 HTTP client + SSE interact。"""

    def __init__(self, email: str, name: str):
        self.email = email
        self.http = httpx.AsyncClient(
            base_url=BASE_URL, cookies=mint_cookie(email, name), timeout=120.0
        )
        self.session_id: str | None = None

    async def api(self, method: str, path: str, **kwargs) -> Any:
        res = await self.http.request(method, path, **kwargs)
        if res.status_code >= 400:
            return {"_status": res.status_code, "_error": res.text[:500]}
        return res.json() if res.content else {}

    async def interact(
        self,
        question: str,
        code: str = "",
        execution_result: dict | None = None,
        reflection_id: str | None = None,
    ) -> dict:
        """POST /chat/interact（SSE）→ {stages, response, debug, error}。"""
        payload = {
            "code": code,
            "question": question,
            "session_id": self.session_id,
            "execution_result": execution_result,
            "reflection_id": reflection_id,
        }
        stages: list[str] = []
        done: dict | None = None
        error: dict | None = None
        async with self.http.stream("POST", "/chat/interact", json=payload) as res:
            if res.status_code >= 400:
                body = await res.aread()
                return {"error": {"status": res.status_code, "body": body.decode()[:500]}}
            event = ""
            async for line in res.aiter_lines():
                if line.startswith("event:"):
                    event = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    data = json.loads(line.split(":", 1)[1].strip())
                    if event == "stage":
                        stages.append(data["stage"])
                    elif event == "done":
                        done = data
                    elif event == "error":
                        error = data
        if done:
            self.session_id = done["session_id"]
        return {
            "stages": stages,
            "response": (done or {}).get("assistant_message", {}).get("content"),
            "user_message_id": (done or {}).get("user_message", {}).get("id"),
            "debug": (done or {}).get("debug"),
            "error": error,
        }

    async def close(self) -> None:
        await self.http.aclose()
