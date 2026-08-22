from collections.abc import Iterable

from sqlalchemy import Table, UniqueConstraint

from app.db.base import Base
from app.models import *

EXPECTED_TABLES = {
    "campuses",
    "academic_terms",
    "colleges",
    "majors",
    "venues",
    "students",
    "club_categories",
    "clubs",
    "club_memberships",
    "activity_categories",
    "activities",
    "activity_registrations",
    "activity_attendance",
    "users",
    "user_club_roles",
    "revoked_tokens",
    "agent_conversations",
    "agent_messages",
}


def unique_column_sets(table: Table) -> set[frozenset[str]]:
    return {
        frozenset(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def foreign_key_targets(table: Table) -> set[str]:
    return {foreign_key.target_fullname for foreign_key in table.foreign_keys}


def index_names(table: Table) -> set[str]:
    return {index.name for index in table.indexes if index.name is not None}


def assert_unique_sets(table_name: str, expected: Iterable[set[str]]) -> None:
    actual = unique_column_sets(Base.metadata.tables[table_name])
    for columns in expected:
        assert frozenset(columns) in actual


def test_all_domain_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_business_identifiers_and_relationships_are_unique() -> None:
    assert_unique_sets("academic_terms", [{"academic_year", "term_no"}])
    assert_unique_sets("club_memberships", [{"club_id", "student_id"}])
    assert_unique_sets("activity_registrations", [{"activity_id", "student_id"}])
    assert_unique_sets("activity_attendance", [{"activity_id", "student_id"}])
    assert_unique_sets("user_club_roles", [{"user_id", "club_id"}])


def test_core_foreign_keys_point_to_the_expected_tables() -> None:
    assert {
        "colleges.id",
        "majors.id",
    }.issubset(foreign_key_targets(Base.metadata.tables["students"]))
    assert {
        "clubs.id",
        "activity_categories.id",
        "academic_terms.id",
        "venues.id",
    }.issubset(foreign_key_targets(Base.metadata.tables["activities"]))
    assert {
        "activities.id",
        "students.id",
    }.issubset(foreign_key_targets(Base.metadata.tables["activity_registrations"]))
    assert {
        "activities.id",
        "students.id",
        "activity_registrations.id",
    }.issubset(foreign_key_targets(Base.metadata.tables["activity_attendance"]))


def test_statistics_hot_paths_have_named_indexes() -> None:
    assert "ix_activities_term_status_start" in index_names(
        Base.metadata.tables["activities"]
    )
    assert "ix_registrations_activity_status" in index_names(
        Base.metadata.tables["activity_registrations"]
    )
    assert "ix_attendance_activity_status" in index_names(
        Base.metadata.tables["activity_attendance"]
    )
    assert "ix_attendance_student_status" in index_names(
        Base.metadata.tables["activity_attendance"]
    )


def test_agent_messages_never_define_hidden_reasoning_storage() -> None:
    message_columns = set(Base.metadata.tables["agent_messages"].columns.keys())
    assert "chain_of_thought" not in message_columns
    assert "reasoning" not in message_columns
