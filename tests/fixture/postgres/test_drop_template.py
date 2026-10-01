import asyncio
import copy
import uuid

import pytest

from pytest_mock_resources.fixture.base import generate_fixture_id
from pytest_mock_resources.fixture.postgresql import (
    _async_fixture,
    _sync_fixture,
    DatabaseDropWarning,
)
from pytest_mock_resources.templates import drop_templates
from tests import skip_if_not_sqlalchemy2
from tests.fixture.postgres.test_drop_database import (
    drop_database,
    drop_database_async,
    list_databases,
    list_databases_async,
)

MANAGER_KWARGS = {
    "ordered_actions": (),
    "tables": None,
    "createdb_template": "template1",
    "session": None,
    "fixture_id": None,
    "actions_share_transaction": None,
}


def test_template_is_dropped_when_templates_are_dropped(
    pmr_postgres_container, pmr_postgres_config
):
    kwargs = build_manager_kwargs()
    template = kwargs["fixture_id"]
    fixture = _sync_fixture(pmr_postgres_config, kwargs, {}, cleanup_databases=True)
    next(fixture)

    fixture.close()

    assert template in list_databases(pmr_postgres_config)

    drop_templates(pmr_postgres_config)

    assert template not in list_databases(pmr_postgres_config)


def test_template_is_kept_when_cleanup_is_disabled(pmr_postgres_container, pmr_postgres_config):
    kwargs = build_manager_kwargs()
    template = kwargs["fixture_id"]
    fixture = _sync_fixture(pmr_postgres_config, kwargs, {}, cleanup_databases=False)
    engine, _ = next(fixture)
    database_name = engine.url.database
    fixture.close()

    drop_templates(pmr_postgres_config)

    databases = list_databases(pmr_postgres_config)
    assert template in databases
    assert database_name in databases
    drop_database(pmr_postgres_config, template)
    drop_database(pmr_postgres_config, database_name)


def test_template_of_other_fixture_is_left_alone(pmr_postgres_container, pmr_postgres_config):
    dropped_kwargs = build_manager_kwargs()
    kept_kwargs = build_manager_kwargs()
    dropped = _sync_fixture(pmr_postgres_config, dropped_kwargs, {}, cleanup_databases=True)
    kept = _sync_fixture(pmr_postgres_config, kept_kwargs, {}, cleanup_databases=False)
    next(dropped)
    kept_engine, _ = next(kept)
    kept_database = kept_engine.url.database
    dropped.close()
    kept.close()

    drop_templates(pmr_postgres_config)

    databases = list_databases(pmr_postgres_config)
    assert dropped_kwargs["fixture_id"] not in databases
    assert kept_kwargs["fixture_id"] in databases
    drop_database(pmr_postgres_config, kept_kwargs["fixture_id"])
    drop_database(pmr_postgres_config, kept_database)


def test_already_dropped_template_is_ignored(pmr_postgres_container, pmr_postgres_config):
    kwargs = build_manager_kwargs()
    template = kwargs["fixture_id"]
    fixture = _sync_fixture(pmr_postgres_config, kwargs, {}, cleanup_databases=True)
    next(fixture)
    fixture.close()
    drop_database(pmr_postgres_config, template)

    drop_templates(pmr_postgres_config)

    assert template not in list_databases(pmr_postgres_config)


def test_template_drop_failure_warns_with_template_name(
    pmr_postgres_container, pmr_postgres_config
):
    unreachable_config = copy.copy(pmr_postgres_config)
    kwargs = build_manager_kwargs()
    template = kwargs["fixture_id"]
    fixture = _sync_fixture(unreachable_config, kwargs, {}, cleanup_databases=True)
    next(fixture)
    fixture.close()
    unreachable_config.set("root_database", "pmr_missing_root_database")

    with pytest.warns(DatabaseDropWarning) as warning_records:
        drop_templates(unreachable_config)

    assert len(warning_records) == 1
    message = str(warning_records[0].message)
    assert message.startswith(f"Failed to drop database '{template}' at fixture teardown: ")
    assert "pmr_missing_root_database" in message
    assert template in list_databases(pmr_postgres_config)
    drop_database(pmr_postgres_config, template)


@pytest.mark.asyncio
@skip_if_not_sqlalchemy2
async def test_async_template_is_dropped_when_templates_are_dropped(
    pmr_postgres_container, pmr_postgres_config
):
    kwargs = build_manager_kwargs()
    template = kwargs["fixture_id"]
    fixture = _async_fixture(pmr_postgres_config, kwargs, {}, cleanup_databases=True)
    await fixture.__anext__()
    with pytest.raises(StopAsyncIteration):
        await fixture.__anext__()

    assert template in await list_databases_async(pmr_postgres_config)

    # NOTE: `drop_templates` runs its own event loop, which cannot start inside the running one.
    await asyncio.get_running_loop().run_in_executor(None, drop_templates, pmr_postgres_config)

    assert template not in await list_databases_async(pmr_postgres_config)


@pytest.mark.asyncio
@skip_if_not_sqlalchemy2
async def test_async_template_is_kept_when_cleanup_is_disabled(
    pmr_postgres_container, pmr_postgres_config
):
    kwargs = build_manager_kwargs()
    template = kwargs["fixture_id"]
    fixture = _async_fixture(pmr_postgres_config, kwargs, {}, cleanup_databases=False)
    engine, _ = await fixture.__anext__()
    database_name = engine.url.database
    with pytest.raises(StopAsyncIteration):
        await fixture.__anext__()

    await asyncio.get_running_loop().run_in_executor(None, drop_templates, pmr_postgres_config)

    databases = await list_databases_async(pmr_postgres_config)
    assert template in databases
    await drop_database_async(pmr_postgres_config, template)
    await drop_database_async(pmr_postgres_config, database_name)


def test_template_is_dropped_when_container_fixture_ends(
    pytester, pmr_postgres_container, pmr_postgres_config
):
    template = f"pmr_template_pg_{uuid.uuid4().hex}"
    pytester.makepyfile(build_inner_test(template, cleanup_databases=True))

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=1)
    assert list_databases(pmr_postgres_config).isdisjoint({template, read_inner_database(pytester)})


def test_template_is_kept_after_container_fixture_ends_when_cleanup_is_disabled(
    pytester, pmr_postgres_container, pmr_postgres_config
):
    template = f"pmr_template_pg_{uuid.uuid4().hex}"
    pytester.makepyfile(build_inner_test(template, cleanup_databases=False))

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=1)
    database_name = read_inner_database(pytester)
    databases = list_databases(pmr_postgres_config)
    assert template in databases
    assert database_name in databases
    drop_database(pmr_postgres_config, template)
    drop_database(pmr_postgres_config, database_name)


def build_manager_kwargs():
    return dict(MANAGER_KWARGS, fixture_id=generate_fixture_id(name="pg"))


def build_inner_test(template, *, cleanup_databases):
    # NOTE: The template name is pinned so the outer test can look for it after the inner process
    #       exits.
    return f"""
import pathlib

import pytest_mock_resources.fixture.postgresql as postgresql
from pytest_mock_resources import create_postgres_fixture

postgresql.generate_fixture_id = lambda enabled, name: "{template}"
inner_postgres = create_postgres_fixture(cleanup_databases={cleanup_databases})


def test_inner(inner_postgres):
    path = pathlib.Path(__file__).with_name("database.txt")
    path.write_text(inner_postgres.url.database)
"""


def read_inner_database(pytester):
    return (pytester.path / "database.txt").read_text()
