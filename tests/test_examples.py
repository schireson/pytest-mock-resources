from textwrap import dedent

import pytest


@pytest.mark.redis
def test_multiprocess_redis_database(pytester):
    pytester.copy_example()

    # The `-n 4` are here is tightly coupled with the implementation of `test_split.py`.
    args = ["-vv", "-n", "4", "--pmr-multiprocess-safe", "test_split.py"]
    result = pytester.inline_run(*args)
    result.assertoutcome(passed=4, skipped=0, failed=0)


@pytest.mark.postgres
def test_multiprocess_container_cleanup_race_condition(pytester):
    pytester.copy_example()

    # NOTE: This worker count is coupled to `test_split.py`.
    args = ["-vv", "-n", "2", "--pmr-multiprocess-safe", "test_split.py"]
    result = pytester.inline_run(*args)
    result.assertoutcome(passed=2, skipped=0, failed=0)


@pytest.mark.postgres
def test_postgres_cleanup_databases(pytester):
    pytester.makeconftest(
        dedent(
            """
            import pytest
            from sqlalchemy import text

            from pytest_mock_resources import create_postgres_fixture, PostgresConfig
            from pytest_mock_resources.container.postgres import get_sqlalchemy_engine


            @pytest.fixture(scope="session")
            def pmr_postgres_config():
                return PostgresConfig(port=None)


            @pytest.fixture(autouse=True)
            def assert_database_cleanup(pmr_postgres_config, pmr_postgres_container):
                # NOTE: The ephemeral port gives this nested suite its own catalog to snapshot.
                database_names = get_database_names(pmr_postgres_config)

                yield

                # NOTE: The unchanged catalog after fixture teardown proves no test databases remain.
                assert get_database_names(pmr_postgres_config) == database_names


            pg = create_postgres_fixture(session=True, cleanup_databases=True)
            pg_async = create_postgres_fixture(
                session=True,
                async_=True,
                cleanup_databases=True,
            )


            def get_database_names(pmr_postgres_config):
                engine = get_sqlalchemy_engine(
                    pmr_postgres_config,
                    pmr_postgres_config.root_database,
                )
                try:
                    with engine.connect() as connection:
                        database_names = connection.execute(text("SELECT datname FROM pg_database"))
                        return sorted(name for (name,) in database_names)
                finally:
                    engine.dispose()
            """
        ).strip()
    )
    pytester.makepyfile(
        dedent(
            """
            import pytest
            from sqlalchemy import text


            def test_one(pg):
                assert pg.execute(text("SELECT 1")).scalar() == 1


            def test_two(pg):
                assert pg.execute(text("SELECT 1")).scalar() == 1


            @pytest.mark.asyncio
            async def test_async(pg_async):
                assert (await pg_async.execute(text("SELECT 1"))).scalar() == 1
            """
        ).strip()
    )

    result = pytester.runpytest()

    result.assert_outcomes(passed=3)
