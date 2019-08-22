import subprocess  # nosec

import pytest


@pytest.fixture(scope="function")
def data_catalog():
    process = subprocess.Popen(["moto_server", "glue"])  # nosec
    yield
    process.terminate()
