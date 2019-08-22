from pytest_mock_resources import create_presto_fixture

presto = create_presto_fixture()


def test_basic_presto_fixture(presto):
    cursor = presto.cursor()
    cursor.execute("select 1")

    assert cursor.fetchone()[0] == 1
