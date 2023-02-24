from sqlalchemy import Column, event, Integer

from pytest_mock_resources import create_postgres_fixture
from pytest_mock_resources.compat.sqlalchemy import declarative_base
from pytest_mock_resources.container.postgres import get_sqlalchemy_engine
from pytest_mock_resources.fixture.postgresql import _produce_clean_database

Base = declarative_base()


class Thing(Base):
    __tablename__ = "thing"

    id = Column(Integer, autoincrement=True, primary_key=True)


createdb_template_pg = create_postgres_fixture(Base, createdb_template="template0")


def test_create_clean_database_createdb_template(pmr_postgres_config, createdb_template_pg):
    """Assert `createdb_template` is included in emitted CREATE DATABASE statement."""
    root_engine = get_sqlalchemy_engine(
        pmr_postgres_config, pmr_postgres_config.root_database, isolation_level="AUTOCOMMIT"
    )

    statement = ""

    def before_execute(conn, clauseelement, multiparams, params, execution_options=None):
        # Search for our create database statement, so we can assert against it.
        if "CREATE DATABASE" in clauseelement.text:
            nonlocal statement
            statement = clauseelement.text
        return clauseelement, multiparams, params

    # Use the event system to hook into the statements being executed by sqlalchemy.
    with root_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        event.listen(conn, "before_execute", before_execute)
        _produce_clean_database(conn, createdb_template="template0")
        event.remove(conn, "before_execute", before_execute)

    assert "template0" in statement


def test_createdb_template(createdb_template_pg):
    """Assert successful usage of a fixture which sets the `createdb_template` argument."""
    with createdb_template_pg.begin() as conn:
        conn.execute(Thing.__table__.insert().values({"id": 1}))


nested_transaction = create_postgres_fixture(Base)


def test_nested_transaction(nested_transaction):
    """Assert success with a fixture relying on being in a transaction (like SAVEPOINT)."""
    with nested_transaction.begin() as conn:
        with conn.begin_nested():
            conn.execute(Thing.__table__.insert().values({"id": 1}))
