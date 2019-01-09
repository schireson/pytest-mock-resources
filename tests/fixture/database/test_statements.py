from pytest_mock_resources import create_postgres_fixture, Statements

statements = Statements("CREATE VIEW cool_view as select 3", "CREATE VIEW cool_view_2 as select 1")


postgres_statements = create_postgres_fixture(ordered_actions=[statements])


def test_statements(postgres_statements):
    execute = postgres_statements.execute(
        "SELECT table_name FROM INFORMATION_SCHEMA.views WHERE table_name in ('cool_view', 'cool_view_2')"
    )

    result = [row[0] for row in execute]
    assert ["cool_view", "cool_view_2"] == result
