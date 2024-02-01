from pytest_mock_resources.compat.import_ import ImportAdaptor

# isort: split
from pytest_mock_resources.compat import sqlalchemy

try:
    import psycopg2
except ImportError:
    fail_message = (
        "Cannot use postgres/redshift fixtures without psycopg2.\n"
        "pip install pytest-mock-resources[postgres] or pytest-mock-resources[[postgres-binary].\n"
        "Additionally, pip install pytest-mock-resources[redshift] for redshift fixtures."
    )
    psycopg2 = ImportAdaptor(
        "psycopg2",
        "postgres",
        fail_message=fail_message,
        extensions=ImportAdaptor(
            "psycopg2", "psycopg2", fail_message=fail_message, cursor=ImportAdaptor
        ),
    )

try:
    import asyncpg
except ImportError:
    fail_message = (
        "Cannot use postgres async fixtures without asyncpg.\n"
        "pip install pytest-mock-resources[postgres-async].\n"
    )
    asyncpg = ImportAdaptor(
        "asyncpg",
        "postgres",
        fail_message=fail_message,
        extensions=ImportAdaptor(
            "asyncpg", "asyncpg", fail_message=fail_message, cursor=ImportAdaptor
        ),
    )

try:
    import boto3
except ImportError:
    boto3 = ImportAdaptor("boto3", "redshift")

try:
    import moto
except ImportError:
    moto = ImportAdaptor("moto", "redshift")

try:
    import sqlparse
except ImportError:
    sqlparse = ImportAdaptor(
        "sqlparse",
        "redshift",
    )

try:
    import pymongo
except ImportError:
    pymongo = ImportAdaptor("pymongo", "mongo")

try:
    import redis
except ImportError:
    redis = ImportAdaptor("redis", "redis")

try:
    import pymysql
except ImportError:
    pymysql = ImportAdaptor("pymysql", "mysql")


__all__ = [
    "sqlalchemy",
    "psycopg2",
    "asyncpg",
    "boto3",
    "moto",
    "sqlparse",
    "pymongo",
    "redis",
    "pymysql",
]
