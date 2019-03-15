from pytest_mock_resources import (
    create_redshift_fixture,
    patch_create_engine,
    patch_psycopg2_connect,
    PG_HOST,
    PG_PORT,
)
from tests.fixture.database import (
    copy_fn_to_test_create_engine_patch,
    copy_fn_to_test_psycopg2_connect_patch,
    copy_fn_to_test_psycopg2_connect_patch_as_context_manager,
    unload_fn_to_test_create_engine_patch,
    unload_fn_to_test_psycopg2_connect_patch,
    unload_fn_to_test_psycopg2_connect_patch_as_context_manager,
)

redshift = create_redshift_fixture()
PG_HOST = PG_HOST
PG_POST = PG_PORT


@patch_create_engine(path="tests.fixture.database.create_engine")
def test_copy(redshift):
    copy_fn_to_test_create_engine_patch(redshift)


@patch_create_engine(path="tests.fixture.database.create_engine")
def test_unload(redshift):
    unload_fn_to_test_create_engine_patch(redshift)


@patch_psycopg2_connect(path="tests.fixture.database.psycopg2.connect")
def test_copy_with_psycopg2(redshift, PG_HOST, PG_PORT):
    config = {
        "dbname": redshift.database,
        "user": "user",
        "password": "password",
        "host": PG_HOST,
        "port": PG_PORT,
    }

    copy_fn_to_test_psycopg2_connect_patch(config)


@patch_psycopg2_connect(path="tests.fixture.database.psycopg2.connect")
def test_copy_with_psycopg2_as_context_manager(redshift, PG_HOST, PG_PORT):
    config = {
        "dbname": redshift.database,
        "user": "user",
        "password": "password",
        "host": PG_HOST,
        "port": PG_PORT,
    }

    copy_fn_to_test_psycopg2_connect_patch_as_context_manager(config)


@patch_psycopg2_connect(path="tests.fixture.database.psycopg2.connect")
def test_unload_with_psycopg2(redshift, PG_HOST, PG_PORT):
    config = {
        "dbname": redshift.database,
        "user": "user",
        "password": "password",
        "host": PG_HOST,
        "port": PG_PORT,
    }

    unload_fn_to_test_psycopg2_connect_patch(config)


@patch_psycopg2_connect(path="tests.fixture.database.psycopg2.connect")
def test_unload_with_psycopg2_as_context_manager(redshift, PG_HOST, PG_PORT):
    config = {
        "dbname": redshift.database,
        "user": "user",
        "password": "password",
        "host": PG_HOST,
        "port": PG_PORT,
    }

    unload_fn_to_test_psycopg2_connect_patch_as_context_manager(config)
