import pytest

from pytest_mock_resources import (
    create_postgres_fixture,
    create_redshift_fixture,
    create_sqlite_fixture,
    Statements,
)

statements = Statements("CREATE VIEW cool_view as select 3", "CREATE VIEW cool_view_2 as select 1")
postgres = create_postgres_fixture(statements)
sqlite = create_sqlite_fixture(statements)


@pytest.mark.postgres
def test_statements(postgres):
    execute = postgres.execute(
        """
        SELECT table_name
        FROM INFORMATION_SCHEMA.views
        WHERE table_name in ('cool_view', 'cool_view_2')
        ORDER BY table_name
        """
    )

    result = [row[0] for row in execute]
    assert ["cool_view", "cool_view_2"] == result


statements = Statements(
    """
    CREATE TABLE account(
     user_id serial PRIMARY KEY,
     username VARCHAR (50) UNIQUE NOT NULL,
     password VARCHAR (50) NOT NULL
    );
    INSERT INTO account VALUES (1, 'user1', 'password1')
    """
)
redshift = create_redshift_fixture(statements)


@pytest.mark.redshift
def test_multi_statement_statements(redshift):
    execute = redshift.execute("SELECT password FROM account")

    result = sorted([row[0] for row in execute])
    assert ["password1"] == result
