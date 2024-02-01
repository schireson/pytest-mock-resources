from __future__ import annotations

import io
from dataclasses import dataclass
from typing import BinaryIO, ClassVar, Iterable, TextIO, TYPE_CHECKING, Union

from pytest_mock_resources.action import AbstractAction, validate_actions

if TYPE_CHECKING:
    from pytest_mock_resources.fixture.moto.base import Session


ObjectContent = Union[bytes, str, BinaryIO, TextIO]


@dataclass
class S3Bucket(AbstractAction):
    fixtures: ClassVar[tuple[str, ...]] = ("moto",)
    static_safe: ClassVar[bool] = True

    name: str

    def object(self, key: str, data: ObjectContent):
        return S3Object(self, key, data)

    def apply(self, session: Session):
        client = session.resource("s3")
        client.create_bucket(Bucket=self.name)


@dataclass
class S3Object(AbstractAction):
    fixtures: ClassVar[tuple[str, ...]] = ("moto",)
    static_safe: ClassVar[bool] = True

    bucket: str | S3Bucket
    key: str
    data: ObjectContent
    encoding: str = "utf-8"

    def apply(self, session: Session):
        resource = session.resource("s3")
        bucket_name = self.bucket.name if isinstance(self.bucket, S3Bucket) else self.bucket

        if isinstance(self.data, str):
            data = io.BytesIO(self.data.encode(self.encoding))
        elif isinstance(self.data, bytes):
            data = io.BytesIO(self.data)
        elif isinstance(self.data, io.StringIO):
            data = io.BytesIO(self.data.getvalue().encode(self.encoding))
        elif isinstance(self.data, io.BytesIO):
            data = io.BytesIO(self.data.getbuffer().tobytes())
        else:
            raise NotImplementedError()

        resource.Object(bucket_name=bucket_name, key=self.key).upload_fileobj(data)


MotoAction = Union[S3Bucket, S3Object]


def apply_ordered_actions(session: Session, ordered_actions: Iterable[MotoAction]):
    validate_actions(ordered_actions, fixture="moto")
    for action in ordered_actions:
        action.apply(session)
