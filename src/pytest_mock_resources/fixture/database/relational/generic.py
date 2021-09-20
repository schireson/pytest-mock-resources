import abc
import fnmatch
from typing import Tuple

import attr
import six
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.ddl import CreateSchema
from sqlalchemy.sql.schema import Table

from pytest_mock_resources import compat


@six.add_metaclass(abc.ABCMeta)
class AbstractAction(object):
    @abc.abstractmethod
    def run(self, engine_manager):
        """Run an action on a database via the passed-in engine_manager instance."""


class Rows(AbstractAction):
    def __init__(self, *rows):
        self.rows = rows

    def run(self, engine_manager):
        rows = self._get_stateless_rows(self.rows)

        metadatas = self._get_metadatas(rows)

        for metadata in metadatas:
            engine_manager.create_ddl(metadata)

        self._create_rows(engine_manager.engine, rows)

    @staticmethod
    def _get_stateless_rows(rows):
        """Create rows that aren't associated with any other SQLAlchemy session."""
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

    def run(self, engine_manager):
        for statement in self.statements:
            engine_manager.engine.execute(statement)


@attr.s
class EngineManager(object):
    engine = attr.ib()
    ordered_actions = attr.ib(default=attr.Factory(tuple))
    tables: Tuple = attr.ib(default=None, converter=attr.converters.optional(tuple))
    session = attr.ib(default=False)
    default_schema = attr.ib(default=None)

    _ddl_created = False

    def _run_actions(self):
        BaseType = type(declarative_base())

        for action in self.ordered_actions:
            if isinstance(action, MetaData):
                self.create_ddl(action)
            elif isinstance(action, BaseType):
                self.create_ddl(action.metadata)
            elif isinstance(action, AbstractAction):
                action.run(self)
            elif callable(action):
                self._execute_function(action)
            else:
                raise ValueError(
                    "create_fixture function takes in sqlalchemy.MetaData or actions as inputs only."
                )

    def _create_schemas(self, metadata):
        if self._ddl_created:
            return

        all_schemas = {table.schema for table in metadata.tables.values() if table.schema}

        for schema in all_schemas:
            if self.default_schema == schema:
                continue

            statement = CreateSchema(schema, quote=True)
            self.engine.execute(statement)

    def _create_tables(self, metadata):
        if not self.tables:
            metadata.create_all(self.engine)
            return

        table_objects = {
            table_object
            for table in self.tables
            for table_object in identify_matching_tables(metadata, table)
        }

        metadata.create_all(self.engine, tables=list(table_objects))

    def _execute_function(self, fn):
        Session = sessionmaker(bind=self.engine)
        session = Session()

        fn(session)

        session.commit()
        session.close()

    def create_ddl(self, metadata):
        self._create_schemas(metadata)
        self._create_tables(metadata)
        self._ddl_created = True

    def manage(self, session=None):
        try:
            self._run_actions()

            if session:
                if isinstance(session, sessionmaker):
                    session_factory = session
                else:
                    session_factory = sessionmaker(bind=self.engine)

                Session = scoped_session(session_factory)
                session = Session(bind=self.engine)
                yield session
                session.close()
            else:
                yield self.engine
        finally:
            self.engine.dispose()

    def manage_sync(self, session=None):
        try:
            self._run_actions()

            if session:
                if isinstance(session, sessionmaker):
                    session_factory = session
                else:
                    session_factory = sessionmaker(bind=self.engine)

                Session = scoped_session(session_factory)
                session = Session(bind=self.engine)
                yield session
                session.close()
            else:
                yield self.engine
        finally:
            self.engine.dispose()

    async def manage_async(self, session=None):
        try:
            self._run_actions()

            async_engine = self._get_async_engine()

            if session:
                if isinstance(session, sessionmaker):
                    session_factory = session
                else:
                    session_factory = sessionmaker(
                        async_engine,
                        expire_on_commit=False,
                        class_=compat.sqlalchemy.asyncio.AsyncSession,
                    )
                async with session_factory() as session:
                    yield session
            else:
                yield async_engine
        finally:
            self.engine.dispose()

    def _get_async_engine(self, isolation_level=None):
        url = compat.sqlalchemy.URL(
            drivername="postgresql+asyncpg",
            username=self.engine.pmr_credentials.username,
            password=self.engine.pmr_credentials.password,
            host=self.engine.pmr_credentials.host,
            port=self.engine.pmr_credentials.port,
            database=self.engine.pmr_credentials.database,
            query=dict(ssl="disable"),
        )
        options = {}
        if isolation_level:
            options["isolation_level"] = isolation_level
        return compat.sqlalchemy.asyncio.create_async_engine(url, **options)


def identify_matching_tables(metadata, table_specifier):
    if isinstance(table_specifier, DeclarativeMeta):
        return [table_specifier.__table__]

    if isinstance(table_specifier, Table):
        return [table_specifier]

    tables = [
        table
        for table_name, table in metadata.tables.items()
        if fnmatch.fnmatch(table_name, table_specifier)
    ]

    if tables:
        return tables

    table_names = ", ".join(sorted(metadata.tables.keys()))
    raise ValueError(
        'Could not identify any tables matching "{}" from: {}'.format(table_specifier, table_names)
    )
