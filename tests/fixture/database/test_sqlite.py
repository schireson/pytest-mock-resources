import pytest
import sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, Unicode
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_sqlite_fixture, Rows

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
