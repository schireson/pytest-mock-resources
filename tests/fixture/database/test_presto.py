from typing import Any

from sqlalchemy import Column, INT, String
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_hive_fixture, create_presto_fixture
from pytest_mock_resources.fixture.database.presto import (
    create_hive_fixture_raw,
    create_presto_fixture_raw,
)

Base: Any = declarative_base()


class Table(Base):
    __tablename__ = "test_sqla"
    __table_args__ = {"schema": "sqla"}

    foo = Column(INT, primary_key=True)
    bar = Column(String)


hive = create_hive_fixture(Base, scope="session")
hive_raw = create_hive_fixture_raw(scope="session")
presto = create_presto_fixture(scope="session")
presto_raw = create_presto_fixture_raw(scope="session")


def test_presto_fixture(presto_raw):
    cursor = presto_raw.cursor()
    cursor.execute("SELECT 1")

    assert cursor.fetchone()[0] == 1


def test_presto_show_session(presto_raw):
    cursor = presto_raw.cursor()
    cursor.execute("SHOW SESSION")


def test_presto_hive_raw_fixtures(hive_raw, presto_raw):
    cursor = hive_raw.cursor()
    cursor.execute("CREATE TABLE test_raw (foo INT, bar STRING)")
    cursor.execute("LOAD DATA LOCAL INPATH '/tmp/inputs/test.csv' OVERWRITE INTO TABLE test_raw")

    cursor = presto_raw.cursor()
    cursor.execute("SELECT COUNT(*) FROM default.test_raw")
    assert cursor.fetchone()[0] == 3


def test_presto_hive_fixtures(hive, presto):
    hive.execute(
        "LOAD DATA LOCAL INPATH '/tmp/inputs/test.csv' OVERWRITE INTO TABLE sqla.test_sqla"
    )

    result_proxy = presto.execute("SELECT COUNT(*) FROM sqla.test_sqla")
    assert list(result_proxy)[0][0] == 3
