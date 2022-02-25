import pytest

from pytest_mock_resources.container.base import get_container
from pytest_mock_resources.container.redshift import RedshiftConfig
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
def _redshift_container(pytestconfig, pmr_redshift_config):
    yield from get_container(pytestconfig, pmr_redshift_config)


def create_redshift_fixture(
    *ordered_actions,
    scope="function",
    tables=None,
    session=None,
    async_=False,
    createdb_template="template1",
    engine_kwargs=None,
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
    """

    from pytest_mock_resources.fixture.database.relational.redshift.udf import REDSHIFT_UDFS

    ordered_actions = ordered_actions + (REDSHIFT_UDFS,)

    engine_manager_kwargs = dict(
        ordered_actions=ordered_actions,
        tables=tables,
        createdb_template=createdb_template,
        engine_kwargs=engine_kwargs,
    )

    @pytest.fixture(scope=scope)
    def _sync(_redshift_container, pmr_redshift_config):
        engine_manager = create_engine_manager(pmr_redshift_config, **engine_manager_kwargs)
        database_name = engine_manager.engine.url.database

        for engine in engine_manager.manage_sync(session=session):
            sqlalchemy.register_redshift_behavior(engine)
            with psycopg2.patch_connect(pmr_redshift_config, database_name):
                yield engine

    @pytest.fixture(scope=scope)
    async def _async(_redshift_container, pmr_redshift_config):
        engine_manager = create_engine_manager(pmr_redshift_config, **engine_manager_kwargs)
        database_name = engine_manager.engine.url.database

        async for engine in engine_manager.manage_async(session=session):
            sqlalchemy.register_redshift_behavior(engine)
            with psycopg2.patch_connect(pmr_redshift_config, database_name):
                yield engine

    if async_:
        return _async
    else:
        return _sync
