import pytest
import sqlalchemy
from sqlalchemy import Column, Integer, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_postgres_fixture, Rows

Base = declarative_base()


class Quarter(Base):
    __tablename__ = "quarter"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    year = Column(SmallInteger, nullable=False)
    quarter = Column(SmallInteger, nullable=False)


class Report(Base):
    __tablename__ = "report"

    id = Column(Integer, primary_key=True)


rows = Rows(Report(id=3))

postgres_1 = create_postgres_fixture(Base, rows, tables=["report"])


def test_create_specific_tables_only_implicit_public(postgres_1):
    with pytest.raises(sqlalchemy.exc.ProgrammingError) as e:
        postgres_1.execute("SELECT * FROM quarter")

    assert 'relation "quarter" does not exist' in str(e)

    execute = postgres_1.execute(
        """
        SELECT *
        FROM report
        """
    )
    assert [(3,)] == list(execute)


postgres_2 = create_postgres_fixture(Base, rows, tables=["public.report"])


def test_create_specific_tables_only_explicit_public(postgres_2):
    with pytest.raises(sqlalchemy.exc.ProgrammingError) as e:
        postgres_2.execute("SELECT * FROM quarter")

    assert 'relation "quarter" does not exist' in str(e)

    execute = postgres_2.execute(
        """
        SELECT *
        FROM report
        """
    )
    assert [(3,)] == list(execute)


postgres_3 = create_postgres_fixture(Base, rows, tables=["public.report", "quarter"])


def test_create_specific_tables(postgres_3):
    execute = postgres_3.execute(
        """
        SELECT *
        FROM quarter
        ORDER BY id
        """
    )
    assert [] == list(execute)

    execute = postgres_3.execute(
        """
        SELECT *
        FROM report
        """
    )
    assert [(3,)] == list(execute)
