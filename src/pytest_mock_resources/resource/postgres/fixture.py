import pytest

from pytest_mock_resources.config import PostgresConfig
from pytest_mock_resources.container import get_container
from pytest_mock_resources.fixture import generate_fixture_id
from pytest_mock_resources.resource.postgres.sqlalchemy import (
    create_engine_manager,
    get_sqlalchemy_engine,
)


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
