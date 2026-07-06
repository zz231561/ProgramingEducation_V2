"""智慧出題 service — 2-4 Phase（Select / Generate / Validate / Grade / Orchestrate / Hint / Feedback）。"""

from services.quiz.bank import (
    UnitQuestionItem,
    list_unit_question_set,
    pick_random_validated_question,
)
from services.quiz.feedback import (
    ConceptMasteryItem,
    QuizFeedbackResult,
    RecommendedUnit,
    generate_quiz_feedback,
)
from services.quiz.generate import generate_question
from services.quiz.grade import grade_answer
from services.quiz.hint import HintResult, generate_hint
from services.quiz.orchestrator import (
    generate_for_student,
    list_history,
    pick_target_concept,
    submit_answer,
)
from services.quiz.select import (
    CENTRALITY_BONUS,
    WEAK_THRESHOLD,
    select_weak_concepts,
)
from services.quiz.validate import ValidationReport, validate_question
from services.quiz.weakness_set import build_weakness_set

__all__ = [
    "CENTRALITY_BONUS",
    "ConceptMasteryItem",
    "HintResult",
    "QuizFeedbackResult",
    "RecommendedUnit",
    "UnitQuestionItem",
    "WEAK_THRESHOLD",
    "ValidationReport",
    "build_weakness_set",
    "list_unit_question_set",
    "generate_for_student",
    "generate_hint",
    "generate_question",
    "generate_quiz_feedback",
    "grade_answer",
    "list_history",
    "pick_random_validated_question",
    "pick_target_concept",
    "select_weak_concepts",
    "submit_answer",
    "validate_question",
]
