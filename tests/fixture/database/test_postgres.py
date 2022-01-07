from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_postgres_fixture

Base = declarative_base()


class Thing(Base):
    __tablename__ = "thing"

    id = Column(Integer, autoincrement=True, primary_key=True)


createdb_template_pg = create_postgres_fixture(Base, createdb_template="template0", session=True)


def test_createdb_template(createdb_template_pg):
    """Assert successful usage of a fixture which sets the `createdb_template` argument."""
    thing = Thing(id=1)
    createdb_template_pg.add(thing)
    createdb_template_pg.commit()
