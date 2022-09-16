from typing import List

import pytest
from sqlalchemy import Column, ForeignKey, Integer, String, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import relationship

from pytest_mock_resources import create_postgres_fixture, Rows, Statements
from pytest_mock_resources.compat.sqlalchemy import declarative_base
from tests import skip_if_not_sqlalchemy2

Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "stuffs"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    objects: List["Object"] = relationship("Object", back_populates="owner")


class Object(Base):
    __tablename__ = "object"
    __table_args__ = {"schema": "stuffs"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    belongs_to = Column(Integer, ForeignKey("stuffs.user.id"))

    owner: List[User] = relationship("User", back_populates="objects")


rows = Rows(User(name="Harold"), User(name="Gump"))
additional_rows = Rows(User(name="Perrier"), User(name="Mug"))


class Test_non_shared_transaction_session:
    """Assert the temp table is not accessible when not using the shared transaction option."""

    temp_table = Statements(
        "CREATE TEMP TABLE user1 as SELECT DISTINCT CONCAT(name, 1) as name FROM stuffs.user"
    )

    non_shared_transaction_session = create_postgres_fixture(
        rows, temp_table, additional_rows, session=True, actions_share_transaction=False
    )

    @pytest.mark.postgres
    def test_session_is_not_shared(self, non_shared_transaction_session):
        with pytest.raises(ProgrammingError):
            non_shared_transaction_session.execute(text("SELECT * FROM user1"))


class Test_non_shared_transaction_engine:
    """Assert the temp table is not accessible when not using the shared transaction option."""

    temp_table = Statements(
        "CREATE TEMP TABLE user1 as SELECT DISTINCT CONCAT(name, 1) as name FROM stuffs.user"
    )

    postgres = create_postgres_fixture(
        rows, temp_table, additional_rows, actions_share_transaction=False
    )

    @pytest.mark.postgres
    def test_engine_is_not_shared(self, postgres):
        with pytest.raises(ProgrammingError):
            with postgres.begin() as conn:
                conn.execute(text("SELECT * FROM user1"))


class Test_ordered_actions:
    """Assert a temp table created in a Statements is accessible to a session based fixture.

    Run the test 5 times to ensure fixture is stateless
    """

    temp_table = Statements(
        "CREATE TEMP TABLE user1 as SELECT DISTINCT CONCAT(name, 1) as name FROM stuffs.user"
    )

    postgres_ordered_actions = create_postgres_fixture(
        rows, temp_table, additional_rows, session=True
    )

    @pytest.mark.parametrize("run", range(5))
    @pytest.mark.postgres
    def test_ordered_actions(self, postgres_ordered_actions, run):
        execute = postgres_ordered_actions.execute(text("SELECT * FROM user1"))
        result = sorted([row[0] for row in execute])
        assert ["Gump1", "Harold1"] == result


class Test_postgres_session_function:
    """Assert a "function" action which operates on a session is handed a session.

    Run the test 5 times to ensure fixture is stateless
    """

    def session_function(session):
        session.add(User(name="Fake Name", objects=[Object(name="Boots")]))

    postgres_session_function = create_postgres_fixture(Base, session_function, session=True)

    @pytest.mark.parametrize("run", range(5))
    @pytest.mark.postgres
    def test_session_function(self, postgres_session_function, run):
        execute = postgres_session_function.execute(text("SELECT * FROM stuffs.object"))
        owner_id = sorted([row[2] for row in execute])[0]
        execute = postgres_session_function.execute(
            text("SELECT * FROM stuffs.user where id = {id}".format(id=owner_id))
        )
        result = [row[1] for row in execute]
        assert result == ["Fake Name"]


postgres_metadata_only = create_postgres_fixture(Base.metadata, session=True)


def test_metadata_only(postgres_metadata_only):
    execute = postgres_metadata_only.execute(text("SELECT * FROM stuffs.user"))

    result = sorted([row[0] for row in execute])
    assert [] == result


class Test_postgres_ordered_actions_async:
    temp_table = Statements(
        "CREATE TEMP TABLE user1 as SELECT DISTINCT CONCAT(name, 1) as name FROM stuffs.user"
    )

    postgres_ordered_actions_async = create_postgres_fixture(
        rows,
        temp_table,
        additional_rows,
        async_=True,
        actions_share_transaction=True,
    )

    @pytest.mark.postgres
    @pytest.mark.asyncio
    @pytest.mark.parametrize("run", range(5))
    @skip_if_not_sqlalchemy2
    async def test_ordered_actions_aysnc_shares_transaction(
        self, postgres_ordered_actions_async, run
    ):
        async with postgres_ordered_actions_async.begin() as conn:
            execute = await conn.execute(text("SELECT * FROM user1"))

        result = sorted([row[0] for row in execute])
        assert ["Gump1", "Harold1"] == result


class Test_session_function_async:
    """

    Run the test more than once (i.e. 5 times) to ensure fixture is stateless.
    """

    def async_session_function(session):
        session.add(User(name="Fake Name", objects=[Object(name="Boots")]))

    postgres_session_function_async = create_postgres_fixture(
        Base, async_session_function, async_=True, session=True
    )

    @pytest.mark.asyncio
    @pytest.mark.postgres
    @pytest.mark.parametrize("run", range(5))
    @skip_if_not_sqlalchemy2
    async def test_session_function_async(self, postgres_session_function_async, run):
        execute = await postgres_session_function_async.execute(text("SELECT * FROM stuffs.object"))
        owner_id = sorted([row[2] for row in execute])[0]
        execute = await postgres_session_function_async.execute(
            text("SELECT * FROM stuffs.user where id = {id}".format(id=owner_id))
        )
        result = [row[1] for row in execute]
        assert result == ["Fake Name"]


engine_function = create_postgres_fixture(
    Base, lambda engine: engine.execute(text("insert into stuffs.user (name) values ('fake')"))
)


def test_engine_function(engine_function):
    with engine_function.connect() as conn:
        result = conn.execute(text("SELECT name FROM stuffs.user")).scalar()
        assert "fake" == result


def async_engine_function(conn):
    conn.execute(text("insert into stuffs.user (name) values ('fake')"))


async_engine_function = create_postgres_fixture(Base, async_engine_function, async_=True)


@pytest.mark.asyncio
@skip_if_not_sqlalchemy2
async def test_async_engine_function(async_engine_function):
    async with async_engine_function.begin() as conn:
        query = await conn.execute(text("SELECT name FROM stuffs.user"))
        result = query.scalar()
    assert "fake" == result


non_template_database = create_postgres_fixture(Base, additional_rows, template_database=False)


@pytest.mark.parametrize("run", range(5))
def test_non_template_database(non_template_database, run):
    with non_template_database.begin() as conn:
        execute = conn.execute(text("SELECT name FROM stuffs.user")).fetchall()
        result = sorted([row[0] for row in execute])
        assert ["Mug", "Perrier"] == result


class Test_multi_metadata_schemata:
    """Assert that schemas are automatically created, given more than one input MetaData.

    Addresses bug which set test-state in such a way that only the first MetaData's
    schemas were created.
    """

    Base = declarative_base()

    class Foo(Base):
        __tablename__ = "foo"
        __table_args__ = {"schema": "foo"}

        id = Column(Integer, primary_key=True, autoincrement=True)

    Base2 = declarative_base()

    class Bar(Base2):
        __tablename__ = "bar"
        __table_args__ = {"schema": "bar"}

        id = Column(Integer, primary_key=True, autoincrement=True)

    multi_metadata_schemata = create_postgres_fixture(Base, Base2)

    @pytest.mark.postgres
    def test_creates_all_metadata_schemas(self, multi_metadata_schemata):
        with multi_metadata_schemata.connect() as conn:
            result = conn.execute(text("select * from foo.foo")).fetchall()
            assert len(result) == 0

            result = conn.execute(text("select * from bar.bar")).fetchall()
            assert len(result) == 0
            # We dont need much in the way of assertions. You would see
            # database errors from the nonexistence of these schemas/tables.
