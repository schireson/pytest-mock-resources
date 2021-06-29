from pytest_mock_resources import create_redshift_fixture
from tests.fixture.database import (
    copy_fn_to_test_create_engine_patch,
    copy_fn_to_test_psycopg2_connect_patch,
    copy_fn_to_test_psycopg2_connect_patch_as_context_manager,
    unload_fn_to_test_create_engine_patch,
    unload_fn_to_test_psycopg2_connect_patch,
    unload_fn_to_test_psycopg2_connect_patch_as_context_manager,
)

redshift = create_redshift_fixture()


def test_copy(redshift):
    copy_fn_to_test_create_engine_patch(redshift)


def test_unload(redshift):
    unload_fn_to_test_create_engine_patch(redshift)


def test_copy_with_psycopg2(redshift):
    config = redshift.pmr_credentials.as_psycopg2_kwargs()
    copy_fn_to_test_psycopg2_connect_patch(config)


def test_copy_with_psycopg2_as_context_manager(redshift):
    config = redshift.pmr_credentials.as_psycopg2_kwargs()
    copy_fn_to_test_psycopg2_connect_patch_as_context_manager(config)


def test_unload_with_psycopg2(redshift):
    config = redshift.pmr_credentials.as_psycopg2_kwargs()
    unload_fn_to_test_psycopg2_connect_patch(config)


def test_unload_with_psycopg2_as_context_manager(redshift):
    config = redshift.pmr_credentials.as_psycopg2_kwargs()
    unload_fn_to_test_psycopg2_connect_patch_as_context_manager(config)
