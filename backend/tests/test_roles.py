"""Role-based 權限測試 — require_roles 依賴工廠。"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from models.user import User, UserRole
from api.deps import require_roles
from main import app
from tests.helpers import encrypt_test_token, TestSessionFactory


# === 註冊測試用路由（僅執行一次） ===

_test_router = APIRouter(prefix="/test-roles", tags=["test"])


@_test_router.get("/student-only")
async def student_only(user: User = Depends(require_roles(UserRole.STUDENT))):
    return {"role": user.role.value}


@_test_router.get("/teacher-only")
async def teacher_only(user: User = Depends(require_roles(UserRole.TEACHER))):
    return {"role": user.role.value}


@_test_router.get("/admin-only")
async def admin_only(user: User = Depends(require_roles(UserRole.ADMIN))):
    return {"role": user.role.value}


@_test_router.get("/teacher-or-admin")
async def teacher_or_admin(
    user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
):
    return {"role": user.role.value}


app.include_router(_test_router)


# === 測試資料 ===

STUDENT_PAYLOAD = {
    "sub": "student-1",
    "email": "student@example.com",
    "name": "Student",
    "googleId": "g-student-1",
}

TEACHER_PAYLOAD = {
    "sub": "teacher-1",
    "email": "teacher@example.com",
    "name": "Teacher",
    "googleId": "g-teacher-1",
}


async def _set_user_role(email: str, role: UserRole):
    """直接更新 DB 中使用者的角色。"""
    async with TestSessionFactory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = role
        await session.commit()


# === 測試 ===

async def test_student_can_access_student_route(client: AsyncClient):
    """student 可存取 student-only 路由。"""
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.get(
        "/test-roles/student-only",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "student"


async def test_student_blocked_from_teacher_route(client: AsyncClient):
    """student 不可存取 teacher-only 路由。"""
    token = encrypt_test_token(STUDENT_PAYLOAD)
    # 先建立使用者
    await client.get("/test-roles/student-only", cookies={"authjs.session-token": token})

    resp = await client.get(
        "/test-roles/teacher-only",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "FORBIDDEN"


async def test_student_blocked_from_admin_route(client: AsyncClient):
    """student 不可存取 admin-only 路由。"""
    token = encrypt_test_token(STUDENT_PAYLOAD)
    await client.get("/test-roles/student-only", cookies={"authjs.session-token": token})

    resp = await client.get(
        "/test-roles/admin-only",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 403


async def test_teacher_can_access_teacher_or_admin(client: AsyncClient):
    """teacher 可存取 teacher-or-admin 路由。"""
    token = encrypt_test_token(TEACHER_PAYLOAD)
    # 建立使用者後升級為 teacher
    await client.get("/test-roles/student-only", cookies={"authjs.session-token": token})
    await _set_user_role("teacher@example.com", UserRole.TEACHER)

    resp = await client.get(
        "/test-roles/teacher-or-admin",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "teacher"


async def test_admin_can_access_any_role_route(client: AsyncClient):
    """admin 可存取 admin-only 和 teacher-or-admin 路由。"""
    token = encrypt_test_token(TEACHER_PAYLOAD)
    await client.get("/test-roles/student-only", cookies={"authjs.session-token": token})
    await _set_user_role("teacher@example.com", UserRole.ADMIN)

    resp1 = await client.get(
        "/test-roles/admin-only",
        cookies={"authjs.session-token": token},
    )
    assert resp1.status_code == 200

    resp2 = await client.get(
        "/test-roles/teacher-or-admin",
        cookies={"authjs.session-token": token},
    )
    assert resp2.status_code == 200
