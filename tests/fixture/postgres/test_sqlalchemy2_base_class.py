from tests import is_at_least_sqlalchemy2

if is_at_least_sqlalchemy2:
    from sqlalchemy import Column, Integer
    from sqlalchemy.orm import DeclarativeBase

    from pytest_mock_resources import create_postgres_fixture

    class Base(DeclarativeBase):
        ...

    class Thing(Base):
        __tablename__ = "thing"

        id = Column(Integer, autoincrement=True, primary_key=True)

    pg = create_postgres_fixture(Base, session=True)

    def test_creates_ddl(pg):
        rows = pg.query(Thing).all()
        assert len(rows) == 0
