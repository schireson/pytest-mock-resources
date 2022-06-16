from pytest_mock_resources.config import (
    MongoConfig,
    MysqlConfig,
    PostgresConfig,
    RedisConfig,
    RedshiftConfig,
)
from pytest_mock_resources.fixtures import (
    create_mongo_fixture,
    create_mysql_fixture,
    create_postgres_fixture,
    create_redis_fixture,
    create_redshift_fixture,
    create_sqlite_fixture,
)
from pytest_mock_resources.sqlalchemy.actions import Rows, Statements, StaticStatements

try:
    from pytest_mock_resources.resource.mongo import pmr_mongo_config, pmr_mongo_container
except ImportError:
    pass

try:
    from pytest_mock_resources.resource.mysql import pmr_mysql_config, pmr_mysql_container
except ImportError:
    pass

try:
    from pytest_mock_resources.resource.postgres import pmr_postgres_config, pmr_postgres_container
except ImportError:
    pass

try:
    from pytest_mock_resources.resource.redis import pmr_redis_config, pmr_redis_container
except ImportError:
    pass

try:
    from pytest_mock_resources.resource.redshift import pmr_redshift_config, pmr_redshift_container
except ImportError:
    pass

__all__ = [
    "MongoConfig",
    "MysqlConfig",
    "PostgresConfig",
    "RedisConfig",
    "RedshiftConfig",
    "create_mongo_fixture",
    "create_mysql_fixture",
    "create_postgres_fixture",
    "create_redis_fixture",
    "create_redshift_fixture",
    "create_sqlite_fixture",
    "pmr_mongo_config",
    "pmr_mongo_container",
    "pmr_mysql_config",
    "pmr_mysql_container",
    "pmr_postgres_config",
    "pmr_postgres_container",
    "pmr_redis_config",
    "pmr_redis_container",
    "pmr_redshift_config",
    "pmr_redshift_container",
    "Rows",
    "Statements",
    "StaticStatements",
]


# isort: split

from pytest_mock_resources.hooks import pytest_addoption  # noqa
from pytest_mock_resources.hooks import pytest_configure  # noqa
from pytest_mock_resources.hooks import pytest_itemcollected  # noqa
from pytest_mock_resources.hooks import pytest_sessionfinish  # noqa
