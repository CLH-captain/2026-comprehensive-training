from sqlalchemy import Connection, text

from app.statistics.summaries import club_summary, student_summary


def test_student_summary_uses_present_and_late(statistics_connection: Connection) -> None:
    student_id = statistics_connection.scalar(
        text(
            """
            SELECT student_id FROM activity_attendance
            WHERE status IN ('present', 'late')
            GROUP BY student_id ORDER BY COUNT(*) DESC, student_id LIMIT 1
            """
        )
    )

    result = student_summary(statistics_connection, student_id)

    assert result is not None
    assert result["participations"] > 0
    assert result["registrations"] >= result["participations"]
    assert 0 <= result["attendance_rate"] <= 100


def test_club_summary_contains_unified_activity_score(statistics_connection: Connection) -> None:
    result = club_summary(statistics_connection, 1)

    assert result is not None
    assert result["members"] > 0
    assert 0 <= result["activity_score"] <= 100


def test_missing_entity_summary_returns_none(statistics_connection: Connection) -> None:
    assert student_summary(statistics_connection, 999999) is None
    assert club_summary(statistics_connection, 999999) is None
