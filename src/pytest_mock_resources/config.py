from __future__ import annotations

import functools
import os
import socket
from typing import ClassVar, Iterable

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


def get_env_config(name, kind, default=None):
    env_var = f"PMR_{name.upper()}_{kind.upper()}"
    return os.environ.get(env_var, default)


def fallback(fn):
    attr = fn.__name__

    @property
    @functools.wraps(fn)
    def wrapper(self):
        value = get_env_config(self.name, attr)
        if value is not None:
            return value

        if self.has(attr):
            return self.get(attr)

        try:
            return fn(self)
        except NotImplementedError:
            if attr in self._fields_defaults:
                return self._fields_defaults[attr]
            return None

    return wrapper


class DockerContainerConfig:
    name: ClassVar[str]

    _fields: ClassVar[Iterable] = {"image", "host", "port", "ci_port", "container_args"}
    _fields_defaults: ClassVar[dict] = {}

    subclasses: ClassVar[dict[str, type[DockerContainerConfig]]] = {}

    @classmethod
    def __init_subclass__(cls):
        DockerContainerConfig.subclasses[cls.name] = cls

    def __init__(self, **kwargs):
        for field, value in kwargs.items():
            if field not in self._fields:
                continue

            attr = f"_{field}"
            setattr(self, attr, value)

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "{cls_name}({attrs})".format(
            cls_name=cls_name,
            attrs=", ".join(f"{attr}={getattr(self, attr)!r}" for attr in self._fields),
        )

    def has(self, attr):
        attr_name = f"_{attr}"
        return hasattr(self, attr_name)

    def get(self, attr):
        attr_name = f"_{attr}"
        return getattr(self, attr_name)

    def set(self, attr, value):
        attr_name = f"_{attr}"
        return setattr(self, attr_name, value)

    @fallback
    def image(self):
        raise NotImplementedError()

    @fallback
    def ci_port(self):
        raise NotImplementedError()

    @fallback
    def host(self):
        if os.environ.get("PYTEST_MOCK_RESOURCES_HOST") is not None:
            return os.environ.get("PYTEST_MOCK_RESOURCES_HOST")

        if is_docker_host():
            return _DOCKER_HOST

        return "localhost"

    @fallback
    def port(self):
        ci_port = self.ci_port
        if ci_port and is_ci():
            return ci_port

        raise NotImplementedError()

    @fallback
    def container_args(self):
        return ()

    def ports(self):
        return {}

    def environment(self):
        return {}

    def check_fn(self):
        pass
