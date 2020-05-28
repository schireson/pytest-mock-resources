from sqlalchemy import Column, Integer, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_postgres_fixture, Rows, create_mysql_fixture

Base = declarative_base()


class Quarter(Base):
    __tablename__ = "quarter"

    id = Column(Integer, primary_key=True)
    year = Column(SmallInteger, nullable=False)
    quarter = Column(SmallInteger, nullable=False)


rows = Rows(
    Quarter(id=1, year=2012, quarter=1),
    Quarter(id=2, year=2012, quarter=2),
    Quarter(id=3, year=2012, quarter=3),
    Quarter(id=4, year=2012, quarter=4),
)

postgres = create_postgres_fixture(rows)
mysql = create_mysql_fixture(rows)


def test_rows_postgres(postgres):
    execute = postgres.execute(
        """
        SELECT *
        FROM quarter
        ORDER BY id
        """
    )
    assert [(1, 2012, 1), (2, 2012, 2), (3, 2012, 3), (4, 2012, 4)] == list(execute)


def test_rows_mysql(mysql):
    execute = mysql.execute(
        """
        SELECT *
        FROM quarter
        ORDER BY id
        """
    )
    assert [(1, 2012, 1), (2, 2012, 2), (3, 2012, 3), (4, 2012, 4)] == list(execute)


SecondBase = declarative_base()


class Report(SecondBase):
    __tablename__ = "report"

    id = Column(Integer, primary_key=True)


rows = Rows(Quarter(id=1, year=2012, quarter=1), Quarter(id=2, year=2012, quarter=2), Report(id=3))
base_2_postgres = create_postgres_fixture(rows)
base_2_mysql = create_mysql_fixture(rows)


def test_2_bases_postgres(base_2_postgres):
    execute = base_2_postgres.execute(
        """
        SELECT *
        FROM quarter
        ORDER BY id
        """
    )
    assert [(1, 2012, 1), (2, 2012, 2)] == list(execute)

    execute = base_2_postgres.execute(
        """
        SELECT *
        FROM report
        """
    )
    assert [(3,)] == list(execute)


def test_2_bases_mysql(base_2_mysql):
    execute = base_2_mysql.execute(
        """
        SELECT *
        FROM quarter
        ORDER BY id
        """
    )
    assert [(1, 2012, 1), (2, 2012, 2)] == list(execute)

    execute = base_2_mysql.execute(
        """
        SELECT *
        FROM report
        """
    )
    assert [(3,)] == list(execute)
