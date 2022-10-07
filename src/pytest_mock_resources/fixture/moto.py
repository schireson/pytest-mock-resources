from __future__ import annotations

import time
from dataclasses import dataclass

import pytest

from pytest_mock_resources.compat import boto3
from pytest_mock_resources.container.base import get_container
from pytest_mock_resources.container.moto import endpoint_url, MotoConfig


@pytest.fixture(scope="session")
def pmr_moto_config():
    """Override this fixture with a :class:`MotoConfig` instance to specify different defaults.

    Examples:
        >>> @pytest.fixture(scope='session')
        ... def pmr_moto_config():
        ...     return MotoConfig(image="motoserver/moto:latest")
    """
    return MotoConfig()


@pytest.fixture(scope="session")
def pmr_moto_container(pytestconfig, pmr_moto_config):
    yield from get_container(pytestconfig, pmr_moto_config)


def create_moto_fixture(scope="function"):
    """Produce a Moto fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    moto server.

    .. note::

       Each test executes using a different (fake) AWS account through moto. If you create
       boto3 ``client``/``resource`` objects outside of the one handed to the test (for example,
       in the code under test), they should be sure to use the ``aws_access_key_id``,
       ``aws_secret_access_key``, ``aws_session_token``, and ``endpoint_url`` given by the
       ``pmr_moto_credentials`` fixture.

    .. note::

       A moto dashboard should be available for debugging while the container is running.
       By default it would be available at ``http://localhost:5555/moto-api/#`` (but
       the exact URL may be different depending on your host/port config.

    Args:
        scope (str): The scope of the fixture can be specified by the user, defaults to "function".
    """
    # TODO: Add options for declarative creation of AWS objects, like S3 buckets/files.

    @pytest.fixture(scope=scope)
    def _fixture(pmr_moto_credentials) -> Session:
        return Session(
            boto3.Session(
                aws_access_key_id=pmr_moto_credentials.aws_access_key_id,
                aws_secret_access_key=pmr_moto_credentials.aws_secret_access_key,
                aws_session_token=pmr_moto_credentials.aws_session_token,
            ),
            endpoint_url=pmr_moto_credentials.endpoint_url,
        )

    return _fixture


@pytest.fixture()
def pmr_moto_credentials(pmr_moto_container, pmr_moto_config) -> Credentials:
    # Attempt at a cross-process way of generating unique 12-character integers.
    account_id = str(time.time_ns())[:12]

    url = endpoint_url(pmr_moto_config)

    sts = boto3.client(
        "sts",
        endpoint_url=url,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    response = sts.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/my-role",
        RoleSessionName="test-session-name",
        ExternalId="test-external-id",
    )

    return Credentials(
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"],
        endpoint_url=url,
    )


@dataclass
class Credentials:
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: str
    endpoint_url: str
    region_name = "us-east-1"

    def as_kwargs(self):
        return {
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "aws_session_token": self.aws_session_token,
            "endpoint_url": self.endpoint_url,
            "region_name": self.region_name,
        }


@dataclass
class Session:
    """Wrap the vanilla boto3 Session object, automatically inserting the endpoint_url field."""

    session: boto3.Session
    endpoint_url: str

    def client(self, service_name, **kwargs):
        return self.session.client(service_name, endpoint_url=self.endpoint_url, **kwargs)

    def resource(self, service_name, **kwargs):
        return self.session.resource(service_name, endpoint_url=self.endpoint_url, **kwargs)
