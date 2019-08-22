from typing import Any

import pytest
from pyhive import hive
from sqlalchemy import Column, create_engine, INT, schema, String
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base

from pytest_mock_resources import create_presto_fixture

presto = create_presto_fixture()

Base: Any = declarative_base()


class Table(Base):
    __tablename__ = "test_sqla"
    __table_args__ = {"schema": "default"}

    foo = Column(INT, primary_key=True)
    bar = Column(String)


@compiles(schema.PrimaryKeyConstraint)
def visit_primary_key_constraint(self, constraint):
    return ""


@compiles(schema.CreateColumn)
def compile(element, compiler, **kw):
    column = element.element

    text = "%s %s" % (column.name, compiler.type_compiler.process(column.type))

    return text


def test_presto_fixture(presto):
    cursor = presto.cursor()
    cursor.execute("SELECT 1")

    assert cursor.fetchone()[0] == 1


def test_presto_show_session(presto):
    cursor = presto.cursor()
    cursor.execute("SHOW SESSION")


@pytest.mark.skip
def test_presto_create_table(presto):
    cursor = hive.connect("localhost").cursor()
    cursor.execute("CREATE TABLE test (foo INT, bar STRING)")
    cursor.execute("LOAD DATA LOCAL INPATH '/tmp/inputs/test.csv' OVERWRITE INTO TABLE test")

    cursor = presto.cursor()
    cursor.execute("SELECT COUNT(*) FROM default.test")
    assert cursor.fetchone()[0] == 3


@pytest.mark.skip
def test_presto_create_table_sqlalchemy(presto):
    # frequently run into this error here, but eventually it goes away
    # maybe this is because the hive server is not yet ready?
    # thrift.transport.TTransport.TTransportException: TSocket read 0 bytes
    engine = create_engine("hive://localhost:10000/default")
    Base.metadata.create_all(engine)

    engine.execute("LOAD DATA LOCAL INPATH '/tmp/inputs/test.csv' OVERWRITE INTO TABLE test_sqla")

    result_proxy = engine.execute("SELECT COUNT(*) FROM test_sqla")
    assert list(result_proxy)[0][0] == 3
