import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_postgres_fixture, CreateAll, Rows, Statements

Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "stuffs"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)


create_all = CreateAll(Base)

rows = Rows(User(name="Harold"), User(name="Gump"))

row_dependant_statements = Statements(
    "CREATE TEMP TABLE user1 as SELECT DISTINCT CONCAT(name, 1) as name FROM stuffs.user"
)

additional_rows = Rows(User(name="Perrier"), User(name="Mug"))

postgres_ordered_actions = create_postgres_fixture(
    ordered_actions=[create_all, rows, row_dependant_statements, additional_rows]
)


# Run the test 5 times to ensure fixture is stateless
@pytest.mark.parametrize("run", range(5))
def test_ordered_actions(postgres_ordered_actions, run):
    execute = postgres_ordered_actions.execute("SELECT * FROM user1")

    result = sorted([row[0] for row in execute])
    assert ["Gump1", "Harold1"] == result
