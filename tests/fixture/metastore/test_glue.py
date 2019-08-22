import boto3

from pytest_mock_resources.fixture.metastore.glue import data_catalog  # noqa


def test_glue(data_catalog):  # noqa
    table_input = {
        "Name": "bar",
        "Owner": "schireson",
        "StorageDescriptor": {
            "Columns": [{"Name": "column", "Type": "string", "Comment": "comment"}],
            "Location": "s3://foo/bar/0/",
            "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
            "Compressed": False,
            "NumberOfBuckets": -1,
            "SerdeInfo": {
                "SerializationLibrary": "org.apache.hadoop.hive.serde2.OpenCSVSerde",
                "Parameters": {"serialization.format": "1"},
            },
        },
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {"classification": "csv"},
    }

    client = boto3.client("glue", endpoint_url="http://127.0.0.1:5000/")

    client.create_database(DatabaseInput={"Name": "foo", "Description": "bar"})

    client.get_database(Name="foo")

    client.create_table(DatabaseName="foo", TableInput=table_input)

    response = client.get_table(DatabaseName="foo", Name="bar")

    assert response["Table"]["StorageDescriptor"]["Location"] == "s3://foo/bar/0/"

    table_input["StorageDescriptor"]["Location"] = "s3://foo/bar/1/"

    client.update_table(DatabaseName="foo", TableInput=table_input)

    response = client.get_table(DatabaseName="foo", Name="bar")

    assert response["Table"]["StorageDescriptor"]["Location"] == "s3://foo/bar/1/"

    client.get_partitions(DatabaseName="foo", TableName="bar")

    client.create_partition(
        DatabaseName="foo",
        TableName="bar",
        PartitionInput={
            "Values": ["1970"],
            "StorageDescriptor": {"Location": "s3://foo/bar/1/1970/"},
        },
    )

    response = client.get_partitions(DatabaseName="foo", TableName="bar")

    assert response["Partitions"][0]["Values"] == ["1970"]
