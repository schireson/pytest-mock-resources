from pytest_mock_resources.compat import verify_import


def create_mongo_fixture(scope="function"):
    """Produce a mongo fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    Arguments:
        scope: Passthrough pytest's fixture scope.
    """
    verify_import("pymongo", extra_name="mongo")

    from pytest_mock_resources.resource import mongo

    return mongo.create_mongo_fixture(scope=scope)


def create_mysql_fixture(*ordered_actions, scope="function", tables=None, session=None):
    """Produce a MySQL fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    Arguments:
        ordered_actions: Any number of ordered actions to be run on test setup.
        scope: Passthrough pytest's fixture scope.
        tables: Subsets the tables created by `ordered_actions`. This is generally
            most useful when a model-base was specified in `ordered_actions`.
        session: Whether to return a session instead of an engine directly. This can
            either be a bool or a callable capable of producing a session.
    """
    verify_import("sqlalchemy", extra_name="mysql")

    from pytest_mock_resources.resource import mysql

    return mysql.create_mysql_fixture(*ordered_actions, scope=scope, tables=tables, session=session)


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

            database, then creating all subsequent per-test databases from that template.
    """
    verify_import("sqlalchemy", "psycopg2", extra_name="postgres/postgres-binary")
    if async_:
        verify_import("asyncpg", extra_name="postgres-async")

    from pytest_mock_resources.resource import postgres

    postgres.create_postgres_fixture(
        *ordered_actions,
        scope=scope,
        tables=tables,
        session=session,
        async_=async_,
        createdb_template=createdb_template,
        engine_kwargs=engine_kwargs,
        template_database=template_database,
    )


def create_redis_fixture(scope="function"):
    """Produce a Redis fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    .. note::

       If running tests in parallel, the implementation fans out to different redis "database"s,
       up to a 16 (which is the default container fixed limite). This means you can only run
       up to 16 simultaneous tests.

       Additionally, any calls to `flushall` or any other cross-database calls **will** still
       represent cross-test state.

       Finally, the above notes are purely describing the current implementation, and should not
       be assumed. In the future, the current database selection mechanism may change, or
       databases may not be used altogether.

    Args:
        scope (str): The scope of the fixture can be specified by the user, defaults to "function".

    Raises:
        KeyError: If any additional arguments are provided to the function than what is necessary.
    """
    verify_import("redis", extra_name="redis")

    from pytest_mock_resources.resource import redis

    return redis.create_redis_fixture(scope=scope)


def create_redshift_fixture(
    *ordered_actions,
    scope="function",
    tables=None,
    session=None,
    async_=False,
    createdb_template="template1",
    engine_kwargs=None,
    template_database=True,
):
    """Produce a Redshift fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    Note that, by default, redshift uses a postgres container as the database server
    and attempts to reintroduce appoximations of Redshift features, such as
    S3 COPY/UNLOAD, redshift-specific functions, and other specific behaviors.

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
    verify_import("sqlalchemy", "sqlparse", "boto3", extra_name="redshift")

    from pytest_mock_resources.resource import redshift

    redshift.create_redshift_fixture(
        *ordered_actions,
        scope=scope,
        tables=tables,
        session=session,
        async_=async_,
        createdb_template=createdb_template,
        engine_kwargs=engine_kwargs,
        template_database=template_database,
    )


def create_sqlite_fixture(
    *ordered_actions,
    scope="function",
    tables=None,
    session=None,
    decimal_warnings=False,
    postgres_like=True,
):
    """Produce a SQLite fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    Arguments:
        ordered_actions: Any number of ordered actions to be run on test setup.
        scope: Passthrough pytest's fixture scope.
        tables: Subsets the tables created by `ordered_actions`. This is generally
            most useful when a model-base was specified in `ordered_actions`.
        session: Whether to return a session instead of an engine directly. This can
            either be a bool or a callable capable of producing a session.
        decimal_warnings: Whether to show sqlalchemy decimal warnings related to precision loss. The
            default `False` suppresses these warnings.
        postgres_like: Whether to add extra SQLite features which attempt to mimic postgres
            enough to stand in for it for testing.
    """
    from pytest_mock_resources.resource import sqlite

    sqlite.create_sqlite_fixture(
        *ordered_actions,
        scope=scope,
        tables=tables,
        session=session,
        decimal_warnings=decimal_warnings,
        postgres_like=postgres_like,
    )
