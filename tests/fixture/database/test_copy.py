import csv
import os
import random
import time

import boto3
import moto
import pandas as pd
from sqlalchemy import text

from pytest_mock_resources import create_redshift_fixture

redshift = create_redshift_fixture()

original_df = pd.DataFrame(
    data=[(3342, 32434.0, "a", "gfhsdgaf"), (3343, 0, "b", None), (0, 32434.0, None, "gfhsdgaf")],
    columns=["i", "f", "c", "v"],
)

values_as_list = original_df.get_values().tolist()

COPY_TEMPLATE = (
    "{COMMAND} test_s3_copy_into_redshift {COLUMNS} {FROM} '{LOCATION}' "
    "{CREDENTIALS} 'aws_access_key_id=AAAAAAAAAAAAAAAAAAAA;"
    "aws_secret_access_key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'"
    "{OPTIONAL_ARGS};"
)


def get_dataframe_csv(dataframe, is_gzipped=False, **additional_to_csv_options):
    compression = "infer"
    if is_gzipped:
        compression = "gzip"
    content = dataframe.to_csv(
        sep="|",
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


def _fetch_values_from_table_and_assert(redshift):
    execute = redshift.execute("SELECT * from test_s3_copy_into_redshift")
    results = [row for row in execute]
    redshift.execute("DROP TABLE test_s3_copy_into_redshift")
    assert len(results) == len(values_as_list)
    for index, val in enumerate(results):
        assert results[index] == tuple(values_as_list[index])


def _setup_table_and_bucket(redshift, file_name="file.csv"):
    redshift.execute(
        "CREATE TEMP TABLE test_s3_copy_into_redshift (i INT, f FLOAT, c CHAR(1), v VARCHAR(16));"
    )

    conn = boto3.resource(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="AAAAAAAAAAAAAAAAAAAA",
        aws_secret_access_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    conn.create_bucket(Bucket="mybucket")
    conn.Object("mybucket", file_name).put(Body=get_dataframe_csv(original_df).encode())


def _randomcase(s):
    result = ""
    for c in s:
        case = random.randint(0, 1)
        if case == 0:
            result += c.upper()
        else:
            result += c.lower()
    return result


@moto.mock_s3
def test_s3_copy_into_redshift(redshift):
    _setup_table_and_bucket(redshift)

    redshift.execute(
        COPY_TEMPLATE.format(
            COMMAND="COPY",
            LOCATION="s3://mybucket/file.csv",
            COLUMNS="",
            FROM="from",
            CREDENTIALS="credentials",
            OPTIONAL_ARGS="",
        )
    )

    # Assert the values fetched for the database are the same as the values in the dataframe.
    _fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
def test_case_sensitivity(redshift):
    _setup_table_and_bucket(redshift)

    redshift.execute(
        COPY_TEMPLATE.format(
            COMMAND=_randomcase("copy"),
            LOCATION="s3://mybucket/file.csv",
            COLUMNS="",
            FROM=_randomcase("from"),
            CREDENTIALS=_randomcase("CREDENTIALS"),
            OPTIONAL_ARGS="",
        )
    )

    # Assert case sensitivity doesn't affect parsing.
    _fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
def test_s3_copy_from_gzip(redshift):
    redshift.execute(
        "CREATE TEMP TABLE test_s3_copy_into_redshift (i INT, f FLOAT, c CHAR(1), v VARCHAR(16));"
    )
    conn = boto3.resource(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="AAAAAAAAAAAAAAAAAAAA",
        aws_secret_access_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    conn.create_bucket(Bucket="mybucket")

    temp_file_name = "file_{time_in_mills}.csv.gz".format(
        time_in_mills=int(round(time.time() * 1000))
    )

    get_dataframe_csv(original_df, is_gzipped=True, path_or_buf=temp_file_name)

    conn.Object("mybucket", "file.csv.gz").put(Body=open(temp_file_name, "rb"))
    redshift.execute(
        COPY_TEMPLATE.format(
            COMMAND="COPY",
            LOCATION="s3://mybucket/file.csv.gz",
            COLUMNS="",
            CREDENTIALS="credentials",
            FROM="from",
            OPTIONAL_ARGS="",
        )
    )

    os.remove(temp_file_name)

    # Assert support for gzipped files.
    _fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
def test_s3_copy_columns(redshift):
    _setup_table_and_bucket(redshift)

    redshift.execute(
        COPY_TEMPLATE.format(
            COMMAND="copy",
            LOCATION="s3://mybucket/file.csv",
            COLUMNS="(i, f, c, v)",
            FROM="from",
            CREDENTIALS="credentials",
            OPTIONAL_ARGS="",
        )
    )

    # Assert support for Columns
    _fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
def test_inverted_credentials_string(redshift):
    _setup_table_and_bucket(redshift)

    redshift.execute(
        (
            "{COMMAND} test_s3_copy_into_redshift {COLUMNS} from '{LOCATION}' "
            "credentials 'aws_secret_access_key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA;"
            "aws_access_key_id=AAAAAAAAAAAAAAAAAAAA'"
        ).format(
            COMMAND="COPY",
            LOCATION="s3://mybucket/file.csv",
            COLUMNS="",
            FROM="from",
            CREDENTIALS="credentials",
            OPTIONAL_ARGS="",
        )
    )

    # Assert order for credentials is irrelavant
    _fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
def test_optional_keywords(redshift):
    _setup_table_and_bucket(redshift)

    redshift.execute(
        COPY_TEMPLATE.format(
            COMMAND="COPY",
            LOCATION="s3://mybucket/file.csv",
            COLUMNS="",
            FROM="from",
            CREDENTIALS="with credentials as",
            OPTIONAL_ARGS="GZIP delimiter '|' region 'us-west-2'",
        )
    )

    # Assert optional keywords are ignored.
    _fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
def test_random_spacing(redshift):
    _setup_table_and_bucket(redshift)

    redshift.execute(
        COPY_TEMPLATE.format(
            COMMAND="COPY",
            LOCATION="s3://mybucket/file.csv",
            COLUMNS="( i ,   f,  c,    v )",
            FROM="from",
            CREDENTIALS="credentials",
            OPTIONAL_ARGS="",
        ).replace(" ", "    ")
    )

    # Assert irregular spaces doesn't affect parsing.
    _fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
def test_ignores_sqlalchmey_text_obj(redshift):
    _setup_table_and_bucket(redshift)

    redshift.execute(
        text(
            (
                "INSERT INTO test_s3_copy_into_redshift(i, f, c, v)"
                " values(3342, 32434.0, 'a', 'gfhsdgaf'), (3343, 0, 'b', NULL), "
                "(0, 32434.0, NULL, 'gfhsdgaf')"
            )
        )
    )

    # SQL command as a SQLAlchemy TextClause objetct is ignored and the default engine executes
    # the command.
    _fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
def test_multiple_sql_statemts(redshift):
    conn = boto3.resource(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="AAAAAAAAAAAAAAAAAAAA",
        aws_secret_access_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    conn.create_bucket(Bucket="mybucket")
    conn.Object("mybucket", "file.csv").put(Body=get_dataframe_csv(original_df).encode())

    redshift.execute(
        (
            "CREATE TEMP TABLE test_s3_copy_into_redshift "
            "(i INT, f FLOAT, c CHAR(1), v VARCHAR(16));"
            "{COMMAND} test_s3_copy_into_redshift {COLUMNS} {FROM} '{LOCATION}' "
            "{CREDENTIALS} 'aws_access_key_id=AAAAAAAAAAAAAAAAAAAA;"
            "aws_secret_access_key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'"
            "{OPTIONAL_ARGS};".format(
                COMMAND="COPY",
                LOCATION="s3://mybucket/file.csv",
                COLUMNS="(i, f, c, v)",
                FROM="from",
                CREDENTIALS="credentials",
                OPTIONAL_ARGS="",
            )
        )
    )

    _fetch_values_from_table_and_assert(redshift)
