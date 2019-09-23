from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_sqlite_fixture, Rows

Base = declarative_base()


class Thing(Base):  # type: ignore
    __tablename__ = "thing"
    __table_args__ = {"schema": "other"}

    id = Column(Integer, primary_key=True)


sqlite = create_sqlite_fixture(Base, Rows(Thing(id=3)))


def test_create_schema(sqlite):
    result = list(sqlite.execute("select * from other.thing"))
    assert result == [(3,)]


def test_create_all(sqlite):
    Base.metadata.create_all(bind=sqlite)

    result = list(sqlite.execute("select * from other.thing"))
    assert result == [(3,)]
