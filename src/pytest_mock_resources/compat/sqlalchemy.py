import sqlalchemy
import sqlalchemy.engine.url

from pytest_mock_resources.compat.import_ import ImportAdaptor

version = getattr(sqlalchemy, "__version__", "")

if version.startswith("1.4") or version.startswith("2."):
    from sqlalchemy.ext import asyncio
    from sqlalchemy.orm import declarative_base, DeclarativeMeta

    URL = sqlalchemy.engine.url.URL.create

    select = sqlalchemy.select
else:
    from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

    URL = sqlalchemy.engine.url.URL

    asyncio = ImportAdaptor(
        "SQLAlchemy",
        "SQLAlchemy >= 1.4",
        fail_message="Cannot use sqlalchemy async features with SQLAlchemy < 1.4.\n",
    )

    def _select(*args, **kwargs):
        return sqlalchemy.select(list(args), **kwargs)

    select = _select


__all__ = [
    "asyncio",
    "declarative_base",
    "DeclarativeMeta",
    "URL",
    "select",
    "version",
]
