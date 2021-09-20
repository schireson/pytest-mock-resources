from pytest_mock_resources.compat.import_ import ImportAdaptor

try:
    from sqlalchemy.ext import asyncio as asyncio  # type: ignore
except ImportError:
    asyncio = ImportAdaptor(  # type: ignore
        "SQLAlchemy",
        "SQLAlchemy >= 1.4",
        fail_message="Cannot use sqlalchemy async features with SQLAlchemy < 1.4.\n",
    )
