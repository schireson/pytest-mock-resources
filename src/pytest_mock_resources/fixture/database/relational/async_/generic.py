import abc
import asyncio
import fnmatch

import attr
import six
from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, DeclarativeMeta
from sqlalchemy.sql.ddl import CreateSchema
from sqlalchemy.sql.schema import Table


@six.add_metaclass(abc.ABCMeta)
class AbstractAction(object):
    @abc.abstractmethod
    def run(self, engine_manager):
        """Run an action on a database via the passed-in engine_manager instance."""


class Rows(AbstractAction):
    def __init__(self, *rows):
        self.rows = rows

    async def run(self, engine_manager):
        rows = self._get_stateless_rows(self.rows)

        metadatas = self._get_metadatas(rows)

        for metadata in metadatas:
            await engine_manager.create_ddl(metadata)

        await self._create_rows(engine_manager.engine, rows)

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
    async def _create_rows(engine, rows):
        async_session = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            async with session.begin():
                session.add_all(rows)


class Statements(AbstractAction):
    def __init__(self, *statements):
        self.statements = statements

    async def run(self, engine_manager):
        async with engine_manager.engine.begin() as conn:
            for statement in self.statements:
                if isinstance(statement, str):
                    statement = text(statement)
                await conn.execute(statement)


@attr.s
class EngineManager(object):
    engine = attr.ib()
    ordered_actions = attr.ib(default=attr.Factory(tuple))
    tables = attr.ib(default=None, converter=attr.converters.optional(tuple))
    session = attr.ib(default=False)
    default_schema = attr.ib(default=None)

    _ddl_created = False

    async def _run_actions(self):
        BaseType = type(declarative_base())

        for action in self.ordered_actions:
            if isinstance(action, MetaData):
                await self.create_ddl(action)
            elif isinstance(action, BaseType):
                await self.create_ddl(action.metadata)
            elif isinstance(action, AbstractAction):
                await action.run(self)
            elif callable(action):
                await self._execute_function(action)
            else:
                raise ValueError(
                    "create_fixture function takes in sqlalchemy.MetaData or actions as inputs only."
                )

    async def _create_schemas(self, metadata):
        if self._ddl_created:
            return

        all_schemas = {table.schema for table in metadata.tables.values() if table.schema}

        async with self.engine.begin() as conn:
            for schema in all_schemas:
                if self.default_schema == schema:
                    continue

                statement = CreateSchema(schema, quote=True)
                await conn.execute(statement)

    async def _create_tables(self, metadata):
        if not self.tables:
            async with self.engine.begin() as conn:
                await conn.run_sync(metadata.create_all)
            return

        table_objects = {
            table_object
            for table in self.tables
            for table_object in identify_matching_tables(metadata, table)
        }

        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all, tables=list(table_objects))

    async def _execute_function(self, fn):
        async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            async with session.begin():
                await fn(session)

    async def create_ddl(self, metadata):
        await self._create_schemas(metadata)
        await self._create_tables(metadata)
        self._ddl_created = True

    async def _manage(self, session=None):
        try:
            await self._run_actions()

            if session:
                if isinstance(session, sessionmaker):
                    async_session = sessionmaker(
                        self.engine, expire_on_commit=False, class_=AsyncSession
                    )
                    async with async_session() as _session:
                        yield _session
                else:
                    yield session
            else:
                yield self.engine
        finally:
            pass

    def manage(self, session=None):
        async def _get_engine():
            engine = await self._manage(session).__anext__()
            return engine
        loop = asyncio.get_event_loop()
        yield loop.run_until_complete(_get_engine())


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