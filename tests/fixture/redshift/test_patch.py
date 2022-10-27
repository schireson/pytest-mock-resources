import pytest
import sqlalchemy.exc
from sqlalchemy import text

from pytest_mock_resources import create_postgres_fixture, create_redshift_fixture
from tests import skip_if_sqlalchemy2
from tests.fixture.redshift.utils import (
    copy_fn_to_test_create_engine_patch,
    copy_fn_to_test_psycopg2_connect_patch,
    copy_fn_to_test_psycopg2_connect_patch_as_context_manager,
    COPY_TEMPLATE,
    setup_table_and_bucket,
    unload_fn_to_test_create_engine_patch,
    unload_fn_to_test_psycopg2_connect_patch,
    unload_fn_to_test_psycopg2_connect_patch_as_context_manager,
)

redshift = create_redshift_fixture()
postgres = create_postgres_fixture()


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


def test_tightly_scoped_patch(redshift, postgres):
    """Assert psycopg2's patch is tightly scoped

    Redshift combined with a 2nd non-redshift fixture in the same test should not
    add redshift-specific features to the other engine.
    """
    import moto

    copy_command = text(
        COPY_TEMPLATE.format(
            COMMAND="COPY",
            LOCATION="s3://mybucket/file.csv",
            COLUMNS="",
            FROM="from",
            CREDENTIALS="credentials",
            OPTIONAL_ARGS="",
        )
    )
    with moto.mock_s3():
        setup_table_and_bucket(redshift)
        setup_table_and_bucket(postgres, create_bucket=False)
        with redshift.begin() as conn:
            conn.execute(copy_command)

        with pytest.raises(sqlalchemy.exc.ProgrammingError) as e:
            with postgres.begin() as conn:
                conn.execute(copy_command)

        assert 'syntax error at or near "credentials"' in str(e.value)


redshift_engine = create_redshift_fixture(session=False)
redshift_session = create_redshift_fixture(session=True)
async_redshift_engine = create_redshift_fixture(session=False, async_=True)
async_redshift_session = create_redshift_fixture(session=True, async_=True)


@skip_if_sqlalchemy2
def test_event_listener_registration_engine(redshift_engine):
    with redshift_engine.connect() as conn:
        result = conn.execute("select 1; select 1").scalar()

    result = redshift_engine.execute("select 1; select 1").scalar()
    assert result == 1


@skip_if_sqlalchemy2
def test_event_listener_registration_session(redshift_session):
    result = redshift_session.execute("select 1; select 1").scalar()
    assert result == 1


def test_event_listener_registration_text(redshift_session):
    result = redshift_session.execute(text("select 1; select 1")).scalar()
    assert result == 1


@pytest.mark.asyncio
async def test_event_listener_registration_async_engine(async_redshift_engine):
    async with async_redshift_engine.connect() as conn:
        result = await conn.execute(text("select 1"))
    value = result.scalar()
    assert value == 1


@pytest.mark.asyncio
async def test_event_listener_registration_async_session(async_redshift_session):
    result = await async_redshift_session.execute(text("select 1"))
    value = result.scalar()
    assert value == 1
