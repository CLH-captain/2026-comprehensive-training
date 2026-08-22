from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def migration_script() -> ScriptDirectory:
    config = Config(BACKEND_ROOT / "alembic.ini")
    return ScriptDirectory.from_config(config)


def test_migration_history_has_one_initial_head() -> None:
    script = migration_script()
    heads = script.get_heads()

    assert len(heads) == 1
    assert script.get_revision(heads[0]).down_revision is None


def test_initial_migration_creates_and_drops_all_domain_tables() -> None:
    script = migration_script()
    revision = script.get_revision(script.get_current_head())
    source = Path(revision.path).read_text(encoding="utf-8")

    assert source.count("op.create_table(") == 18
    assert source.count("op.drop_table(") == 18
    assert "mysql_engine='InnoDB'" in source
    assert "mysql_charset='utf8mb4'" in source
    assert "chain_of_thought" not in source
