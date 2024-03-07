import pytest
from sqlalchemy import Column, select, String, text

from pytest_mock_resources import create_postgres_fixture, Rows
from pytest_mock_resources.compat.sqlalchemy import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    name = Column(String, primary_key=True)


rows = Rows(User(name="Harold"), User(name="Gump"))


pg_clean = create_postgres_fixture(Base, rows, session=True, cleanup_databases=True, async_=True)
pg_no_clean = create_postgres_fixture(Base, rows, session=True, async_=True)


database_name = None
non_cleaned_database_name = None


@pytest.mark.asyncio
async def test_to_be_cleaned_up(pg_clean):
    global database_name
    database_name = (await pg_clean.connection()).engine.url.database

    names = [u[0].name for u in (await pg_clean.execute(select(User))).all()]
    assert names == ["Harold", "Gump"]

    names = (await pg_clean.execute(text("SELECT datname FROM pg_database"))).all()
    unique_names = {name for (name,) in names}
    assert database_name in unique_names


@pytest.mark.order(after="test_to_be_cleaned_up")
@pytest.mark.asyncio
async def test_database_cleaned_up(pg_clean):
    global database_name

    assert database_name is not None

    assert database_name != (await pg_clean.connection()).engine.url.database

    names = (await pg_clean.execute(text("SELECT datname FROM pg_database"))).all()
    unique_names = {name for (name,) in names}
    assert database_name not in unique_names


@pytest.mark.asyncio
async def test_not_to_be_cleaned_up(pg_no_clean):
    global non_cleaned_database_name
    non_cleaned_database_name = (await pg_no_clean.connection()).engine.url.database

    names = [u[0].name for u in (await pg_no_clean.execute(select(User))).all()]
    assert names == ["Harold", "Gump"]

    names = (await pg_no_clean.execute(text("SELECT datname FROM pg_database"))).all()
    unique_names = {name for (name,) in names}
    assert non_cleaned_database_name in unique_names


@pytest.mark.order(after="test_not_to_be_cleaned_up")
@pytest.mark.asyncio
async def test_database_is_not_cleaned_up(pg_no_clean):
    global non_cleaned_database_name

    assert non_cleaned_database_name is not None

    assert non_cleaned_database_name != (await pg_no_clean.connection()).engine.url.database

    names = (await pg_no_clean.execute(text("SELECT datname FROM pg_database"))).all()
    unique_names = {name for (name,) in names}
    assert non_cleaned_database_name in unique_names
