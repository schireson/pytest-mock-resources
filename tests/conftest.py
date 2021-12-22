import pytest

pytest_plugins = "pytester"


# See https://github.com/spulec/moto/issues/3292#issuecomment-770682026
@pytest.fixture(autouse=True)
def set_aws_region(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
