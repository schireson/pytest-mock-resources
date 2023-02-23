Postgres
========

.. note::

   The default postgres driver support is `psycopg2` for synchronous fixtures,
   and `asyncpg` for async fixtures. If you want to use a different driver, you
   can configure the `drivername` field using the `pmr_postgres_config` fixture:

   ```python
   from pytest_mock_resources import PostgresConfig

   @pytest.fixture
   def pmr_postgres_config():
       PostgresConfig(drivername='postgresql+psycopg2')  # but whatever drivername you require.
   ```

   Note however, that the `asyncpg` driver **only** works with the async fixture, and the
   `psycopg2` driver **only** works with the synchronous fixture. These are inherent
   attributes of the drivers/support within SQLAlchemy.
