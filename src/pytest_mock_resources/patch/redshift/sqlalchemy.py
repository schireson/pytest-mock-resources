from typing import Union

from sqlalchemy import event
from sqlalchemy.sql.base import Executable

from pytest_mock_resources.compat import sqlparse
from pytest_mock_resources.patch.redshift.mock_s3_copy import mock_s3_copy_command, strip
from pytest_mock_resources.patch.redshift.mock_s3_unload import mock_s3_unload_command


def register_redshift_behavior(engine):
    """Substitute the default execute method with a custom execute for copy and unload command."""

    event.listen(engine, "before_execute", receive_before_execute, retval=True)
    event.listen(engine, "before_cursor_execute", receive_before_cursor_execute, retval=True)


def receive_before_execute(
    conn, clauseelement: Union[Executable, str], multiparams, params, execution_options=None
):
    """Handle the `before_execute` event.

    Specifically, this only needs to handle the parsing of multiple statements into
    individual cursor executions. Only the final statement's return value will be
    returned.
    """
    if isinstance(clauseelement, Executable):
        return clauseelement, multiparams, params

    *statements, final_statement = parse_multiple_statements(clauseelement)

    cursor = conn.connection.cursor()
    for statement in statements:
        cursor.execute(statement, *multiparams, **params)

    return final_statement, multiparams, params


def receive_before_cursor_execute(_, cursor, statement: str, parameters, context, executemany):
    """Handle the `before_cursor_execute` event.

    This is where we add support for custom features such as redshift COPY/UNLOAD because
    the query has already been rendered (into a string) at this point.

    Notably, COPY/UNLOAD need to perform extra non-sql behavior and potentially execute
    more than a single query and the interface requires that we return a query. Thus,
    we return a no-op query to be executed by sqlalchemy for certain kinds of supported
    extra features.
    """
    normalized_statement = strip(statement).lower()
    if normalized_statement.startswith("unload"):
        mock_s3_unload_command(statement, cursor)
        return "SELECT 1", {}

    if normalized_statement.startswith("copy"):
        mock_s3_copy_command(statement, cursor)
        context.should_autocommit = True
        return "SELECT 1", {}
    return statement, parameters


def parse_multiple_statements(statement: str):
    """Split the given sql statement into a list of individual sql statements."""
    processed_statement = _preprocess(statement)
    statements_list = [str(statement) for statement in sqlparse.split(processed_statement)]

    return statements_list


def _preprocess(statement: str):
    """Preprocess the input statement."""
    statement = statement.strip()
    # Replace any occourance of " with '.
    statement = statement.replace('"', "'")
    if statement[-1] != ";":
        statement += ";"
    return statement
