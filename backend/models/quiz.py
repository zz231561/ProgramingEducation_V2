"""Question / StudentAnswer ORM Models — 對應 Module 6: 智慧出題。

Schema 對齊 alembic migration `f6a7b8c9d0e1`。
type / source 用 str 列舉而非 PG ENUM，避開 enum.value/.name 同款坑。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class QuestionType(str, enum.Enum):
    """題型。"""

    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    CODING = "coding"


class QuestionSource(str, enum.Enum):
    """題目來源。"""

    GENERATED = "generated"  # LLM 即時生成（QUIZ 弱項現生）
    BATCH = "batch"          # 6-3c 知識點批次預生成（LEARN 單元題組）
    IMPORTED = "imported"    # 教師匯入
    LEETCODE = "leetcode"    # 第三方題庫匯入


class ComprehensionType(str, enum.Enum):
    """Post-Solution Comprehension Check 驗證類型（roadmap 2-6）。"""

    EPL = "epl"  # Explain in Plain Language：用自己的話解釋
    PREDICT_OUTPUT = "predict_output"  # 預測新測資輸出
    VARIATION = "variation"  # 變體題挑戰


class Question(Base):
    """題目資料表。

    `content` JSON 形狀依 type 不同：
    - multiple_choice: {"stem": "...", "options": [...], "answer_index": int}
    - fill_blank: {"stem": "...", "blanks": [...], "answers": [...]}
    - coding: {"stem": "...", "starter_code": "...", "test_cases": [...]}
    """

    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(20))
    concept_tags: Mapped[list[str]] = mapped_column(JSON)
    bloom_level: Mapped[int] = mapped_column(SmallInteger)
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    content: Mapped[dict] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(20), default=QuestionSource.GENERATED.value)
    validated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('multiple_choice', 'fill_blank', 'coding')",
            name="ck_questions_type_enum",
        ),
        CheckConstraint(
            "source IN ('generated', 'batch', 'imported', 'leetcode')",
            name="ck_questions_source_enum",
        ),
        CheckConstraint("bloom_level BETWEEN 1 AND 6", name="ck_questions_bloom_range"),
        CheckConstraint(
            "difficulty BETWEEN 1 AND 5", name="ck_questions_difficulty_range"
        ),
        Index("ix_questions_type", "type"),
        Index("ix_questions_bloom_level", "bloom_level"),
        Index("ix_questions_difficulty", "difficulty"),
    )


class StudentAnswer(Base):
    """學生作答記錄。"""

    __tablename__ = "student_answers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
    )
    answer: Mapped[dict] = mapped_column(JSON)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    hint_level_used: Mapped[int] = mapped_column(SmallInteger, default=0)
    feedback: Mapped[str] = mapped_column(Text, default="")
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    # Post-Solution Comprehension Check（roadmap 2-6a）— 解題後選擇性驗證，預設 NULL
    comprehension_type: Mapped[str | None] = mapped_column(String(20), default=None)
    comprehension_prompt: Mapped[str | None] = mapped_column(Text, default=None)
    comprehension_answer: Mapped[str | None] = mapped_column(Text, default=None)
    comprehension_passed: Mapped[bool | None] = mapped_column(Boolean, default=None)

    __table_args__ = (
        CheckConstraint(
            "hint_level_used BETWEEN 0 AND 5", name="ck_student_answers_hint_range"
        ),
        CheckConstraint(
            "time_spent_seconds IS NULL OR time_spent_seconds >= 0",
            name="ck_student_answers_time_non_negative",
        ),
        CheckConstraint(
            "comprehension_type IS NULL OR comprehension_type IN "
            "('epl', 'predict_output', 'variation')",
            name="ck_student_answers_comprehension_type_enum",
        ),
        Index("ix_student_answers_user_answered", "user_id", "answered_at"),
        Index("ix_student_answers_question", "question_id"),
    )
