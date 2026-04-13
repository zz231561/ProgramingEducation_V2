"""使用者 service — 首次登入自動建立 DB 記錄。"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import TokenPayload
from models.user import User


async def get_or_create_user(db: AsyncSession, token: TokenPayload) -> User:
    """依 google_id 查找使用者，不存在則自動建立。

    每次呼叫都會更新 last_login_at 和 profile 資訊（name / avatar）。
    """
    stmt = select(User).where(User.google_id == token.google_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=token.email,
            name=token.name,
            avatar_url=token.picture,
            google_id=token.google_id or token.sub,
            last_login_at=datetime.now(timezone.utc),
        )
        db.add(user)
    else:
        user.name = token.name
        user.avatar_url = token.picture
        user.last_login_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)
    return user
