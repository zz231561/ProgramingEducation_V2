"""unlock all learning units (7-U2)

課程全解鎖決策（2026-08-06）：既有使用者的 locked unit 一律轉為 available。
順序仍以 order_index 呈現為「建議路徑」，學習引導改由 K-Graph 前置依賴 /
弱項診斷 / 補救路徑負責，不再用鎖擋人。

`locked` 值保留於 enum 與 CHECK 約束（remedial 服務仍會讀取歷史狀態，
且移除約束值需重建約束，收益不成比例）。

Revision ID: u7d8e9f0a1b2
Revises: t6c7d8e9f0a1
Create Date: 2026-08-06
"""

from alembic import op

revision = "u7d8e9f0a1b2"
down_revision = "t6c7d8e9f0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE learning_units SET status = 'available' WHERE status = 'locked'"
    )


def downgrade() -> None:
    # 不可逆：原本哪些 unit 是 locked 已無從得知（依賴當時的完成進度推算）。
    # 回退僅還原「除第一個以外皆 locked」的初始語義。
    op.execute(
        """
        UPDATE learning_units SET status = 'locked'
        WHERE status = 'available' AND order_index > 0
        """
    )
