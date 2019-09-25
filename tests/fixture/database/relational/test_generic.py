import pytest
import sqlalchemy
from sqlalchemy import Column, Integer, SmallInteger, Unicode
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from pytest_mock_resources import create_postgres_fixture, create_sqlite_fixture, Rows

Base = declarative_base()


class Thing(Base):  # type: ignore
    __tablename__ = "thing"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(5), nullable=False)


class Other(Base):  # type: ignore
    __tablename__ = "other"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(5), nullable=False)


class Other2(Base):  # type: ignore
    __tablename__ = "other"
    __table_args__ = {"schema": "other"}

    id = Column(Integer, autoincrement=True, primary_key=True)


sqlite_model = create_sqlite_fixture(Base, tables=[Thing])
sqlite_table = create_sqlite_fixture(Base, tables=[Thing.__table__])
sqlite_name_implicit_schema = create_sqlite_fixture(Base, tables=["thing"])
sqlite_name_explicit_schema = create_sqlite_fixture(Base, tables=["other.other"])
sqlite_name_bad_table = create_sqlite_fixture(Base, tables=["foo"])
sqlite_duplicate = create_sqlite_fixture(
    Base, tables=[Thing, Other2.__table__, "thing", "other.other"]
)


class TestTablesArg:
    def test_model_object(self, sqlite_model):
        sqlite_model.execute("select * from thing")
        with pytest.raises(sqlalchemy.exc.OperationalError):
            sqlite_model.execute("select * from other.other")

    def test_table_object(self, sqlite_table):
        sqlite_table.execute("select * from thing")
        with pytest.raises(sqlalchemy.exc.OperationalError):
            sqlite_table.execute("select * from other.other")

    def test_table_name_implicit_schema(self, sqlite_name_implicit_schema):
        sqlite_name_implicit_schema.execute("select * from thing")
        with pytest.raises(sqlalchemy.exc.OperationalError):
            sqlite_name_implicit_schema.execute("select * from other.other")

    def test_table_name_explicit_schema(self, sqlite_name_explicit_schema):
        sqlite_name_explicit_schema.execute("select * from other.other")
        with pytest.raises(sqlalchemy.exc.OperationalError):
            sqlite_name_explicit_schema.execute("select * from public.other")

    @pytest.mark.xfail(strict=True, raises=ValueError)
    def test_table_name_bad_name(self, sqlite_name_bad_table):
        pass

    def test_table_duplicate(self, sqlite_duplicate):
        sqlite_duplicate.execute("select * from thing")
        sqlite_duplicate.execute("select * from other.other")
        with pytest.raises(sqlalchemy.exc.OperationalError):
            sqlite_duplicate.execute("select * from public.other")


PGBase = declarative_base()


class Quarter(PGBase):  # type: ignore
    __tablename__ = "quarter"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    year = Column(SmallInteger, nullable=False)
    quarter = Column(SmallInteger, nullable=False)


class Report(PGBase):  # type: ignore
    __tablename__ = "report"

    id = Column(Integer, primary_key=True)


pg_implicit_schema = create_postgres_fixture(PGBase, tables=["report"])
pg_explicit_schema = create_postgres_fixture(PGBase, tables=["public.quarter"])


class TestPg:
    @pytest.mark.postgres
    def test_implicit_schema(self, pg_implicit_schema):
        pg_implicit_schema.execute("select * from report")
        with pytest.raises(sqlalchemy.exc.ProgrammingError):
            pg_implicit_schema.execute("select * from public.quarter")

    @pytest.mark.postgres
    def test_explicit_schema(self, pg_explicit_schema):
        pg_explicit_schema.execute("select * from quarter")
        with pytest.raises(sqlalchemy.exc.ProgrammingError):
            pg_explicit_schema.execute("select * from report")


rows = Rows(Quarter(id=1, year=1, quarter=1))
sqlite = create_sqlite_fixture(PGBase, rows, session=True)
sqlite2 = create_sqlite_fixture(PGBase, rows, session=sessionmaker(autocommit=True))
pg_session = create_postgres_fixture(
    PGBase, rows, session=True, tables=["report", "public.quarter"]
)


class TestSessionArg:
    def test_session(self, sqlite):
        result = sqlite.query(Quarter).one()
        assert result.id == 1

        sqlite.execute("INSERT INTO report (id) VALUES (1)")

        sqlite.rollback()
        result = sqlite.query(Report).all()
        assert len(result) == 0

    def test_session2(self, sqlite2):
        sqlite2.execute("INSERT INTO report (id) VALUES (1)")
        sqlite2.rollback()
        result = sqlite2.query(Report).all()
        assert len(result) == 1

    @pytest.mark.postgres
    def test_session_pg(self, pg_session):
        result = pg_session.query(Quarter).one()
        assert result.id == 1
