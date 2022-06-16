import abc


class AbstractAction(metaclass=abc.ABCMeta):
    static_safe = False

    @abc.abstractmethod
    def run(self, conn):
        """Run an action on a database via the passed-in engine_manager instance."""


class Rows(AbstractAction):
    static_safe = True

    def __init__(self, *rows):
        self.rows = rows

    def run(self, conn):
        from sqlalchemy.orm import Session

        rows = self._get_stateless_rows(self.rows)

        if isinstance(conn, Session):
            session = conn
        else:
            session = Session(bind=conn)

        session.add_all(rows)
        session.commit()

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
    static_safe = False

    def __init__(self, *statements):
        self.statements = statements

    def run(self, conn):
        from sqlalchemy import text

        for statement in self.statements:
            if isinstance(statement, str):
                statement = text(statement)
            conn.execute(statement)


class StaticStatements(Statements):
    """A discriminator for statements which are safe to execute exactly once."""

    static_safe = True
