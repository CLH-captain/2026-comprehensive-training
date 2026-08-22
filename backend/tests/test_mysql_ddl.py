from app.db.base import Base
from app.models import *
from sqlalchemy.dialects.mysql import dialect
from sqlalchemy.schema import CreateTable


def test_every_table_compiles_for_mysql() -> None:
    mysql_dialect = dialect()

    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=mysql_dialect))
        assert f"CREATE TABLE {table.name}" in ddl
        assert "ENGINE=InnoDB" in ddl
        assert "CHARSET=utf8mb4" in ddl
