import fnmatch
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, TypeVar, Union

import sqlalchemy
from sqlalchemy import MetaData, text
from sqlalchemy.orm import scoped_session, Session, sessionmaker
from sqlalchemy.sql.ddl import CreateSchema
from sqlalchemy.sql.schema import Table

from pytest_mock_resources import compat
from pytest_mock_resources.action import AbstractAction, validate_actions
from pytest_mock_resources.credentials import Credentials

log = logging.getLogger(__name__)


class Rows(AbstractAction):
    fixtures = ("mysql", "postgres", "redshift", "sqlite")
    static_safe = True

    def __init__(self, *rows):
        self.rows = rows

    def apply(self, conn):
        rows = self._get_stateless_rows(self.rows)

        if isinstance(conn, Session):
            session = conn
        else:
            session = Session(bind=conn)

        session.add_all(rows)
        commit(session)

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


class Statements(AbstractAction):
    fixtures = ("mysql", "postgres", "redshift", "sqlite")
    static_safe = False

    def __init__(self, *statements):
        self.statements = statements

    def apply(self, conn):
        for statement in self.statements:
            if isinstance(statement, str):
                statement = text(statement)
            conn.execute(statement)


class StaticStatements(Statements):
    """A discriminator for statements which are safe to execute exactly once."""

    static_safe = True


StaticAction = Union[MetaData, compat.sqlalchemy.DeclarativeMeta, Rows, StaticStatements]
Action = Union[MetaData, compat.sqlalchemy.DeclarativeMeta, AbstractAction]
T = TypeVar("T", StaticAction, Action)


@dataclass
class EngineManager:
    dynamic_actions: Iterable[Action] = ()
    tables: Iterable = ()
    session: Union[bool, Session] = False
    static_actions: Iterable[StaticAction] = ()
    actions_share_transaction: Optional[bool] = None

    _ddl_created: Dict[MetaData, bool] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        dynamic_actions: Iterable[Action],
        *,
        fixture: Optional[str] = None,
        tables: Iterable = (),
        session: Union[bool, Session] = False,
        static_actions: Iterable[StaticAction] = (),
    ) -> "EngineManager":
        return cls(
            static_actions=normalize_actions(static_actions, fixture=fixture),
            dynamic_actions=normalize_actions(dynamic_actions, fixture=fixture),
            tables=tables,
            session=session,
        )

    def manage_sync(self, engine):
        try:
            if self.session:
                if isinstance(self.session, sessionmaker):
                    session_factory = self.session
                    session = session_factory(bind=engine)
                elif isinstance(self.session, Session):
                    session = self.session
                else:
                    session_factory = scoped_session(sessionmaker(bind=engine))
                    session = session_factory(bind=engine)

                try:
                    self.run_actions(session)
                    commit(session)

                    if self.actions_share_transaction is False:
                        engine.dispose()

                    Credentials.assign_from_connection(session)
                    yield engine, session
                finally:
                    session.close()
            else:
                with engine.begin() as conn:
                    self.run_actions(conn)
                    commit(conn)

                if self.actions_share_transaction is False:
                    engine.dispose()

                Credentials.assign_from_connection(engine)
                yield engine, engine

        finally:
            engine.dispose()

    async def manage_async(self, engine, session=None):
        from sqlalchemy.ext.asyncio.session import AsyncSession

        try:
            if self.session:
                if isinstance(self.session, (sessionmaker, AsyncSession)):
                    session_factory = self.session
                else:
                    session_factory = sessionmaker(
                        expire_on_commit=False,
                        class_=compat.sqlalchemy.asyncio.AsyncSession,
                    )

                async with session_factory(bind=engine) as session:
                    await session.run_sync(self.run_actions)
                    if not self.actions_share_transaction:
                        await session.commit()
                        await session.close()

                    Credentials.assign_from_connection(engine.sync_engine)
                    yield engine, session
            else:
                async with engine.begin() as conn:
                    await conn.run_sync(self.run_actions)
                    await conn.commit()

                if not self.actions_share_transaction:
                    await engine.dispose()

                Credentials.assign_from_connection(engine.sync_engine)
                yield engine, engine
        finally:
            await engine.dispose()

    def run_actions(self, conn):
        self.run_static_actions(conn)
        self.run_dynamic_actions(conn)

    def run_static_actions(self, conn):
        for action in self.static_actions:
            self.execute_action(conn, action, allow_function=False)

    def run_dynamic_actions(self, conn):
        for action in self.dynamic_actions:
            self.execute_action(conn, action, allow_function=True)

    def _create_schemas(self, conn, metadata):
        if metadata in self._ddl_created:
            return

        all_schemas = {table.schema for table in metadata.tables.values() if table.schema}

        for schema in all_schemas:
            if hasattr(conn, "dialect"):
                dialect = conn.dialect
            else:
                dialect = conn.connection().dialect

            if dialect.default_schema_name == schema:
                continue

            statement = CreateSchema(schema)
            conn.execute(statement)

    def _create_tables(self, conn, metadata):
        if isinstance(conn, Session):
            conn = conn.connection()

        if not self.tables:
            metadata.create_all(conn)
            return

        table_objects = {
            table_object
            for table in self.tables
            for table_object in identify_matching_tables(metadata, table)
        }

        metadata.create_all(conn, tables=list(table_objects))

    def create_ddl(self, conn, metadata):
        self._create_schemas(conn, metadata)
        self._create_tables(conn, metadata)
        self._ddl_created[metadata] = True

    def execute_action(self, conn, action, allow_function=False):
        if isinstance(action, MetaData):
            self.create_ddl(conn, action)
        elif isinstance(action, AbstractAction):
            action.apply(conn)
        elif allow_function and callable(action):
            action(conn)
            commit(conn)


def normalize_actions(
    ordered_actions: Iterable[T], *, fixture: Optional[str] = None
) -> Iterable[T]:
    validate_actions(
        ordered_actions,
        fixture=fixture,
        additional_types=(compat.sqlalchemy.DeclarativeMeta, Callable, MetaData),
    )

    # Keep track of metadata we've seen to ensure it's only added once per
    # instance, regardless of `Row` references.
    unique_metadata: Set[MetaData] = set()
    normalized_actions: List[T] = []
    for action in ordered_actions:
        metadata = compat.sqlalchemy.extract_model_base_metadata(action)
        if metadata:
            normalized_actions.append(metadata)

        elif isinstance(action, Rows):
            new_metadata = {row.metadata for row in action.rows} - unique_metadata
            unique_metadata |= new_metadata
            normalized_actions.extend(list(new_metadata))
            normalized_actions.append(action)

        elif isinstance(action, MetaData):
            if action not in unique_metadata:
                normalized_actions.append(action)
        elif isinstance(action, AbstractAction) or callable(action):
            normalized_actions.append(action)

    return normalized_actions


def bifurcate_actions(ordered_actions):
    static_actions = []
    dynamic_actions = []

    static = True
    for action in ordered_actions:
        static_safe = isinstance(action, MetaData) or (
            isinstance(action, AbstractAction) and action.static_safe
        )

        if static:
            if static_safe:
                static_actions.append(action)
            else:
                static = False
                dynamic_actions.append(action)
        else:
            dynamic_actions.append(action)

    return (static_actions, dynamic_actions)


def identify_matching_tables(metadata, table_specifier):
    if isinstance(table_specifier, compat.sqlalchemy.DeclarativeMeta):
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
        f'Could not identify any tables matching "{table_specifier}" from: {table_names}'
    )


def commit(conn):
    try:
        if isinstance(conn, Session):
            return conn.commit()

        return conn.execute(text("COMMIT"))
    except sqlalchemy.exc.InvalidRequestError:
        # In autocommit mode, we won't be able to commit.
        pass
