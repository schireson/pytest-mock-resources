from pytest_mock_resources import create_moto_fixture

moto = create_moto_fixture()


def test_create_bucket(moto):
    s3 = moto.client("s3")
    s3.create_bucket(Bucket="foo")
    buckets = s3.list_buckets()["Buckets"]
    assert len(buckets) == 1
    assert buckets[0]["Name"] == "foo"
