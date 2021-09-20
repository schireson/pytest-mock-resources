import sqlalchemy.engine.url

from pytest_mock_resources.compat.import_ import ImportAdaptor

try:
    from sqlalchemy.ext import asyncio  # type: ignore
except ImportError:
    asyncio = ImportAdaptor(
        "SQLAlchemy",
        "SQLAlchemy >= 1.4",
        fail_message="Cannot use sqlalchemy async features with SQLAlchemy < 1.4.\n",
    )

URL = sqlalchemy.engine.url.URL
try:
    # Attempt to use the newly recommended `URL.create` method when available
    URL = URL.create  # type: ignore
except AttributeError:
    # But if it's not available, the top-level contructor should still exist,
    # as this is the only available option in sqlalchemy<1.4 versions.
    pass
