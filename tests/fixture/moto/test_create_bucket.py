from pytest_mock_resources import create_moto_fixture, S3Bucket

moto = create_moto_fixture(S3Bucket("foo"))


def test_create_bucket(moto):
    s3 = moto.client("s3")
    buckets = s3.list_buckets()["Buckets"]
    assert len(buckets) == 1
    assert buckets[0]["Name"] == "foo"
