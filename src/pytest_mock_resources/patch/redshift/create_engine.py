from sqlalchemy import create_engine
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.sql.expression import Insert, Select, Update

from pytest_mock_resources.compat import functools, mock, sqlparse
from pytest_mock_resources.patch.redshift.mock_s3_copy import execute_mock_s3_copy_command, strip
from pytest_mock_resources.patch.redshift.mock_s3_unload import execute_mock_s3_unload_command

SQLALCHEMY_BASES = (Select, Insert, Update, TextClause)


def substitute_execute_with_custom_execute(engine):
    """Substitute the default execute method with a custom execute for copy and unload command."""
    default_execute = engine.execute

    def custom_execute(statement, *args, **kwargs):
        if not isinstance(statement, SQLALCHEMY_BASES) and strip(statement).lower().startswith(
            "copy"
        ):
            return execute_mock_s3_copy_command(statement, engine)
        if not isinstance(statement, SQLALCHEMY_BASES) and strip(statement).lower().startswith(
            "unload"
        ):
            return execute_mock_s3_unload_command(statement, engine)
        return default_execute(statement, *args, **kwargs)

    def handle_multiple_statements(statement, *args, **kwargs):
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


def parse_multiple_statements(statement):
    """Split the given sql statement into a list of individual sql statements."""
    statements_list = []

    # Ignore SQLAlchemy Text Objects.
    if isinstance(statement, SQLALCHEMY_BASES):
        statements_list.append(statement)
        return statements_list

    # Prprocess input statement
    statement = _preprocess(statement)

    statements_list = [str(statement) for statement in sqlparse.split(statement)]

    return statements_list


def _preprocess(statement):
    """Preprocess the input statement."""
    statement = statement.strip()
    # Replace any occourance of " with '.
    statement = statement.replace('"', "'")
    if statement[-1] != ";":
        statement += ";"
    return statement


def patch_create_engine(path):
    """Patch any occourances of sqlalchemy's `create_engine` with function.

    The `path` should be the path to the `create_engine` call you want to patch.
    """

    def _patch_create_engine(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with mock.patch(path, new=mock_create_engine):
                return func(*args, **kwargs)

        return wrapper

    return _patch_create_engine


def mock_create_engine(*args, **kwargs):
    engine = create_engine(*args, **kwargs)
    return substitute_execute_with_custom_execute(engine)
