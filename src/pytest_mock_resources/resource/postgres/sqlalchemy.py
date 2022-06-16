import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import Connection

from pytest_mock_resources.credentials import assign_fixture_credentials
from pytest_mock_resources.sqlalchemy.engine_manager import (
    bifurcate_actions,
    EngineManager,
    normalize_actions,
)


class DatabaseExistsError(RuntimeError):
    """Raise when the database being created already exists.

    This exception commonly occurs during multiprocess test execution, as a
    sentinel for gracefully continueing among test workers which attempt to create
    the same database.
    """


def get_sqlalchemy_engine(config, database_name, **engine_kwargs):
    url = sqlalchemy.engine.url.URL(
        drivername="postgresql+psycopg2",
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        database=database_name,
        query={"sslmode": "disable"},
    )

    engine = sqlalchemy.create_engine(url, **engine_kwargs)

    # Verify engine is connected
    engine.connect()

    return engine


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
            database_name = produce_clean_database(
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
    database_name = produce_clean_database(root_engine, createdb_template=createdb_template)
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


def produce_clean_database(
    root_conn: Connection, createdb_template="template1", database_name=None, ignore_failure=False
):
    if not database_name:
        database_name = generate_database_name(root_conn)

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


def generate_database_name(conn):
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
