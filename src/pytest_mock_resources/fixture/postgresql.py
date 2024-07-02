from __future__ import annotations

import inspect
import logging
from typing import cast, TYPE_CHECKING

import pytest
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from pytest_mock_resources.compat import get_resource
from pytest_mock_resources.container.base import (
    async_retry,
    DEFAULT_RETRIES,
    get_container,
    retry,
)
from pytest_mock_resources.container.postgres import (
    get_sqlalchemy_engine,
    PostgresConfig,
)
from pytest_mock_resources.fixture.base import (
    asyncio_fixture,
    generate_fixture_id,
    Scope,
)
from pytest_mock_resources.hooks import get_pytest_flag
from pytest_mock_resources.sqlalchemy import (
    bifurcate_actions,
    EngineManager,
    normalize_actions,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

log = logging.getLogger(__name__)


class DatabaseExistsError(RuntimeError):
    """Raise when the database being created already exists.

    This exception commonly occurs during multiprocess test execution, as a
    sentinel for gracefully continuing among test workers which attempt to create
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
    scope: Scope = "function",
    tables=None,
    session=None,
    async_=False,
    createdb_template="template1",
    engine_kwargs=None,
    template_database=True,
    actions_share_transaction=None,
    cleanup_databases: bool | None = None,
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
        actions_share_transaction: When True, the transaction used by `ordered_actions` context
            will be the same as the one handed to the test function. This is required in order
            to support certain usages of `ordered_actions, such as the creation of temp tables
            through a `Statements` object. By default, this behavior is enabled for synchronous
            fixtures for backwards compatibility; and disabled by default for
            asynchronous fixtures (the way v2-style/async features work in SQLAlchemy can lead
            to bad default behavior).
        cleanup_databases: When `True` created databases will be deleted after dependent tests
            have completed. Defaults to `None` which causes it to refer to the `pmr_cleanup`/`--pmr-cleanup`
            pytest-level config (this defaults to `False`).
    """
    fixture_id = generate_fixture_id(enabled=template_database, name="pg")
    scope_fixture_name = f"pmr_postgres_scope_{fixture_id}"

    engine_kwargs_ = engine_kwargs or {}
    engine_manager_kwargs = {
        "ordered_actions": ordered_actions,
        "tables": tables,
        "createdb_template": createdb_template,
        "session": session,
        "fixture_id": fixture_id,
        "actions_share_transaction": actions_share_transaction,
    }

    register_scope_fixture(
        engine_manager_kwargs,
        engine_kwargs=engine_kwargs_,
        name=scope_fixture_name,
        cleanup_databases=cleanup_databases,
        async_=async_,
        container_fixture="pmr_postgres_container",
        config_fixture="pmr_postgres_config",
    )

    if async_:

        async def _async(*_, pmr_postgres_container, pmr_postgres_config, request):
            cleanup = resolve_cleanup(request.config, cleanup_databases)

            fixture_scope = _async_scope_fixture(
                engine_manager_kwargs,
                engine_kwargs=engine_kwargs_,
                cleanup_databases=cleanup,
                config_fixture="pmr_postgres_config",
            )
            async for template_database, engine_manager in fixture_scope(request):
                fixture = _async_fixture(
                    pmr_postgres_config,
                    engine_kwargs_,
                    template_database,
                    engine_manager.copy(),
                    cleanup_databases=cleanup,
                )
                async for _, conn in fixture:
                    yield conn

        usefixture = pytest.mark.usefixtures(scope_fixture_name)
        return usefixture(asyncio_fixture(_async, scope=scope))

    @pytest.mark.usefixtures(scope_fixture_name)
    @pytest.fixture(scope=scope)
    def _sync(*_, pmr_postgres_container, pmr_postgres_config, request):
        cleanup = resolve_cleanup(request.config, cleanup_databases)
        template_database, engine_manager = request.getfixturevalue(scope_fixture_name)

        fixture = _sync_fixture(
            pmr_postgres_config,
            engine_kwargs_,
            template_database,
            engine_manager.copy(),
            cleanup_databases=cleanup,
        )
        for _, conn in fixture:
            yield conn

    return _sync


def register_scope_fixture(
    engine_manager_kwargs,
    engine_kwargs,
    *,
    name,
    cleanup_databases: bool | None = None,
    async_: bool = False,
    container_fixture: str,
    config_fixture: str,
):
    if async_:
        scope_fixture = _async_scope_fixture
        fixture_fn = asyncio_fixture
    else:
        scope_fixture = _sync_scope_fixture
        fixture_fn = pytest.fixture  # type: ignore

    caller_globals = find_caller_globals()
    if name not in caller_globals:
        fixture = fixture_fn(
            scope_fixture(
                engine_manager_kwargs,
                engine_kwargs=engine_kwargs,
                cleanup_databases=cleanup_databases,
                config_fixture=config_fixture,
            ),
            scope="session",
            name=name,
        )
        fixture_uses = pytest.mark.usefixtures(container_fixture, config_fixture)
        caller_globals[name] = fixture_uses(fixture)


def _sync_scope_fixture(
    engine_manager_kwargs,
    *,
    engine_kwargs: dict,
    config_fixture: str,
    cleanup_databases: bool | None = None,
    name="postgres",
):
    def fixture(request):
        cleanup = resolve_cleanup(request.config, cleanup_databases)

        pmr_config = request.getfixturevalue(config_fixture)

        root_engine = cast(
            Engine,
            get_sqlalchemy_engine(pmr_config, pmr_config.root_database),
        )
        conn = retry(root_engine.connect, retries=DEFAULT_RETRIES)
        conn.close()
        root_engine.dispose()

        root_engine = cast(
            Engine,
            get_sqlalchemy_engine(pmr_config, pmr_config.root_database, autocommit=True),
        )
        with root_engine.connect() as root_conn:
            with root_conn.begin() as trans:
                (
                    template_database,
                    template_manager,
                    engine_manager,
                ) = create_engine_manager(root_conn, **engine_manager_kwargs, fixture=name)
                trans.commit()
        root_engine.dispose()

        if template_manager:
            assert template_database

            template_engine = cast(
                Engine,
                get_sqlalchemy_engine(pmr_config, template_database, **engine_kwargs),
            )
            with template_engine.connect() as conn:
                with conn.begin() as trans:
                    template_manager.run_static_actions(conn)
                    trans.commit()
            template_engine.dispose()

        try:
            yield template_database, engine_manager
        finally:
            if cleanup and template_database.startswith("pmr_template"):
                with root_engine.connect() as root_conn:
                    _sync_drop_database(root_conn, template_database)
                root_engine.dispose()

    return fixture


def _sync_fixture(
    pmr_config,
    engine_kwargs,
    template_database: Scope,
    engine_manager: EngineManager,
    *,
    cleanup_databases: bool = False,
):
    # Everything below is normal per-test context. We create a brand new database/engine/manager
    # distinct from what might have been used for the template database.
    root_engine = cast(
        Engine,
        get_sqlalchemy_engine(pmr_config, pmr_config.root_database, autocommit=True),
    )
    with root_engine.connect() as root_conn:
        with root_conn.begin() as trans:
            database_name = _produce_clean_database(root_conn, createdb_template=template_database)
            trans.commit()
    root_engine.dispose()

    engine = get_sqlalchemy_engine(pmr_config, database_name, **engine_kwargs)
    try:
        yield from engine_manager.manage_sync(engine)
    finally:
        if cleanup_databases:
            with root_engine.connect() as root_conn:
                _sync_drop_database(root_conn, database_name)
            root_engine.dispose()


def _async_scope_fixture(
    engine_manager_kwargs,
    *,
    engine_kwargs: dict,
    config_fixture: str,
    cleanup_databases: bool | None = None,
    name="postgres",
):
    async def fixture(request):
        cleanup = resolve_cleanup(request.config, cleanup_databases)

        pmr_config = request.getfixturevalue(config_fixture)

        root_engine = cast(
            "AsyncEngine",
            get_sqlalchemy_engine(
                pmr_config,
                pmr_config.root_database,
                async_=True,
                autocommit=True,
            ),
        )

        root_conn = await async_retry(root_engine.connect, retries=DEFAULT_RETRIES)
        await root_conn.close()

        async with root_engine.connect() as root_conn:
            async with root_conn.begin() as trans:
                (
                    template_database,
                    template_manager,
                    engine_manager,
                ) = await root_conn.run_sync(
                    create_engine_manager,
                    **engine_manager_kwargs,
                    fixture=name,
                    allow_existing=True,
                )
                await trans.commit()

        if template_manager:
            assert template_database

            engine = cast(
                "AsyncEngine",
                get_sqlalchemy_engine(pmr_config, template_database, **engine_kwargs, async_=True),
            )
            async with engine.begin() as conn:
                await conn.run_sync(template_manager.run_static_actions)
                await conn.commit()
            await engine.dispose()

        try:
            yield template_database, engine_manager
        finally:
            if cleanup and template_database.startswith("pmr_template"):
                async with root_engine.connect() as root_conn:
                    await root_conn.run_sync(_sync_drop_database, template_database)
                await root_engine.dispose()

    return fixture


async def _async_fixture(
    pmr_config,
    engine_kwargs,
    template_database: str,
    engine_manager: EngineManager,
    cleanup_databases: bool = False,
):
    root_engine = cast(
        "AsyncEngine",
        get_sqlalchemy_engine(
            pmr_config,
            pmr_config.root_database,
            async_=True,
            autocommit=True,
        ),
    )
    # Everything below is normal per-test context. We create a brand new database/engine/manager
    # distinct from what might have been used for the template database.
    async with root_engine.connect() as root_conn:
        async with root_conn.begin() as trans:
            database_name = await root_conn.run_sync(
                _produce_clean_database, createdb_template=template_database
            )
            await trans.commit()

    await root_engine.dispose()

    engine = get_sqlalchemy_engine(pmr_config, database_name, **engine_kwargs, async_=True)

    try:
        async for engine, conn in engine_manager.manage_async(engine):
            yield engine, conn
    finally:
        if cleanup_databases:
            async with root_engine.connect() as root_conn:
                await root_conn.run_sync(_sync_drop_database, database_name)
            await root_engine.dispose()


def create_engine_manager(
    root_connection,
    *,
    ordered_actions,
    session,
    tables,
    createdb_template="template1",
    fixture_id=None,
    actions_share_transaction=None,
    fixture="postgres",
    allow_existing: bool = False,
):
    normalized_actions = normalize_actions(ordered_actions, fixture=fixture)
    static_actions, dynamic_actions = bifurcate_actions(normalized_actions)

    template_database = createdb_template
    template_manager = None
    if fixture_id:
        try:
            template_database = _produce_clean_database(
                root_connection,
                createdb_template=createdb_template,
                database_name=fixture_id,
                ignore_failure=True,
            )

            template_manager = EngineManager(
                dynamic_actions,
                static_actions=static_actions,
                session=session,
                tables=tables,
            )
        except DatabaseExistsError:
            # This implies it's been created during a prior test, and the template should already be
            # populated.
            if not allow_existing:
                raise

        # The template to be used needs to be changed for the downstream database to the template
        # we created earlier.
        template_database = fixture_id

        # With template databases, static actions must be zeroed out so they're only executed once.
        # It only happens in this condition, so that when template databases are **not** used, we
        # execute them during the normal `manage_sync` flow per-test.
        static_actions = []

    fixture_manager = EngineManager(
        dynamic_actions,
        static_actions=static_actions,
        session=session,
        tables=tables,
        actions_share_transaction=actions_share_transaction,
    )
    return template_database, template_manager, fixture_manager


def _produce_clean_database(
    root_conn: Connection,
    *,
    trans=None,
    createdb_template="template1",
    database_name=None,
    ignore_failure=False,
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
        raise DatabaseExistsError(database_name)

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
    id_ = next(iter(result))[0]
    return f"pytest_mock_resource_db_{id_}"


def _sync_drop_database(conn: Connection, database_name: str):
    with conn.begin() as trans:
        conn.execute(text(f"DROP DATABASE {database_name}"))
        trans.commit()


def find_caller_globals():
    """Return the stackframe of the calling function of the `create_<x_fixture` call."""
    ignore_path = get_resource("pytest_mock_resources")
    stack = inspect.stack()
    for item in stack:
        if item.filename.startswith(ignore_path) or item.filename.endswith("pdb.py"):
            continue

        frame = item.frame
        return frame.f_globals

    raise RuntimeError("Could not find calling frame.")  # pragma: no cover


def resolve_cleanup(config, value: bool | None) -> bool:
    if value is None:
        return get_pytest_flag(config, "pmr_cleanup")
    return value
