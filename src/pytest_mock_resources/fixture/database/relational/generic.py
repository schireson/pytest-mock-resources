import abc

import six
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.ddl import CreateSchema
from sqlalchemy.sql.schema import Table

from pytest_mock_resources.compat import functools


@six.add_metaclass(abc.ABCMeta)
class AbstractAction(object):
    @abc.abstractmethod
    def run(self, engine, tables):
        """Run an action on a database via the passed-in engine.

        Args:
            engine (sqlalchemy.engine.Engine)
        """


class Rows(AbstractAction):
    def __init__(self, *rows):
        self.rows = rows

    def run(self, engine, tables, default_schema=None):
        rows = self._get_stateless_rows(self.rows)

        metadatas = self._get_metadatas(rows)

        for metadata in metadatas:
            _create_ddl(engine, metadata, tables, default_schema=default_schema)

        self._create_rows(engine, rows)

    @staticmethod
    def _get_stateless_rows(rows):
        """Create rows that aren't associated with any other SQLAlchemy session.
        """
        stateless_rows = []
        for row in rows:
            row_args = row.__dict__
            row_args.pop("_sa_instance_state", None)

            stateless_row = type(row)(**row_args)

            stateless_rows.append(stateless_row)
        return stateless_rows

    @staticmethod
    def _get_metadatas(rows):
        return {row.metadata for row in rows}

    @staticmethod
    def _create_rows(engine, rows):
        Session = sessionmaker(bind=engine)
        session = Session()

        session.add_all(rows)

        session.commit()
        session.close()


class Statements(AbstractAction):
    def __init__(self, *statements):
        self.statements = statements

    def run(self, engine, tables, default_schema=None):
        for statement in self.statements:
            engine.execute(statement)


def _run_actions(engine, ordered_actions, tables=None, default_schema=None):
    BaseType = type(declarative_base())
    for action in ordered_actions:
        if isinstance(action, MetaData):
            _create_ddl(engine, action, tables, default_schema=default_schema)
        elif isinstance(action, BaseType):
            _create_ddl(engine, action.metadata, tables, default_schema=default_schema)
        elif isinstance(action, AbstractAction):
            action.run(engine, tables, default_schema=default_schema)
        elif callable(action):
            _execute_function(engine, action)
        else:
            raise ValueError(
                "create_fixture function takes in sqlalchemy.MetaData or actions as inputs only."
            )


def manage_engine(engine, ordered_actions, tables=None, session=False, default_schema=None):
    try:
        _run_actions(engine, ordered_actions, tables=tables, default_schema=default_schema)

        if session:
            if isinstance(session, sessionmaker):
                session_factory = session
            else:
                session_factory = sessionmaker(bind=engine)

            Session = scoped_session(session_factory)
            session = Session(bind=engine)
            yield session
            session.close()
        else:
            yield engine
    finally:
        engine.dispose()


def _create_ddl(engine, metadata, tables=None, default_schema=None):
    _create_schemas(engine, metadata, default_schema=default_schema)
    _create_tables(engine, metadata, tables=tables)


@functools.lru_cache()
def _create_schemas(engine, metadata, default_schema=None):
    all_schemas = {table.schema for table in metadata.tables.values() if table.schema}

    for schema in all_schemas:
        if default_schema == schema:
            continue

        statement = CreateSchema(schema, quote=True)
        engine.execute(statement)


def _create_tables(engine, metadata, tables):
    if not tables:
        metadata.create_all(engine)
        return

    table_objects = set()
    for table in tables:
        if isinstance(table, DeclarativeMeta):
            table_objects.add(table.__table__)
        elif isinstance(table, Table):
            table_objects.add(table)
        else:
            table_name = table

            if table_name not in metadata.tables:
                raise ValueError(
                    'Could not identify table "{}" from: {}'.format(
                        table_name, ", ".join(sorted(metadata.tables.keys()))
                    )
                )

            table = metadata.tables[table_name]
            table_objects.add(table)

    metadata.create_all(engine, tables=list(table_objects))


def _execute_function(engine, fn):
    Session = sessionmaker(bind=engine)
    session = Session()

    fn(session)

    session.commit()
    session.close()
