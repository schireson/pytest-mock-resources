import pytest
import sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, Numeric, Unicode
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.exc import SAWarning
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_postgres_fixture, create_sqlite_fixture, Rows

Base = declarative_base()


class Thing(Base):  # type: ignore
    __tablename__ = "thing"
    __table_args__ = {"schema": "other"}

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(5), nullable=False)


class Fk(Base):  # type: ignore
    __tablename__ = "fk"
    __table_args__ = {"schema": "other"}

    id = Column(Integer, autoincrement=True, primary_key=True)
    thing_id = Column(Integer, ForeignKey("other.thing.id"), nullable=False)


class ColumnTypesTable(Base):  # type: ignore
    __tablename__ = "column_types_table"

    id = Column(Integer, autoincrement=True, primary_key=True)
    json = Column(JSON(none_as_null=True))
    jsonb = Column(JSONB(none_as_null=True))


column_types_table = ColumnTypesTable.__table__


sqlite = create_sqlite_fixture(Base, Rows(Thing(id=1, name="foo")))


def test_create_schema(sqlite):
    result = list(sqlite.execute("select * from other.thing"))
    assert result == [(1, "foo")]


def test_create_all(sqlite):
    Base.metadata.create_all(bind=sqlite)

    result = list(sqlite.execute("select * from other.thing"))
    assert result == [(1, "foo")]


def test_foreign_keys(sqlite):
    sqlite.execute("INSERT INTO other.fk (id, thing_id) VALUES (1, 1)")
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        sqlite.execute("INSERT INTO other.fk (id, thing_id) VALUES (2, 2)")


pg = create_postgres_fixture(Base, Rows(Thing(id=1, name="foo")))


def test_json_column(sqlite):
    sqlite.execute(column_types_table.insert().values(id=1, json={"foo": 2}))
    result = sqlite.execute(sqlalchemy.select([column_types_table.c.json])).scalar()
    assert result == {"foo": 2}


@pytest.mark.postgres
def test_json_column_pg(pg):
    """Included here as a way of showing that this mimics postgres' behavior
    """
    pg.execute(column_types_table.insert().values(id=1, json={"foo": 2}))
    result = pg.execute(sqlalchemy.select([column_types_table.c.json])).scalar()
    assert result == {"foo": 2}


def test_jsonb_column(sqlite):
    sqlite.execute(column_types_table.insert().values(id=1, jsonb={"foo": "bar"}))
    result = sqlite.execute(sqlalchemy.select([column_types_table.c.jsonb])).scalar()
    assert result == {"foo": "bar"}


@pytest.mark.postgres
def test_jsonb_column_pg(pg):
    pg.execute(column_types_table.insert().values(id=1, jsonb={"foo": "bar"}))
    result = pg.execute(sqlalchemy.select([column_types_table.c.jsonb])).scalar()
    assert result == {"foo": "bar"}


NumericBase = declarative_base()


class NumericTable(NumericBase):  # type: ignore
    __tablename__ = "numeric"

    id = Column(Integer, autoincrement=True, primary_key=True)
    value = Column(Numeric(), nullable=False)


sqlite_with_warnings = create_sqlite_fixture(NumericBase, decimal_warnings=True)
sqlite_without_warnings = create_sqlite_fixture(NumericBase)


def test_decimal_warnings_enabled(sqlite_with_warnings):
    sqlite_with_warnings.execute("INSERT INTO numeric (id, value) VALUES (1, 1)")
    with pytest.warns(SAWarning):
        sqlite_with_warnings.execute(sqlalchemy.select([NumericTable.__table__.c.value])).scalar()


@pytest.mark.filterwarnings("error")
def test_decimal_warnings_disabled(sqlite_without_warnings):
    sqlite_without_warnings.execute("INSERT INTO numeric (id, value) VALUES (1, 1)")
    sqlite_without_warnings.execute(sqlalchemy.select([NumericTable.__table__.c.value])).scalar()
