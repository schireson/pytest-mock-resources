Async
=====

In general, pytest-mock-resources >=2.0 is required for async support and will naturally require
python >= 36.

Async is easily supportable **outside** pytest-mock-resources, by simply using the `pmr_<resource>_config`
fixture for the given resource to get a handle on the requisite configuration required to produce a client yourself.

For example:

.. code-block:: python

   from sqlalchemy.engine.url import URL
   from sqlalchemy.ext.asyncio import create_async_engine

   @pytest.fixture
   def async_pg(pmr_postgres_config):
       # or `URL.create` in sqlalchemy 1.4+
       create_async_engine(URL(host=pmr_postgres_config.host, database=pmr_postgres_config.database, ...))


However, we're happy to support default/built-in async client implementations where applicable.

Today, async engines are implemented for:
* postgres, using sqlalchemy >=1.4 (with the asyncpg driver)

Generally, support will be available on a per-fixture basis by way of specifying `async_=True` to the
fixture creation function.

For example

.. code-block:: python

   import pytest
   from sqlalchemy import text
   from pytest_mock_resources import create_postgres_fixture

   postgres_async = create_postgres_fixture(async_=True)

   @pytest.mark.asyncio
   async def test_basic_postgres_fixture_async(postgres_async):
       async with postgres_async.connect() as conn:
           await conn.execute(text("select 1"))

pytest-asyncio
--------------
Generally you will want `pytest-asyncio` or similar to be installed. This will allow your async fixture to work
the same way normal fixtures function.
