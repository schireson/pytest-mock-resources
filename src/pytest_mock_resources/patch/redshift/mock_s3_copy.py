import binascii
import csv
import gzip
import io
import sys

from sqlalchemy import MetaData, Table

from pytest_mock_resources.compat import boto3


def execute_mock_s3_copy_command(statement, engine):
    params = _parse_s3_command(statement)

    _mock_s3_copy(
        table_name=params["table_name"],
        schema_name=params["schema_name"],
        s3_uri=params["s3_uri"],
        aws_secret_access_key=params["aws_secret_access_key"],
        aws_access_key_id=params["aws_access_key_id"],
        columns=params.get("columns", None),
        engine=engine,
    )


def _parse_s3_command(statement):
    """Format, Parse and call patched 'COPY' command."""
    statement = strip(statement)
    params = dict()

    # deleting copy
    tokens = statement.split()[1:]

    # Fetching table name
    params["schema_name"], params["table_name"] = _split_table_name(tokens.pop(0))

    # Checking for columns
    if tokens[0][0] == "(":
        ending_index = 0
        for index, arg in enumerate(tokens):
            if arg.endswith(")"):
                ending_index = index
                break

        ending_index += 1
        columns = tokens[0:ending_index]
        columns[0] = columns[0].replace("(", "")
        columns[-1] = columns[-1].replace(")", "")
        columns = [x.replace(",", "") for x in columns]
        columns = [x for x in columns if x != ""]
        tokens = tokens[ending_index:]
        params["columns"] = columns

    # Fetching s3_uri
    if tokens.pop(0).lower() != "from":
        raise ValueError(
            (
                "Possibly malformed S3 URI Format. "
                "Statement = {statement}"
                "Redshift fixture only supports S3 Copy statments with the following syntax: "
                "COPY <table_name> FROM [(column 1, [column2, [..]])] '<file path on S3 bucket>' "
                "credentials 'aws_access_key_id=<aws_access_key_id>;"
                "aws_secret_access_key=<aws_secret_access_key>'"
            ).format(statement=statement)
        )
    params["s3_uri"] = strip(tokens.pop(0))

    # Fetching credentials
    for token in tokens:
        if "aws_access_key_id" in token.lower() or "aws_secret_access_key" in token.lower():
            # This is because of the following possibiliteis:
            # ... [with ]credentials[ AS] 'aws_access_key_id=x;aws_secret_access_key=y'
            # OR
            # ... [with ]credentials[ AS] 'aws_secret_access_key=y;aws_access_key_id=x'
            # OR
            # ... [with ]credentials[ AS] 'aws_secret_access_key=y;\naws_access_key_id=x'
            # OR
            # ... [with ]credentials[ AS] 'aws_secret_access_key=y; aws_access_key_id=x'
            # Supportred AWS credentials format:
            # [with ]credentials[ AS] 'aws_secret_access_key=y; aws_access_key_id=x'
            # No Support for additional credential formats, eg IAM roles, etc, yet.
            credentials_list = token.split(";")
            for credentials in credentials_list:
                if "aws_access_key_id" in credentials:
                    params["aws_access_key_id"] = credentials.split("=")[-1]
                elif "aws_secret_access_key" in credentials:
                    params["aws_secret_access_key"] = credentials.split("=")[-1]
                else:
                    raise ValueError(
                        (
                            "Possibly malformed AWS Credentials Format. "
                            "Statement = {statement}"
                            "Redshift fixture only supports S3 Copy statments with the following "
                            "syntax: COPY <table_name> FROM [(column 1, [column2, [..]])] '"
                            "<file path on S3 bucket>' "
                            "credentials 'aws_access_key_id=<aws_access_key_id>;"
                            "aws_secret_access_key=<aws_secret_access_key>' "
                            "Supportred AWS credentials format: "
                            "[with ]credentials[ AS] 'aws_secret_access_key=y; aws_access_key_id=x'"
                            " No Support for additional credential formats, eg IAM roles, etc, yet."
                        ).format(statement=statement)
                    )
    return params


def _split_table_name(table_name):
    """Split 'schema_name.table_name' to (schema_name, table_name)."""
    table_name_items = table_name.split(".")
    if len(table_name_items) == 1:
        schema_name = None
    elif len(table_name_items) == 2:
        schema_name, table_name = table_name_items
    else:
        raise ValueError("Cannot determine schema/table name from input {}".format(table_name))
    return schema_name, table_name


def _mock_s3_copy(
    table_name, s3_uri, schema_name, aws_secret_access_key, aws_access_key_id, columns, engine
):
    """Execute patched 'copy' command."""
    s3 = boto3.client(
        "s3", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key
    )
    ending_index = len(s3_uri)
    path_to_file = s3_uri[5:ending_index]
    bucket, key = path_to_file.split("/", 1)
    response = s3.get_object(Bucket=bucket, Key=key)

    # the following lins of code is used to check if the file is gzipped or not.
    # To do so we use magic numbers.
    # A mgic number is a constant numerical or text value used to identify a file format or protocol
    # The magic number for gzip compressed files is 1f 8b.
    is_gzipped = binascii.hexlify(response["Body"].read(2)) == b"1f8b"

    response = s3.get_object(Bucket=bucket, Key=key)
    data = read_data_csv(response["Body"].read(), is_gzipped, columns)

    meta = MetaData()
    table = Table(table_name, meta, autoload=True, schema=schema_name, autoload_with=engine)
    engine.execute(table.insert(data))


def read_data_csv(file, is_gzipped=False, columns=None, delimiter="|"):
    buffer = io.BytesIO(file)
    if is_gzipped:
        buffer = gzip.GzipFile(fileobj=buffer, mode="rb")

    # FUCK you python 2. This is ridiculous!
    wrapper = buffer
    if sys.version_info.major >= 3:
        wrapper = io.TextIOWrapper(buffer)
    else:
        delimiter = delimiter.encode("utf-8")

    reader = csv.DictReader(
        wrapper,
        delimiter=delimiter,
        quoting=csv.QUOTE_MINIMAL,
        quotechar='"',
        lineterminator="\n",
        skipinitialspace=True,
        doublequote=True,
    )
    return [dict(row) for row in reader]


def strip(input_string):
    """Strip trailing whitespace, single/double quotes."""
    return input_string.strip().rstrip(";").strip('"').strip("'")
