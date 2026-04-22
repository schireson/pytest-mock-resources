from unittest import mock

import pytest

# the wiring under test calls into python-on-whales at runtime, so skip
# this module entirely when running in a base test environment that does
# not install the docker extras.
pytest.importorskip("python_on_whales")

from pytest_mock_resources.config import DockerContainerConfig, fallback  # noqa: E402
from pytest_mock_resources.container.base import (  # noqa: E402
    ContainerCheckFailed,
    wait_for_container,
)


class _FakeConfig(DockerContainerConfig):
    # minimal subclass so wait_for_container can introspect ports/env/name.
    name = "fake"
    _fields = ("image", "host", "port", "ci_port", "container_args")
    _fields_defaults = {
        "image": "some-image:latest",
        "port": 12345,
        "ci_port": None,
    }

    @fallback
    def image(self):
        raise NotImplementedError()

    def ports(self):
        return {4321: self.port}

    def environment(self):
        return {"FAKE": "1"}

    def check_fn(self):
        # always fail initially so wait_for_container is forced to call
        # docker.run; subsequent check after run is stubbed in tests.
        raise ContainerCheckFailed()


def _make_docker_client_stub():
    """Produce a DockerClient-shaped mock that captures `run` kwargs."""

    docker = mock.MagicMock()
    docker.run = mock.MagicMock(return_value=mock.MagicMock())
    return docker


class Test_container_args_wiring:
    def _run(self, config):
        # patch the post-run check so we don't actually wait on a container.
        with mock.patch.object(
            _FakeConfig,
            "check_fn",
            side_effect=[ContainerCheckFailed(), None],
        ):
            docker = _make_docker_client_stub()
            wait_for_container(docker, config, retries=1, interval=0)
        return docker

    def test_empty_container_args_does_not_inject_anything(self):
        config = _FakeConfig()
        docker = self._run(config)

        assert docker.run.call_count == 1
        _, kwargs = docker.run.call_args
        # pmr's managed kwargs must always be present.
        assert kwargs["name"] == "pmr_fake_12345"
        assert kwargs["envs"] == {"FAKE": "1"}
        assert kwargs["publish"] == [(12345, 4321)]
        # user provided nothing extra.
        assert "memory" not in kwargs
        assert "cpus" not in kwargs

    def test_user_supplied_container_args_are_forwarded(self):
        config = _FakeConfig(
            container_args={"memory": "2g", "cpus": 4, "labels": {"owner": "pmr"}},
        )
        docker = self._run(config)

        _, kwargs = docker.run.call_args
        assert kwargs["memory"] == "2g"
        assert kwargs["cpus"] == 4
        assert kwargs["labels"] == {"owner": "pmr"}

    def test_pmr_managed_kwargs_override_user_supplied_values(self):
        # user attempts to override reserved pmr plumbing; pmr's values win.
        config = _FakeConfig(
            container_args={
                "name": "i-should-be-ignored",
                "envs": {"ATTACKER": "1"},
                "publish": [("7777", "7777")],
                "memory": "1g",
            },
        )
        docker = self._run(config)

        _, kwargs = docker.run.call_args
        # pmr-managed keys are preserved.
        assert kwargs["name"] == "pmr_fake_12345"
        assert kwargs["envs"] == {"FAKE": "1"}
        assert kwargs["publish"] == [(12345, 4321)]
        # non-conflicting user value is still forwarded.
        assert kwargs["memory"] == "1g"


@pytest.mark.parametrize(
    "container_args",
    [None, {}, {"memory": "1g"}],
)
def test_wait_for_container_accepts_various_shapes(container_args):
    # sanity: wait_for_container must not crash when container_args is falsy,
    # empty, or populated.
    config = _FakeConfig(container_args=container_args)

    with mock.patch.object(
        _FakeConfig,
        "check_fn",
        side_effect=[ContainerCheckFailed(), None],
    ):
        docker = _make_docker_client_stub()
        wait_for_container(docker, config, retries=1, interval=0)

    assert docker.run.call_count == 1
