import pytest
import sqlalchemy
from sqlalchemy import Column, Integer, MetaData, SmallInteger, Table, Unicode
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from pytest_mock_resources import create_postgres_fixture, create_sqlite_fixture, Rows
from pytest_mock_resources.fixture.database.relational.generic import identify_matching_tables

Base = declarative_base()


class Thing(Base):
    __tablename__ = "thing"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(5), nullable=False)


class Other(Base):
    __tablename__ = "other"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(5), nullable=False)


class Other2(Base):
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
sqlite_glob = create_sqlite_fixture(Base, tables=["*.other"])


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

    def test_glob(self, sqlite_glob):
        with pytest.raises(sqlalchemy.exc.OperationalError):
            sqlite_glob.execute("select * from thing")

        sqlite_glob.execute("select * from other.other")
        sqlite_glob.execute("select * from public.other")


PGBase = declarative_base()


class Quarter(PGBase):
    __tablename__ = "quarter"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    year = Column(SmallInteger, nullable=False)
    quarter = Column(SmallInteger, nullable=False)


class Report(PGBase):
    __tablename__ = "report"

    id = Column(Integer, primary_key=True)


pg_implicit_schema = create_postgres_fixture(PGBase, tables=["report"])
pg_explicit_schema = create_postgres_fixture(PGBase, tables=["public.quarter"])


class TestPg:
    def test_implicit_schema(self, pg_implicit_schema):
        pg_implicit_schema.execute("select * from report")
        with pytest.raises(sqlalchemy.exc.ProgrammingError):
            pg_implicit_schema.execute("select * from public.quarter")

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

    def test_session_pg(self, pg_session):
        result = pg_session.query(Quarter).one()
        assert result.id == 1


class Test__identify_matching_tables:
    @staticmethod
    def by_tablename(table):
        return table.schema + table.name

    def setup(self):
        self.metadata = metadata = MetaData()
        self.base = declarative_base()

        self.one_foo = Table("foo", metadata, schema="one")
        self.one_foo_bar = Table("foo_bar", metadata, schema="one")
        self.two_foo = Table("foo", metadata, schema="two")
        self.two_far = Table("far", metadata, schema="two")

    def test_no_glob(self):
        result = identify_matching_tables(self.metadata, "one.foo")
        assert sorted(result, key=self.by_tablename) == [self.one_foo]

    def test_glob_table_on_schema(self):
        result = identify_matching_tables(self.metadata, "one.*")
        assert sorted(result, key=self.by_tablename) == [self.one_foo, self.one_foo_bar]

    def test_glob_schema_on_table(self):
        result = identify_matching_tables(self.metadata, "*.foo")
        assert sorted(result, key=self.by_tablename) == [self.one_foo, self.two_foo]

    def test_glob_optional_char(self):
        result = identify_matching_tables(self.metadata, "two.f??")
        assert sorted(result, key=self.by_tablename) == [self.two_far, self.two_foo]
