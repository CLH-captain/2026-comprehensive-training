from app.core.errors import AppError

RECOVERABLE_LOCAL_CODES = frozenset(
    {
        "HERMES_RUNTIME_MISSING",
        "HERMES_START_FAILED",
        "HERMES_FAILED",
        "HERMES_TIMEOUT",
        "HERMES_EMPTY_RESPONSE",
    }
)
PERSONAL_DETAIL_MARKERS = ("我的", "本人", "个人", "学生", "学号", "姓名", "明细")


def is_recoverable_local_error(error: AppError) -> bool:
    return error.code in RECOVERABLE_LOCAL_CODES


def allows_fallback(role: str, question: str) -> bool:
    compact_question = question.replace(" ", "")
    return role == "admin" and not any(
        marker in compact_question for marker in PERSONAL_DETAIL_MARKERS
    )
