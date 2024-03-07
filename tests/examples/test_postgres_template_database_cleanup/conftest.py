import os

from pytest_mock_resources import create_postgres_fixture

should_clean = bool(os.environ.get("CLEAN", False))
pg = create_postgres_fixture(session=True, cleanup_databases=should_clean)
