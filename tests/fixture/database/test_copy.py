from __future__ import unicode_literals

import time

import boto3
import moto
import pytest
from sqlalchemy import text

from pytest_mock_resources import create_redshift_fixture
from tests.fixture.database import (
    COPY_TEMPLATE,
    fetch_values_from_table_and_assert,
    get_data_csv,
    original_data,
    randomcase,
    ResultProxy,
    setup_table_and_bucket,
)

redshift = create_redshift_fixture()


@moto.mock_s3
@pytest.mark.redshift
def test_s3_copy_into_redshift(redshift):
    setup_table_and_bucket(redshift)

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

    # Assert the values fetched for the database are the same as the values in the data.
    fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
@pytest.mark.redshift
def test_case_sensitivity(redshift):
    setup_table_and_bucket(redshift)

    redshift.execute(
        COPY_TEMPLATE.format(
            COMMAND=randomcase("copy"),
            LOCATION="s3://mybucket/file.csv",
            COLUMNS="",
            FROM=randomcase("from"),
            CREDENTIALS=randomcase("CREDENTIALS"),
            OPTIONAL_ARGS="",
        )
    )

    # Assert case sensitivity doesn't affect parsing.
    fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
@pytest.mark.redshift
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

    file = get_data_csv(ResultProxy(original_data), is_gzipped=True, path_or_buf=temp_file_name)

    conn.Object("mybucket", "file.csv.gz").put(Body=file)
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

    # Assert support for gzipped files.
    fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
@pytest.mark.redshift
def test_s3_copy_columns(redshift):
    setup_table_and_bucket(redshift)

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
    fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
@pytest.mark.redshift
def test_inverted_credentials_string(redshift):
    setup_table_and_bucket(redshift)

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
    fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
@pytest.mark.redshift
def test_optional_keywords(redshift):
    setup_table_and_bucket(redshift)

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
    fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
@pytest.mark.redshift
def test_random_spacing(redshift):
    setup_table_and_bucket(redshift)

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
    fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
@pytest.mark.redshift
def test_ignores_sqlalchmey_text_obj(redshift):
    setup_table_and_bucket(redshift)

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
    fetch_values_from_table_and_assert(redshift)


@moto.mock_s3
@pytest.mark.redshift
def test_multiple_sql_statemts(redshift):
    conn = boto3.resource(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="AAAAAAAAAAAAAAAAAAAA",
        aws_secret_access_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    conn.create_bucket(Bucket="mybucket")
    conn.Object("mybucket", "file.csv").put(Body=get_data_csv(ResultProxy(original_data)))

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

    fetch_values_from_table_and_assert(redshift)
