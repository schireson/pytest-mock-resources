import sqlalchemy
import sqlalchemy.engine.url

version = sqlalchemy.__version__

if version.startswith("1.4") or version.startswith("2."):
    from sqlalchemy.ext import asyncio
    from sqlalchemy.orm import declarative_base, DeclarativeMeta

    URL = sqlalchemy.engine.url.URL.create

    select = sqlalchemy.select
else:
    from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

    URL = sqlalchemy.engine.url.URL

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
