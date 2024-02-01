from typing import Optional

import sqlalchemy
import sqlalchemy.engine.url
from sqlalchemy.schema import MetaData

from pytest_mock_resources.compat.import_ import ImportAdaptor

version = getattr(sqlalchemy, "__version__", "")


if version.startswith("1.4") or version.startswith("2."):
    from sqlalchemy.ext import asyncio
    from sqlalchemy.orm import declarative_base, DeclarativeMeta

    URL = sqlalchemy.engine.url.URL.create

    select = sqlalchemy.select
else:
    from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

    URL = sqlalchemy.engine.url.URL  # type: ignore[assignment]

    asyncio = ImportAdaptor(
        "SQLAlchemy",
        "SQLAlchemy >= 1.4",
        fail_message="Cannot use sqlalchemy async features with SQLAlchemy < 1.4.\n",
    )

    def _select(*args, **kwargs):
        return sqlalchemy.select(list(args), **kwargs)

    select = _select


def extract_model_base_metadata(base) -> Optional[sqlalchemy.MetaData]:
    metadata = getattr(base, "metadata", None)
    if isinstance(metadata, MetaData):
        return metadata

    return None


__all__ = [
    "asyncio",
    "declarative_base",
    "DeclarativeMeta",
    "URL",
    "select",
    "version",
]
