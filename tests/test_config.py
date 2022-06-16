from unittest import mock

from pytest_mock_resources.container.config import DockerContainerConfig, fallback, get_env_config

_DOCKER_HOST = "host.docker.internal"


class Test_get_env_config:
    def test_it_is_missing_env_var(self):
        with mock.patch("os.environ", {}):
            value = get_env_config("postgres", "username")
            assert value is None

    def test_it_has_the_expected_env_var(self):
        with mock.patch("os.environ", {"PMR_POSTGRES_USERNAME": "foobar"}):
            value = get_env_config("postgres", "username")
            assert value == "foobar"


class FooConfig(DockerContainerConfig):
    name = "foo"
    _fields = ("image", "host", "port", "ci_port", "extra_config", "no_value_default")
    _fields_defaults = {"image": "test", "extra_config": "bar", "port": 555}

    @fallback
    def extra_config(self):
        raise NotImplementedError()

    @fallback
    def no_value_default(self):
        raise NotImplementedError()


class Test_FooConfig:
    def test_it_instantiates(self):
        foo = FooConfig()
        assert foo.image == "test"
        assert foo.extra_config == "bar"
        assert foo.no_value_default is None

    def test_gets_values_from_kwargs(self):
        foo = FooConfig(image="bar", extra_config="meow", no_value_default=4)
        assert foo.image == "bar"
        assert foo.extra_config == "meow"
        assert foo.no_value_default == 4

    def test_gets_values_from_env(self):
        with mock.patch(
            "os.environ",
            {
                "PMR_FOO_IMAGE": "bar",
                "PMR_FOO_EXTRA_CONFIG": "meow",
                "PMR_FOO_NO_VALUE_DEFAULT": "4",
            },
        ):
            foo = FooConfig()

            assert foo.image == "bar"
            assert foo.extra_config == "meow"
            assert foo.no_value_default == "4"

    def test_repr(self):
        with mock.patch(
            "os.environ",
            {
                "PMR_FOO_EXTRA_CONFIG": "bar",
            },
        ):
            foo = FooConfig(image="foo")
            result = repr(foo)
            assert (
                result
                == "FooConfig(image='foo', host='localhost', port=555, ci_port=None, extra_config='bar', no_value_default=None)"
            )
