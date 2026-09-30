import pytest

from pytest_mock_resources.hooks import use_cleanup_databases


def test_cleanup_databases_defaults_to_enabled(pytester):
    config = pytester.parseconfig()

    assert use_cleanup_databases(config) is True


@pytest.mark.parametrize(
    "args,expected",
    [
        (["--pmr-cleanup-databases"], True),
        (["--no-pmr-cleanup-databases"], False),
    ],
)
def test_cleanup_databases_follows_command_line_flag(pytester, args, expected):
    config = pytester.parseconfig(*args)

    assert use_cleanup_databases(config) is expected


@pytest.mark.parametrize("ini_value,expected", [("true", True), ("false", False)])
def test_cleanup_databases_follows_ini_setting(pytester, ini_value, expected):
    pytester.makeini(f"[pytest]\npmr_cleanup_databases = {ini_value}\n")

    config = pytester.parseconfig()

    assert use_cleanup_databases(config) is expected


@pytest.mark.parametrize(
    "ini_value,arg,expected",
    [
        ("false", "--pmr-cleanup-databases", True),
        ("true", "--no-pmr-cleanup-databases", False),
    ],
)
def test_cleanup_databases_command_line_flag_overrides_ini_setting(
    pytester, ini_value, arg, expected
):
    pytester.makeini(f"[pytest]\npmr_cleanup_databases = {ini_value}\n")

    config = pytester.parseconfig(arg)

    assert use_cleanup_databases(config) is expected


@pytest.mark.parametrize(
    "arg,override",
    [
        ("--no-pmr-cleanup-databases", True),
        ("--pmr-cleanup-databases", False),
    ],
)
def test_cleanup_databases_fixture_argument_overrides_command_line_flag(pytester, arg, override):
    config = pytester.parseconfig(arg)

    assert use_cleanup_databases(config, override=override) is override
