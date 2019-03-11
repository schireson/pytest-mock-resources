import csv
import tempfile

import boto3
import pandas

from pytest_mock_resources.fixture.database.mock_s3_copy import _strip


def execute_mock_s3_unload_command(statement, engine):
    params = _parse_s3_command(statement)

    _mock_s3_unload(
        select_statement=params["select_statement"],
        s3_uri=params["s3_uri"],
        aws_secret_access_key=params["aws_secret_access_key"],
        aws_access_key_id=params["aws_access_key_id"],
        engine=engine,
        delimiter=params.get("delimiter", "|"),
        is_gzipped=params["gzip"],
    )


def _parse_s3_command(statement):
    """Format and Parse 'UNLOAD' command."""
    statement = _strip(statement)
    params = dict()

    # deleting 'unload'
    tokens = statement.split()[1:]

    # Fetching select statement
    select_statement = ""
    error_flag = False
    for index, token in enumerate(tokens):
        if token.lower() == "to":
            tokens = tokens[index:]
            break
        select_statement += " " + token
    params["select_statement"] = select_statement
    if error_flag:
        raise ValueError(
            (
                "Possibly malformed SELECT Statement. "
                "Statement = {statement}"
                "Redshift fixture only supports S3 Unload statments with the following syntax: "
                "UNLOAD ('select-statement') TO 's3://object-path/name-prefix'"
                "authorization 'aws_access_key_id=<aws_access_key_id>;"
                "aws_secret_access_key=<aws_secret_access_key>'"
                "[GZIP] [DELIMITER [ AS ] 'delimiter-char']"
            ).format(statement=statement)
        )

    # Fetching s3_uri
    if tokens.pop(0).lower() != "to":
        raise ValueError(
            (
                "Possibly malformed S3 URI Format. "
                "Statement = {statement}"
                "Redshift fixture only supports S3 Unload statments with the following syntax: "
                "UNLOAD ('select-statement') TO 's3://object-path/name-prefix'"
                "authorization 'aws_access_key_id=<aws_access_key_id>;"
                "aws_secret_access_key=<aws_secret_access_key>'"
                "[GZIP] [DELIMITER [ AS ] 'delimiter-char']"
            ).format(statement=statement)
        )
    params["s3_uri"] = _strip(tokens.pop(0))

    # Fetching authorization
    for token in tokens:
        if "aws_access_key_id" in token.lower() or "aws_secret_access_key" in token.lower():
            # This is because of the following possibiliteis:
            # ... [with ]authorization[ AS] 'aws_access_key_id=x;aws_secret_access_key=y'
            # OR
            # ... [with ]authorization[ AS] 'aws_secret_access_key=y;aws_access_key_id=x'
            # OR
            # ... [with ]authorization[ AS] 'aws_secret_access_key=y;\naws_access_key_id=x'
            # OR
            # ... [with ]authorization[ AS] 'aws_secret_access_key=y; aws_access_key_id=x'
            # Supportred AWS authorization format:
            # [with ]authorization[ AS] 'aws_secret_access_key=y; aws_access_key_id=x'
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

    # Fetching GZIP Flag
    params["gzip"] = False
    for token in tokens:
        if _strip(token.lower()) == "gzip":
            params["gzip"] = True

    # Fetching delimiter
    for index, token in enumerate(tokens):
        if token.lower() == "delimiter":
            try:
                if tokens[index + 1].lower() != "as":
                    params["delimiter"] = _strip(tokens[index + 1])
                else:
                    params["delimiter"] = _strip(tokens[index + 2])
            except IndexError:
                raise ValueError(
                    (
                        "Possibly malformed Delimiter Format. "
                        "Statement = {statement}"
                        "Redshift fixture only supports S3 Unload statments with the following"
                        "syntax: UNLOAD ('select-statement') TO 's3://object-path/name-prefix'"
                        "authorization 'aws_access_key_id=<aws_access_key_id>;"
                        "aws_secret_access_key=<aws_secret_access_key>'"
                        "[GZIP] [DELIMITER [ AS ] 'delimiter-char']"
                    ).format(statement=statement)
                )
    return params


def _mock_s3_unload(
    select_statement,
    s3_uri,
    aws_secret_access_key,
    aws_access_key_id,
    engine,
    delimiter,
    is_gzipped,
):
    """Execute patched 'unload' command."""
    # Parsing s3 uri
    path_to_file = s3_uri[5 : len(s3_uri)]
    bucket, key = path_to_file.split("/", 1)

    dataframe = pandas.read_sql(sql=select_statement, con=engine)

    # If some sort of compressions is specified then the dataframe needs to be saved as a file.
    # Savaing the dataframe as a `File-Like Object` has no effect of compression.
    # So if `gzip` compression is specifed, then, we save a temporary file.
    with tempfile.NamedTemporaryFile(suffix=".gz") as tf:
        buffer = tf.name if is_gzipped else None

        # Convert the dataframe to csv.
        content = get_dataframe_csv(
            dataframe, is_gzipped=is_gzipped, sep=delimiter, path_or_buf=buffer
        )

        if buffer:
            # Open the temporary file.
            content = tf.read()
        else:
            content = content.encode()

        # Push the data to the S3 Bucket.
        conn = boto3.resource(
            "s3", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key
        )
        conn.create_bucket(Bucket=bucket)
        obj = conn.Object(bucket, key)
        obj.put(Body=content)


def get_dataframe_csv(dataframe, is_gzipped=False, sep="|", **additional_to_csv_options):
    compression = "infer"
    if is_gzipped:
        compression = "gzip"
    content = dataframe.to_csv(
        sep=sep,
        index=False,
        na_rep="",
        encoding="utf8",
        quoting=csv.QUOTE_NONE,
        doublequote=False,
        escapechar="\\",
        compression=compression,
        **additional_to_csv_options
    )
    return content
