from typing import Optional

import sqlalchemy
import sqlalchemy.engine.url
from sqlalchemy.schema import MetaData

version = getattr(sqlalchemy, "__version__", "")


if version.startswith("1.4") or version.startswith("2."):
    from sqlalchemy.orm import declarative_base, DeclarativeMeta

    URL = sqlalchemy.engine.url.URL.create

    select = sqlalchemy.select
else:
    from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

    URL = sqlalchemy.engine.url.URL  # type: ignore[assignment]

    def _select(*args, **kwargs):
        return sqlalchemy.select(list(args), **kwargs)

    select = _select


def extract_model_base_metadata(base) -> Optional[sqlalchemy.MetaData]:
    metadata = getattr(base, "metadata", None)
    if isinstance(metadata, MetaData):
        return metadata

    return None


__all__ = [
    "declarative_base",
    "DeclarativeMeta",
    "URL",
    "select",
    "version",
]
