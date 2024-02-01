import csv
import gzip
import io

from pytest_mock_resources.compat import boto3
from pytest_mock_resources.patch.redshift.mock_s3_copy import strip


def mock_s3_unload_command(statement, cursor):
    params = _parse_s3_command(statement)

    return _mock_s3_unload(
        select_statement=params["select_statement"],
        s3_uri=params["s3_uri"],
        aws_secret_access_key=params["aws_secret_access_key"],
        aws_access_key_id=params["aws_access_key_id"],
        cursor=cursor,
        delimiter=params.get("delimiter", "|"),
        is_gzipped=params["gzip"],
    )


def _parse_s3_command(statement):
    """Format and Parse 'UNLOAD' command."""
    statement = strip(statement)
    params = {}

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
            "Possibly malformed SELECT Statement. "
            f"Statement = {statement}"
            "Redshift fixture only supports S3 Unload statements with the following syntax: "
            "UNLOAD ('select-statement') TO 's3://object-path/name-prefix'"
            "authorization 'aws_access_key_id=<aws_access_key_id>;"
            "aws_secret_access_key=<aws_secret_access_key>'"
            "[GZIP] [DELIMITER [ AS ] 'delimiter-char']"
        )

    # Fetching s3_uri
    if tokens.pop(0).lower() != "to":
        raise ValueError(
            "Possibly malformed S3 URI Format. "
            f"Statement = {statement}"
            "Redshift fixture only supports S3 Unload statements with the following syntax: "
            "UNLOAD ('select-statement') TO 's3://object-path/name-prefix'"
            "authorization 'aws_access_key_id=<aws_access_key_id>;"
            "aws_secret_access_key=<aws_secret_access_key>'"
            "[GZIP] [DELIMITER [ AS ] 'delimiter-char']"
        )
    params["s3_uri"] = strip(tokens.pop(0))

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
                        "Possibly malformed AWS Credentials Format. "
                        f"Statement = {statement}"
                        "Redshift fixture only supports S3 Copy statements with the following "
                        "syntax: COPY <table_name> FROM [(column 1, [column2, [..]])] '"
                        "<file path on S3 bucket>' "
                        "credentials 'aws_access_key_id=<aws_access_key_id>;"
                        "aws_secret_access_key=<aws_secret_access_key>' "
                        "Supportred AWS credentials format: "
                        "[with ]credentials[ AS] 'aws_secret_access_key=y; aws_access_key_id=x'"
                        " No Support for additional credential formats, eg IAM roles, etc, yet."
                    )

    # Fetching GZIP Flag
    params["gzip"] = False
    for token in tokens:
        if strip(token.lower()) == "gzip":
            params["gzip"] = True

    # Fetching delimiter
    for index, token in enumerate(tokens):
        if token.lower() == "delimiter":
            try:
                if tokens[index + 1].lower() != "as":
                    params["delimiter"] = strip(tokens[index + 1])
                else:
                    params["delimiter"] = strip(tokens[index + 2])
            except IndexError:
                raise ValueError(
                    "Possibly malformed Delimiter Format. "
                    f"Statement = {statement}"
                    "Redshift fixture only supports S3 Unload statements with the following"
                    "syntax: UNLOAD ('select-statement') TO 's3://object-path/name-prefix'"
                    "authorization 'aws_access_key_id=<aws_access_key_id>;"
                    "aws_secret_access_key=<aws_secret_access_key>'"
                    "[GZIP] [DELIMITER [ AS ] 'delimiter-char']"
                )
    return params


def _mock_s3_unload(
    select_statement,
    s3_uri,
    aws_secret_access_key,
    aws_access_key_id,
    cursor,
    delimiter,
    is_gzipped,
):
    """Execute patched 'unload' command."""
    # Parsing s3 uri
    ending_index = len(s3_uri)
    path_to_file = s3_uri[5:ending_index]
    bucket, key = path_to_file.split("/", 1)

    cursor.execute(select_statement)
    result = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    buffer = get_data_csv(
        result, column_names=column_names, is_gzipped=is_gzipped, delimiter=delimiter
    )

    # Push the data to the S3 Bucket.
    conn = boto3.resource(
        "s3", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key
    )
    conn.create_bucket(Bucket=bucket)
    obj = conn.Object(bucket, key)
    obj.put(Body=buffer)


def get_data_csv(rows, column_names, is_gzipped=False, delimiter="|", **additional_to_csv_options):
    result = io.BytesIO()
    buffer = result
    if is_gzipped:
        buffer = gzip.GzipFile(fileobj=buffer, mode="wb")

    wrapper = io.TextIOWrapper(buffer)

    writer = csv.DictWriter(
        wrapper,
        fieldnames=column_names,
        delimiter=delimiter,
        quoting=csv.QUOTE_MINIMAL,
        quotechar='"',
        lineterminator="\n",
        skipinitialspace=True,
        doublequote=True,
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(zip(column_names, row)))

    wrapper.detach()

    if is_gzipped:
        buffer.close()

    result.seek(0)
    return result
