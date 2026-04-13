"""Model 定義測試 — 確認所有 model 可正確 import 且 metadata 完整。"""

from core.database import Base
from models.user import User, UserRole


def test_user_model_in_metadata():
    """User model 應已註冊在 Base.metadata 中。"""
    table_names = Base.metadata.tables.keys()
    assert "users" in table_names


def test_user_table_columns():
    """users 表應包含所有必要欄位。"""
    columns = {c.name for c in User.__table__.columns}
    expected = {"id", "email", "name", "avatar_url", "role", "google_id", "created_at", "last_login_at"}
    assert expected == columns


def test_user_role_enum():
    """UserRole enum 應有 student/teacher/admin。"""
    assert set(UserRole) == {UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN}
