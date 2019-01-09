from sqlalchemy import Column, Integer, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_postgres_fixture, CreateAll, Rows

Base = declarative_base()


class Quarter(Base):
    __tablename__ = "quarter"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    year = Column(SmallInteger, nullable=False)
    quarter = Column(SmallInteger, nullable=False)


create_all = CreateAll(Base)

public_rows = Rows(
    Quarter(id=1, year=2012, quarter=1),
    Quarter(id=2, year=2012, quarter=2),
    Quarter(id=3, year=2012, quarter=3),
    Quarter(id=4, year=2012, quarter=4),
)


postgres_rows = create_postgres_fixture(ordered_actions=[create_all, public_rows])


def test_rows(postgres_rows):
    execute = postgres_rows.execute(
        """
        SELECT *
        FROM quarter
        ORDER BY id
        """
    )
    assert [(1, 2012, 1), (2, 2012, 2), (3, 2012, 3), (4, 2012, 4)] == list(execute)
