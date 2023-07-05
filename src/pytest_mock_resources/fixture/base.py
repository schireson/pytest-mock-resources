import uuid
from typing import Union

import pytest
from typing_extensions import Literal


def generate_fixture_id(enabled: bool = True, name=""):
    if enabled:
        uuid_str = str(uuid.uuid4()).replace("-", "_")
        return "_".join(["pmr_template", name, uuid_str])
    return None


def asyncio_fixture(async_fixture, scope="function"):
    # pytest-asyncio in versions >=0.17 force you to use a `pytest_asyncio.fixture`
    # call instead of `pytest.fixture`. Given that this would introduce an unnecessary
    # dependency on pytest-asyncio (when there are other alternatives) seems less than
    # ideal, so instead we can just set the flag that they set, as the indicator.
    async_fixture._force_asyncio_fixture = True

    fixture = pytest.fixture(scope=scope)
    return fixture(async_fixture)


Scope = Union[
    Literal["session"],
    Literal["package"],
    Literal["module"],
    Literal["class"],
    Literal["function"],
]
