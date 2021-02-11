.. _api:
API
===

Fixture Functions
-----------------

.. automodule:: pytest_mock_resources
    :members: create_postgres_fixture, create_redshift_fixture, create_sqlite_fixture, create_mongo_fixture, create_redis_fixture, Rows, Statements


.. automodule:: pytest_mock_resources.fixture.database.generic
    :members: Credentials

Fixture Config
--------------

.. automodule:: pytest_mock_resources
    :members: pmr_postgres_config, PostgresConfig, pmr_mongo_config, MongoConfig, pmr_redis_config, RedisConfig


Patch Functions
---------------

.. automodule:: pytest_mock_resources
    :members: patch_create_engine, patch_psycopg2_connect
