import pytest
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from pytest_mock_resources import create_postgres_fixture, Rows, Statements

Base = declarative_base()


class User(Base):  # type: ignore
    __tablename__ = "user"
    __table_args__ = {"schema": "stuffs"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    objects = relationship("Object", back_populates="owner")


class Object(Base):  # type: ignore
    __tablename__ = "object"
    __table_args__ = {"schema": "stuffs"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    belongs_to = Column(Integer, ForeignKey("stuffs.user.id"))
    owner = relationship("User", back_populates="objects")


rows = Rows(User(name="Harold"), User(name="Gump"))

row_dependant_statements = Statements(
    "CREATE TEMP TABLE user1 as SELECT DISTINCT CONCAT(name, 1) as name FROM stuffs.user"
)

additional_rows = Rows(User(name="Perrier"), User(name="Mug"))


def session_function(session):
    session.add(User(name="Fake Name", objects=[Object(name="Boots")]))


postgres_ordered_actions = create_postgres_fixture(rows, row_dependant_statements, additional_rows)

postgres_session_function = create_postgres_fixture(Base, session_function)


# Run the test 5 times to ensure fixture is stateless
@pytest.mark.parametrize("run", range(5))
@pytest.mark.postgres
def test_ordered_actions(postgres_ordered_actions, run):
    execute = postgres_ordered_actions.execute("SELECT * FROM user1")
    result = sorted([row[0] for row in execute])
    assert ["Gump1", "Harold1"] == result


# Run the test 5 times to ensure fixture is stateless
@pytest.mark.parametrize("run", range(5))
@pytest.mark.postgres
def test_session_function(postgres_session_function, run):
    execute = postgres_session_function.execute("SELECT * FROM stuffs.object")
    owner_id = sorted([row[2] for row in execute])[0]
    execute = postgres_session_function.execute(
        "SELECT * FROM stuffs.user where id = {id}".format(id=owner_id)
    )
    result = [row[1] for row in execute]
    assert result == ["Fake Name"]


postgres_metadata_only = create_postgres_fixture(Base.metadata)


@pytest.mark.postgres
def test_metadata_only(postgres_metadata_only):
    execute = postgres_metadata_only.execute("SELECT * FROM stuffs.user")

    result = sorted([row[0] for row in execute])
    assert [] == result
