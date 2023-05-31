import io

from pytest_mock_resources import create_moto_fixture, S3Bucket, S3Object

bucket = S3Bucket("foo")
moto = create_moto_fixture(
    bucket,
    # manual-construction style
    S3Object("foo", "a/b/c.txt", "hello!"),
    # fluent-method style
    bucket.object("b/text.txt", "This is text"),
    bucket.object("c/textio.txt", io.StringIO("This is textio")),
    bucket.object("d/bytes.txt", b"This is bytes"),
    bucket.object("e/binaryio.txt", io.BytesIO(b"This is binaryio")),
)


def test_produce_objects(moto):
    resource = moto.resource("s3")
    objects = sorted(resource.Bucket("foo").objects.all(), key=lambda o: o.key)
    assert len(objects) == 5

    assert objects[0].key == "a/b/c.txt"
    assert objects[0].get()["Body"].read() == b"hello!"

    assert objects[1].key == "b/text.txt"
    assert objects[1].get()["Body"].read() == b"This is text"

    assert objects[2].key == "c/textio.txt"
    assert objects[2].get()["Body"].read() == b"This is textio"

    assert objects[3].key == "d/bytes.txt"
    assert objects[3].get()["Body"].read() == b"This is bytes"

    assert objects[4].key == "e/binaryio.txt"
    assert objects[4].get()["Body"].read() == b"This is binaryio"


def test_2nd_test_using_same_fixture(moto):
    """Asserts you get the same fixture state in two tests."""
    resource = moto.resource("s3")
    objects = list(resource.Bucket("foo").objects.all())
    assert len(objects) == 5


moto2 = create_moto_fixture(bucket)


def test_separate_fixture_state(moto2):
    """Asserts that two tests referencing the same bucket do not share state."""
    resource = moto2.resource("s3")
    objects = sorted(resource.Bucket("foo").objects.all(), key=lambda o: o.key)
    assert len(objects) == 0
