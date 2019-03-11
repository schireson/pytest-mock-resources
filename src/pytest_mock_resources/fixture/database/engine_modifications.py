from sqlalchemy.sql.elements import TextClause

from pytest_mock_resources.fixture.database.mock_s3_copy import _strip, execute_mock_s3_copy_command
from pytest_mock_resources.fixture.database.mock_s3_unload import execute_mock_s3_unload_command


def substitute_execute_with_custom_execute(redshift):
    """Substitue the default execute method with a custom execute for copy and unload command."""
    default_execute = redshift.execute

    def custom_execute(statement, *args, **kwargs):
        if not isinstance(statement, TextClause) and _strip(statement).lower().startswith("copy"):
            return execute_mock_s3_copy_command(statement, redshift)
        if not isinstance(statement, TextClause) and _strip(statement).lower().startswith("unload"):
            return execute_mock_s3_unload_command(statement, redshift)
        return default_execute(statement, *args, **kwargs)

    redshift.execute = custom_execute
    return redshift
