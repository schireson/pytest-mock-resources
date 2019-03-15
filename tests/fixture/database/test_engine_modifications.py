from pytest_mock_resources import create_redshift_fixture, patch_create_engine
from tests.fixture.database import (
    copy_fn_to_test_create_engine_patch,
    unload_fn_to_test_create_engine_patch,
)

redshift = create_redshift_fixture()


@patch_create_engine(path="tests.fixture.database.create_engine")
def test_copy(redshift):
    copy_fn_to_test_create_engine_patch(redshift)


@patch_create_engine(path="tests.fixture.database.create_engine")
def test_unload(redshift):
    unload_fn_to_test_create_engine_patch(redshift)
