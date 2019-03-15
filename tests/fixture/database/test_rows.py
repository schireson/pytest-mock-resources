from sqlalchemy import Column, Integer, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_postgres_fixture, Rows

Base = declarative_base()


class Quarter(Base):  # type: ignore
    __tablename__ = "quarter"
    __table_args__ = {"schema": "public"}

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


def test_rows(postgres):
    execute = postgres.execute(
        """
        SELECT *
        FROM quarter
        ORDER BY id
        """
    )
    assert [(1, 2012, 1), (2, 2012, 2), (3, 2012, 3), (4, 2012, 4)] == list(execute)


SecondBase = declarative_base()


class Report(SecondBase):  # type: ignore
    __tablename__ = "report"

    id = Column(Integer, primary_key=True)


rows = Rows(Quarter(id=1, year=2012, quarter=1), Quarter(id=2, year=2012, quarter=2), Report(id=3))
base_2_postgres = create_postgres_fixture(rows)


def test_2_bases(base_2_postgres):
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
