import abc

import attr
import six
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.ddl import CreateSchema
from sqlalchemy.sql.schema import Table


@six.add_metaclass(abc.ABCMeta)
class AbstractAction(object):
    @abc.abstractmethod
    def run(self, engine_manager):
        """Run an action on a database via the passed-in engine_manager instance.
        """


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

    def run(self, engine_manager):
        for statement in self.statements:
            engine_manager.engine.execute(statement)


@attr.s
class EngineManager(object):
    engine = attr.ib()
    ordered_actions = attr.ib(default=attr.Factory(tuple))
    tables = attr.ib(default=None, converter=attr.converters.optional(tuple))
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

        table_objects = set()
        for table in self.tables:
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
