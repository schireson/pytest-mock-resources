import logging

import pytest
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import Connection

from pytest_mock_resources.container.base import get_container
from pytest_mock_resources.container.postgres import get_sqlalchemy_engine, PostgresConfig
from pytest_mock_resources.fixture import generate_fixture_id
from pytest_mock_resources.fixture.database.generic import assign_fixture_credentials
from pytest_mock_resources.fixture.database.relational.generic import (
    bifurcate_actions,
    EngineManager,
    normalize_actions,
)

log = logging.getLogger(__name__)


class DatabaseExistsError(RuntimeError):
    """Raise when the database being created already exists.

    This exception commonly occurs during multiprocess test execution, as a
    sentinel for gracefully continueing among test workers which attempt to create
    the same database.
    """


@pytest.fixture(scope="session")
def pmr_postgres_config():
    """Override this fixture with a :class:`PostgresConfig` instance to specify different defaults.

    Examples:
        >>> @pytest.fixture(scope='session')
        ... def pmr_postgres_config():
        ...     return PostgresConfig(image="postgres:9.6.10", root_database="foo")
    """
    return PostgresConfig()


@pytest.fixture(scope="session")
def pmr_postgres_container(pytestconfig, pmr_postgres_config: PostgresConfig):
    yield from get_container(pytestconfig, pmr_postgres_config)


def create_postgres_fixture(
    *ordered_actions,
    scope="function",
    tables=None,
    session=None,
    async_=False,
    createdb_template="template1",
    engine_kwargs=None,
    template_database=True,
):
    """Produce a Postgres fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    Arguments:
        ordered_actions: Any number of ordered actions to be run on test setup.
        scope: Passthrough pytest's fixture scope.
        tables: Subsets the tables created by `ordered_actions`. This is generally
            most useful when a model-base was specified in `ordered_actions`.
        session: Whether to return a session instead of an engine directly. This can
            either be a bool or a callable capable of producing a session.
        async_: Whether to return an async fixture/client.
        createdb_template: The template database used to create sub-databases. "template1" is the
            default chosen when no template is specified.
        engine_kwargs: Optional set of kwargs to send into the engine on creation.
        template_database: Defaults to True. When True, amortizes the cost of performing database
            setup through `ordered_actions`, by performing them once into a postgres "template"
            database, then creating all subsequent per-test databases from that template.
    """
    fixture_id = generate_fixture_id(enabled=template_database, name="pg")

    def _create_engine_manager(config):
        root_engine = get_sqlalchemy_engine(
            config, config.root_database, isolation_level="AUTOCOMMIT"
        )
        with root_engine.begin() as conn:
            return create_engine_manager(
                conn,
                config,
                ordered_actions=ordered_actions,
                tables=tables,
                createdb_template=createdb_template,
                engine_kwargs=engine_kwargs or {},
                session=session,
                fixture_id=fixture_id,
            )

    @pytest.fixture(scope=scope)
    def _sync(pmr_postgres_container, pmr_postgres_config):
        engine_manager = _create_engine_manager(pmr_postgres_config)
        yield from engine_manager.manage_sync()

    @pytest.fixture(scope=scope)
    async def _async(pmr_postgres_container, pmr_postgres_config):
        engine_manager = _create_engine_manager(pmr_postgres_config)
        async for engine in engine_manager.manage_async():
            yield engine

    if async_:
        return _async
    else:
        return _sync


def create_engine_manager(
    root_engine,
    pmr_postgres_config,
    *,
    ordered_actions,
    session,
    tables,
    engine_kwargs,
    createdb_template="template1",
    fixture_id=None,
):
    normalized_actions = normalize_actions(ordered_actions)
    static_actions, dynamic_actions = bifurcate_actions(normalized_actions)

    if fixture_id:
        try:
            database_name = _produce_clean_database(
                root_engine,
                createdb_template=createdb_template,
                database_name=fixture_id,
                ignore_failure=True,
            )
        except DatabaseExistsError:
            # This implies it's been created during a prior test, and the template should already be
            # populated.
            pass
        else:
            engine = get_sqlalchemy_engine(pmr_postgres_config, database_name, **engine_kwargs)
            engine_manager = EngineManager(
                engine,
                dynamic_actions,
                static_actions=static_actions,
                session=session,
                tables=tables,
                default_schema="public",
            )

            with engine.begin() as conn:
                engine_manager.run_static_actions(conn)
                conn.execute(text("commit"))

            engine.dispose()

        # The template to be used needs to be changed for the downstream database to the template
        # we created earlier.
        createdb_template = fixture_id

        # With template databases, static actions must be zeroed out so they're only executed once.
        # It only happens in this condition, so that when template databases are **not** used, we
        # execute them during the normal `manage_sync` flow per-test.
        static_actions = []

    # Everything below is normal per-test context. We create a brand new database/engine/manager
    # distinct from what might have been used for the template database.
    database_name = _produce_clean_database(root_engine, createdb_template=createdb_template)
    engine = get_sqlalchemy_engine(pmr_postgres_config, database_name, **engine_kwargs)
    _assign_credential(engine, pmr_postgres_config, database_name)

    return EngineManager(
        engine,
        dynamic_actions,
        static_actions=static_actions,
        session=session,
        tables=tables,
        default_schema="public",
    )


def _produce_clean_database(
    root_conn: Connection, createdb_template="template1", database_name=None, ignore_failure=False
):
    if not database_name:
        database_name = _generate_database_name(root_conn)

    try:
        root_conn.execute(text(f'CREATE DATABASE "{database_name}" template={createdb_template}'))
        root_conn.execute(
            text(f'GRANT ALL PRIVILEGES ON DATABASE "{database_name}" TO CURRENT_USER')
        )
    except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.ProgrammingError):
        if not ignore_failure:
            raise
        raise DatabaseExistsError()

    return database_name


def _generate_database_name(conn):
    try:
        conn.execute(text("CREATE TABLE IF NOT EXISTS pytest_mock_resource_db (id serial);"))
    except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.ProgrammingError):
        # A race condition may occur during table creation if:
        #  - another process has already created the table
        #  - the current process begins creating the table
        #  - the other process commits the table creation
        #  - the current process tries to commit the table creation
        pass

    result = conn.execute(text("INSERT INTO pytest_mock_resource_db VALUES (DEFAULT) RETURNING id"))
    id_ = tuple(result)[0][0]
    database_name = "pytest_mock_resource_db_{}".format(id_)
    return database_name


def _assign_credential(engine, config, database_name):
    assign_fixture_credentials(
        engine,
        drivername="postgresql+psycopg2",
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        database=database_name,
    )
