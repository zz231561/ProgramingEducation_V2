"""假學生資料 seeder（DEV-E）— 供教師端 / 行為分析本機開發用。

生成可辨識（email 後綴 @seed.dev）的假學生：profile + 班級成員 + coding_events +
chat_messages（含 dialogue_act）+ student_mastery，依三種行為原型（主動 / 被動 / 掙扎）
塑形資料，讓 5-2d 聚合與 5-3 群聚分析有可跑樣本。
"""

from services.dev_seed.seeder import (
    SEED_EMAIL_DOMAIN,
    purge_seed_students,
    seed_fake_students,
)

__all__ = [
    "SEED_EMAIL_DOMAIN",
    "purge_seed_students",
    "seed_fake_students",
]
