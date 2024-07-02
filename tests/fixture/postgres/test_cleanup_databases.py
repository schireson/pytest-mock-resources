from sqlalchemy import Column, String, text

from pytest_mock_resources import create_postgres_fixture, Rows
from pytest_mock_resources.compat.sqlalchemy import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    name = Column(String, primary_key=True)


rows = Rows(User(name="Harold"), User(name="Gump"))


pg_clean = create_postgres_fixture(Base, rows, session=True, cleanup_databases=True)


def test_to_be_cleaned_up(pg_clean):
    database_name = pg_clean.pmr_credentials.database

    names = [u.name for u in pg_clean.query(User).all()]
    assert names == ["Harold", "Gump"]

    names = pg_clean.execute(text("SELECT datname FROM pg_database")).all()
    unique_names = {name for (name,) in names}
    assert database_name in unique_names
