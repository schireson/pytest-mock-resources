import asyncio

from sqlalchemy.ext.asyncio import create_async_engine


async def _get_sqlalchemy_async_engine(config, database_name, isolation_level=None):
    URI_TEMPLATE = (
        "postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}?ssl=disable"
    )
    DB_URI = URI_TEMPLATE.format(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        database=database_name,
    )

    options = {}
    if isolation_level:
        options["isolation_level"] = isolation_level

    # Trigger any asyncpg-based import failures
    from pytest_mock_resources.compat import asyncpg
    asyncpg.connect

    engine = create_async_engine(DB_URI, **options)

    async with engine.connect() as conn:
        pass

    return engine


def get_sqlalchemy_async_engine(config, database_name, isolation_level=None):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_get_sqlalchemy_async_engine(config, database_name, isolation_level))