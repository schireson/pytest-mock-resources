from sqlalchemy import Column, event, Integer
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_postgres_fixture
from pytest_mock_resources.container.postgres import get_sqlalchemy_engine
from pytest_mock_resources.fixture.database.relational.postgresql import _create_clean_database

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

    def before_execute(conn, clauseelement, multiparams, params, execution_options):
        # Search for our create database statement, so we can assert against it.
        if "CREATE DATABASE" in clauseelement:
            nonlocal statement
            statement = clauseelement
        return clauseelement, multiparams, params

    # Use the event system to hook into the statements being executed by sqlalchemy.
    with root_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        event.listen(conn, "before_execute", before_execute)
        _create_clean_database(conn, createdb_template="template0")
        event.remove(conn, "before_execute", before_execute)

    assert "template0" in statement


def test_createdb_template(createdb_template_pg):
    """Assert successful usage of a fixture which sets the `createdb_template` argument."""
    createdb_template_pg.execute(Thing.__table__.insert().values({"id": 1}))