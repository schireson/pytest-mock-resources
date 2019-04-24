import random

import boto3
import pandas
import psycopg2
from moto import mock_s3
from pandas.util.testing import assert_frame_equal
from sqlalchemy import create_engine

from pytest_mock_resources.patch.redshift.mock_s3_copy import read_dataframe_csv
from pytest_mock_resources.patch.redshift.mock_s3_unload import get_dataframe_csv

original_df = pandas.DataFrame(
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

UNLOAD_TEMPLATE = (
    "{COMMAND} ({SELECT_STATEMENT}) {TO} '{LOCATION}' "
    "{AUTHORIZATION} 'aws_access_key_id=AAAAAAAAAAAAAAAAAAAA;"
    "aws_secret_access_key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' "
    "{OPTIONAL_ARGS}"
)


def fetch_values_from_table_and_assert(engine):
    execute = engine.execute("SELECT * from test_s3_copy_into_redshift")
    results = [row for row in execute]
    engine.execute("DROP TABLE test_s3_copy_into_redshift")
    assert len(results) == len(values_as_list)
    for index, val in enumerate(results):
        assert results[index] == tuple(values_as_list[index])


def fetch_and_assert_psycopg2(cursor):
    cursor.execute("SELECT * from test_s3_copy_into_redshift")
    results = cursor.fetchall()
    assert len(results) == len(values_as_list)
    for index, val in enumerate(results):
        assert results[index] == tuple(values_as_list[index])
    cursor.execute("DROP TABLE test_s3_copy_into_redshift")


def setup_table_and_bucket(redshift, file_name="file.csv"):
    redshift.execute(
        "CREATE TABLE test_s3_copy_into_redshift (i INT, f FLOAT, c CHAR(1), v VARCHAR(16));"
    )
    redshift.execute("COMMIT;")

    conn = boto3.resource(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="AAAAAAAAAAAAAAAAAAAA",
        aws_secret_access_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    conn.create_bucket(Bucket="mybucket")
    conn.Object("mybucket", file_name).put(Body=get_dataframe_csv(original_df).encode())


def setup_table_and_insert_data(engine):
    engine.execute(
        "CREATE TABLE test_s3_unload_from_redshift (i INT, f FLOAT, c CHAR(1), v VARCHAR(16));"
    )
    engine.execute("COMMIT;")

    engine.execute(
        (
            "INSERT INTO test_s3_unload_from_redshift(i, f, c, v)"
            " values(3342, 32434.0, 'a', 'gfhsdgaf'), (3343, 0, 'b', NULL), "
            "(0, 32434.0, NULL, 'gfhsdgaf')"
        )
    )


def fetch_values_from_s3_and_assert(engine, file_name="myfile.csv", is_gzipped=False, sep="|"):
    s3 = boto3.client(
        "s3",
        aws_access_key_id="AAAAAAAAAAAAAAAAAAAA",
        aws_secret_access_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    response = s3.get_object(Bucket="mybucket", Key=file_name)
    dataframe = read_dataframe_csv(response["Body"].read(), is_gzipped=is_gzipped, sep=sep)
    assert_frame_equal(dataframe, original_df)
    engine.execute("DROP TABLE test_s3_unload_from_redshift")


def randomcase(s):
    return "".join(c.upper() if random.randint(0, 1) else c.lower() for c in s)


@mock_s3
def copy_fn_to_test_create_engine_patch(redshift):
    engine = create_engine(redshift.url)
    setup_table_and_bucket(engine)

    engine.execute(
        COPY_TEMPLATE.format(
            COMMAND="COPY",
            LOCATION="s3://mybucket/file.csv",
            COLUMNS="",
            FROM="from",
            CREDENTIALS="credentials",
            OPTIONAL_ARGS="",
        )
    )

    fetch_values_from_table_and_assert(engine)


@mock_s3
def copy_fn_to_test_psycopg2_connect_patch(config):
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()
    setup_table_and_bucket(cursor)

    cursor.execute(
        COPY_TEMPLATE.format(
            COMMAND="COPY",
            LOCATION="s3://mybucket/file.csv",
            COLUMNS="",
            FROM="from",
            CREDENTIALS="credentials",
            OPTIONAL_ARGS="",
        )
    )

    fetch_and_assert_psycopg2(cursor)


@mock_s3
def copy_fn_to_test_psycopg2_connect_patch_as_context_manager(config):
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cursor:
            setup_table_and_bucket(cursor)

            cursor.execute(
                COPY_TEMPLATE.format(
                    COMMAND="COPY",
                    LOCATION="s3://mybucket/file.csv",
                    COLUMNS="",
                    FROM="from",
                    CREDENTIALS="credentials",
                    OPTIONAL_ARGS="",
                )
            )

            fetch_and_assert_psycopg2(cursor)


@mock_s3()
def unload_fn_to_test_create_engine_patch(redshift):
    engine = create_engine(redshift.url)
    setup_table_and_insert_data(engine)
    engine.execute(
        UNLOAD_TEMPLATE.format(
            COMMAND="UNLOAD",
            SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
            TO="TO",
            LOCATION="s3://mybucket/myfile.csv",
            AUTHORIZATION="AUTHORIZATION",
            OPTIONAL_ARGS="",
        )
    )

    fetch_values_from_s3_and_assert(engine, is_gzipped=False)


@mock_s3()
def unload_fn_to_test_psycopg2_connect_patch(config):
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()
    setup_table_and_insert_data(cursor)

    cursor.execute(
        UNLOAD_TEMPLATE.format(
            COMMAND="UNLOAD",
            SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
            TO="TO",
            LOCATION="s3://mybucket/myfile.csv",
            AUTHORIZATION="AUTHORIZATION",
            OPTIONAL_ARGS="",
        )
    )

    fetch_values_from_s3_and_assert(cursor, is_gzipped=False)


@mock_s3()
def unload_fn_to_test_psycopg2_connect_patch_as_context_manager(config):
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cursor:
            setup_table_and_insert_data(cursor)

            cursor.execute(
                UNLOAD_TEMPLATE.format(
                    COMMAND="UNLOAD",
                    SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
                    TO="TO",
                    LOCATION="s3://mybucket/myfile.csv",
                    AUTHORIZATION="AUTHORIZATION",
                    OPTIONAL_ARGS="",
                )
            )

            fetch_values_from_s3_and_assert(cursor, is_gzipped=False)
