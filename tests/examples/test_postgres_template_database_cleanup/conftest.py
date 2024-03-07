import os

import pytest

from pytest_mock_resources import create_postgres_fixture, PostgresConfig

should_clean = bool(os.environ.get("CLEAN", False))
port = int(os.environ["PORT"])


@pytest.fixture(scope="session")
def pmr_postgres_config():
    return PostgresConfig(port=port, ci_port=port)


pg = create_postgres_fixture(session=True, cleanup_databases=should_clean)
