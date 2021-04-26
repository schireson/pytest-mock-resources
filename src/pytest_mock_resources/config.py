import os
import socket

from pytest_mock_resources.compat import functools

_DOCKER_HOST = "host.docker.internal"


def is_ci():
    return os.getenv("CI") == "true"


@functools.lru_cache()
def is_docker_host():
    try:
        socket.gethostbyname(_DOCKER_HOST)
    except socket.gaierror:
        return False
    else:
        return True


def get_env_config(name, kind):
    env_var = "PMR_{name}_{kind}".format(name=name.upper(), kind=kind.upper())
    return os.environ.get(env_var)


def fallback(fn):
    attr = fn.__name__

    @property
    @functools.wraps(fn)
    def wrapper(self):
        value = get_env_config(self.name, attr)
        if value is not None:
            return value

        value = getattr(self, "_{attr}".format(attr=attr), None)
        if value is not None:
            return value

        try:
            return fn(self)
        except NotImplementedError:
            if attr in self._fields_defaults:
                return self._fields_defaults[attr]
            return None

    return wrapper


class DockerContainerConfig:
    _fields = {"image", "host", "port", "ci_port"}
    _fields_defaults = {}

    def __init__(self, **kwargs):
        for field in self._fields:
            value = kwargs.get(field)
            attr = "_{}".format(field)
            setattr(self, attr, value)

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "{cls_name}({attrs})".format(
            cls_name=cls_name,
            attrs=", ".join(
                "{}={}".format(attr, repr(getattr(self, attr))) for attr in self._fields
            ),
        )

    @fallback
    def image(self):
        raise NotImplementedError()

    @fallback
    def ci_port(self):
        raise NotImplementedError()

    @fallback
    def host(self):
        if is_docker_host():
            return _DOCKER_HOST

        return os.environ.get("PYTEST_MOCK_RESOURCES_HOST", "localhost")

    @fallback
    def port(self):
        ci_port = self.ci_port
        if ci_port and is_ci():
            return ci_port

        raise NotImplementedError()
