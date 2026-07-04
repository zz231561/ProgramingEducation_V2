"""使用者 service — 首次登入自動建立 DB 記錄。"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import TokenPayload
from models.user import User

# last_login_at 更新節流 — 每個 authenticated request 都會經過本函式，
# 不節流會造成每 request 一次 UPDATE+COMMIT 的寫入放大
_LOGIN_UPDATE_INTERVAL = timedelta(hours=1)


async def get_or_create_user(db: AsyncSession, token: TokenPayload) -> User:
    """依 google_id 查找使用者，不存在則自動建立。

    - 首次登入並發防護：兩個同時到達的 request 都查無使用者時，
      後 INSERT 的一方會撞 unique constraint → rollback 後重查取回既有記錄
    - last_login_at 節流：距上次更新超過 1 小時才寫，避免每 request 寫 DB
    """
    stmt = select(User).where(User.google_id == (token.google_id or token.sub))
    user = (await db.execute(stmt)).scalar_one_or_none()

    if user is None:
        user = User(
            email=token.email,
            name=token.name,
            avatar_url=token.picture,
            google_id=token.google_id or token.sub,
            last_login_at=datetime.now(timezone.utc),
        )
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            user = (await db.execute(stmt)).scalar_one()
        await db.refresh(user)
        return user

    now = datetime.now(timezone.utc)
    last = user.last_login_at
    if last is not None and last.tzinfo is None:
        # SQLite 測試環境回傳 naive datetime — 比較前補上 UTC
        last = last.replace(tzinfo=timezone.utc)
    if last is None or now - last >= _LOGIN_UPDATE_INTERVAL:
        user.name = token.name
        user.avatar_url = token.picture
        user.last_login_at = now
        await db.commit()
        await db.refresh(user)
    return user
