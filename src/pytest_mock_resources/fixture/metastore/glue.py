import subprocess  # nosec

import pytest


@pytest.fixture(scope="function")
def mock_glue():
    process = subprocess.Popen(["moto_server", "glue"])  # nosec
    yield
    process.terminate()
