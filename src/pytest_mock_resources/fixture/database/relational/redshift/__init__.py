import pytest

from pytest_mock_resources.container.base import get_container
from pytest_mock_resources.container.redshift import get_sqlalchemy_engine, RedshiftConfig
from pytest_mock_resources.fixture import generate_fixture_id
from pytest_mock_resources.fixture.database.relational.postgresql import create_engine_manager
from pytest_mock_resources.patch.redshift import psycopg2, sqlalchemy


@pytest.fixture(scope="session")
def pmr_redshift_config():
    """Override this fixture with a :class:`RedshiftConfig` instance to specify different defaults.

    Note that, by default, redshift uses a postgres container.

    Examples:
        >>> @pytest.fixture(scope='session')
        ... def pmr_redshift_config():
        ...     return RedshiftConfig(image="postgres:9.6.10", root_database="foo")
    """
    return RedshiftConfig()


@pytest.fixture(scope="session")
def pmr_redshift_container(pytestconfig, pmr_redshift_config):
    yield from get_container(pytestconfig, pmr_redshift_config)


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

    from pytest_mock_resources.fixture.database.relational.redshift.udf import REDSHIFT_UDFS

    fixture_id = generate_fixture_id(enabled=template_database, name="pg")

    ordered_actions = ordered_actions + (REDSHIFT_UDFS,)

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
    def _sync(pmr_redshift_container, pmr_redshift_config):
        engine_manager = _create_engine_manager(pmr_redshift_config)
        database_name = engine_manager.engine.url.database

        for engine in engine_manager.manage_sync():
            sqlalchemy.register_redshift_behavior(engine)
            with psycopg2.patch_connect(pmr_redshift_config, database_name):
                yield engine

    @pytest.fixture(scope=scope)
    async def _async(pmr_redshift_container, pmr_redshift_config):
        engine_manager = _create_engine_manager(pmr_redshift_config)
        database_name = engine_manager.engine.url.database

        async for engine in engine_manager.manage_async():
            sqlalchemy.register_redshift_behavior(engine)
            with psycopg2.patch_connect(pmr_redshift_config, database_name):
                yield engine

    if async_:
        return _async
    else:
        return _sync
