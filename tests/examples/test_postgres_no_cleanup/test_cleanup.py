from sqlalchemy import Column, String, text

from pytest_mock_resources import create_postgres_fixture, Rows
from pytest_mock_resources.compat.sqlalchemy import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    name = Column(String, primary_key=True)


rows = Rows(User(name="Harold"), User(name="Gump"))


pg_no_clean = create_postgres_fixture(Base, rows, session=True, cleanup_database=False)


non_cleaned_database_name = None


def test_not_to_be_cleaned_up(pg_no_clean):
    global non_cleaned_database_name
    non_cleaned_database_name = pg_no_clean.pmr_credentials.database

    names = [u.name for u in pg_no_clean.query(User).all()]
    assert names == ["Harold", "Gump"]

    names = pg_no_clean.execute(text("SELECT datname FROM pg_database")).all()
    unique_names = {name for (name,) in names}
    assert non_cleaned_database_name in unique_names


def test_database_is_not_cleaned_up(pg_no_clean):
    global non_cleaned_database_name

    assert non_cleaned_database_name is not None

    assert non_cleaned_database_name != pg_no_clean.pmr_credentials.database

    names = pg_no_clean.execute(text("SELECT datname FROM pg_database")).all()
    unique_names = {name for (name,) in names}
    assert non_cleaned_database_name in unique_names
