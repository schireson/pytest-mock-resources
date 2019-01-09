import os

from sqlalchemy import Column, Integer, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_postgres_fixture, CreateAll
from pytest_mock_resources.fixture.database import _create_test_based_database_name

Base = declarative_base()


class Quarter(Base):
    __tablename__ = "quarter"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    year = Column(SmallInteger, nullable=False)
    quarter = Column(SmallInteger, nullable=False)


create_all = CreateAll(Base)

postgres_create_all = create_postgres_fixture(ordered_actions=[create_all])


def test_create_all(postgres_create_all):
    execute = postgres_create_all.execute(
        "SELECT tablename FROM pg_catalog.pg_tables WHERE tablename = 'quarter'"
    )

    result = [row[0] for row in execute]
    assert ["quarter"] == result


def test_create_test_based_database_name():
    name = _create_test_based_database_name()

    assert 41 == len(name)
    assert "create_test_based_database_name" in name

    os.environ["PYTEST_CURRENT_TEST"] = (
        ("a" * 10) + ("b" * 10) + ("c" * 10) + ("d" * 10) + ("e" * 10) + ("f" * 10) + ("g" * 10)
    )


def test_max_create_test_based_database_name():
    """Assert that a test name longer than 45 characters returns a name including only the last 45 characters.
    """
    expected = ("c" * 5) + ("d" * 10) + ("e" * 10) + ("f" * 10) + ("g" * 10)

    os.environ["PYTEST_CURRENT_TEST"] = (
        ("a" * 10) + ("b" * 10) + ("c" * 10) + ("d" * 10) + ("e" * 10) + ("f" * 10) + ("g" * 10)
    )

    name = _create_test_based_database_name()

    assert 55 == len(name)
    assert expected in name
    assert "c" * 10 not in name
