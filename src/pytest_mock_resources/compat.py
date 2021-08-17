class ImportAdaptor(object):
    __wrapped__ = False

    def __init__(self, package, recommended_extra, fail_message=None, **attrs):
        self.package = package
        self.recommended_extra = recommended_extra
        self.fail_message = fail_message

        for key, value in attrs.items():
            setattr(self, key, value)

    def fail(self):
        if self.fail_message:
            fail_message = self.fail_message
        else:
            fail_message = "Cannot use {recommended_extra} fixtures without {package}. pip install pytest-mock-resources[{recommended_extra}]".format(
                package=self.package, recommended_extra=self.recommended_extra
            )

        raise RuntimeError(fail_message)

    def __getattr__(self, attr):
        self.fail()


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
    redis = ImportAdaptor("redis", "redis")  # type: ignore

try:
    import pymysql
except ImportError:
    pymysql = ImportAdaptor("pymysql", "mysql")  # type: ignore

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
except ImportError:
    fail_message = "Cannot use sqlalchemy async features with SQLAlchemy < 1.4.\n"
    create_async_engine = ImportAdaptor(
        "SQLAlchemy", "SQLAlchemy >= 1.4", fail_message=fail_message
    )
    AsyncSession = ImportAdaptor("SQLAlchemy", "SQLAlchemy >= 1.4", fail_message=fail_message)
