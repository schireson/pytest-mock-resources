from typing import Union

from sqlalchemy.sql.base import Executable

from pytest_mock_resources.compat import sqlparse
from pytest_mock_resources.patch.redshift.mock_s3_copy import execute_mock_s3_copy_command, strip
from pytest_mock_resources.patch.redshift.mock_s3_unload import execute_mock_s3_unload_command


def substitute_execute_with_custom_execute(engine):
    """Substitute the default execute method with a custom execute for copy and unload command."""
    default_execute = engine.execute

    def custom_execute(statement: Union[Executable, str], *args, **kwargs):
        if isinstance(statement, Executable):
            return default_execute(statement, *args, **kwargs)

        # The statement is assumed to be a string at this point.
        normalized_statement = strip(statement).lower()
        if normalized_statement.startswith("copy"):
            return execute_mock_s3_copy_command(statement, engine)
        elif normalized_statement.startswith("unload"):
            return execute_mock_s3_unload_command(statement, engine)

        return default_execute(statement, *args, **kwargs)

    def handle_multiple_statements(statement: Union[Executable, str], *args, **kwargs):
        """Split statement into individual sql statements and execute.

        Splits multiple statements by ';' and executes each.
        NOTE: Only the result of the last statements is returned.
        """
        statements_list = parse_multiple_statements(statement)
        result = None
        for statement in statements_list:
            result = custom_execute(statement, *args, **kwargs)

        return result

    # Now each statement is handled as if it contains multiple sql statements
    engine.execute = handle_multiple_statements
    return engine


def parse_multiple_statements(statement: Union[Executable, str]):
    """Split the given sql statement into a list of individual sql statements."""
    # Ignore SQLAlchemy Text Objects.
    if isinstance(statement, Executable):
        return [statement]

    # Preprocess input statement
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
