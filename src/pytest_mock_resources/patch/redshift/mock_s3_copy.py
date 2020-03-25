import binascii
import csv
import gzip
import io

import attr

from pytest_mock_resources.compat import boto3


@attr.s
class S3CopyCommand:
    table_name = attr.ib()
    delimiter = attr.ib()
    s3_uri = attr.ib()
    empty_as_null = attr.ib()
    format = attr.ib(default="CSV")
    aws_access_key_id = attr.ib(default=None)
    aws_secret_access_key = attr.ib(default=None)
    columns = attr.ib(default=None)
    schema_name = attr.ib(default=None)


def mock_s3_copy_command(statement, cursor):
    copy_command = _parse_s3_command(statement)
    return _mock_s3_copy(cursor, copy_command)


def _parse_s3_command(statement):
    """Format, Parse and call patched 'COPY' command."""
    statement = strip(statement)
    params = dict()

    # deleting copy
    tokens = statement.split()[1:]

    # Fetching table name
    params["schema_name"], params["table_name"] = _split_table_name(tokens.pop(0))

    # Checking for columns
    params["columns"] = []
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
    empty_as_null = False
    delimiter = None
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
        if "emptyasnull" == token.lower():
            empty_as_null = True
        if "csv" == token.lower():
            delimiter = ","

    if delimiter is None:
        delimiter = "|"
    return S3CopyCommand(**params, empty_as_null=empty_as_null, delimiter=delimiter)


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
    cursor,
    copy_command,
):
    """Execute patched 'copy' command."""
    s3 = boto3.client(
        "s3",
        aws_access_key_id=copy_command.aws_access_key_id,
        aws_secret_access_key=copy_command.aws_secret_access_key,
    )
    ending_index = len(copy_command.s3_uri)
    path_to_file = copy_command.s3_uri[5:ending_index]
    bucket, key = path_to_file.split("/", 1)
    response = s3.get_object(Bucket=bucket, Key=key)

    # the following lins of code is used to check if the file is gzipped or not.
    # To do so we use magic numbers.
    # A mgic number is a constant numerical or text value used to identify a file format or protocol
    # The magic number for gzip compressed files is 1f 8b.
    is_gzipped = binascii.hexlify(response["Body"].read(2)) == b"1f8b"

    response = s3.get_object(Bucket=bucket, Key=key)
    data = get_raw_file(response["Body"].read(), is_gzipped)

    cursor.copy_expert(
        "COPY {cc.table_name} FROM STDIN WITH DELIMITER AS '{cc.delimiter}' {cc.format} HEADER {non_null_clause}".format(
            cc=copy_command,
            non_null_clause=("FORCE NOT NULL " + ", ".join(copy_command.columns))
            if copy_command.columns
            else "",
        ),
        data,
    )


def get_raw_file(file, is_gzipped=False):
    buffer = io.BytesIO(file)
    if is_gzipped:
        buffer = gzip.GzipFile(fileobj=buffer, mode="rb")
    return buffer


def read_data_csv(file, is_gzipped=False, columns=None, delimiter="|"):
    buffer = get_raw_file(file, is_gzipped=is_gzipped)
    wrapper = io.TextIOWrapper(buffer)
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
