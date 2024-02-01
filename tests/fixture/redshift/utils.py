import random

from sqlalchemy import create_engine, text

from pytest_mock_resources.compat import boto3, moto, psycopg2
from pytest_mock_resources.patch.redshift.mock_s3_copy import read_data_csv
from pytest_mock_resources.patch.redshift.mock_s3_unload import get_data_csv

original_data = [
    (3342, 32434.0, "a", "gfhsdgaf"),
    (3343, 0.0, "b", None),
    (0, 32434.0, None, "gfhsdgaf"),
]
data_columns = ["i", "f", "c", "v"]


def empty_as_string(row, stringify_value=False, c_space=True):
    result = {}
    for key, value in dict(zip(data_columns, row)).items():
        if value is None:
            if c_space and key == "c":
                row_value = " "
            else:
                row_value = ""
        else:
            row_value = value
            if stringify_value:
                row_value = str(value)

        result[key] = row_value
    return result


COPY_TEMPLATE = (
    "{COMMAND} test_s3_copy_into_redshift {COLUMNS} {FROM} '{LOCATION}' "
    "{CREDENTIALS} 'aws_access_key_id=AAAAAAAAAAAAAAAAAAAA;"
    "aws_secret_access_key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' "
    "{OPTIONAL_ARGS};"
)

UNLOAD_TEMPLATE = (
    "{COMMAND} ({SELECT_STATEMENT}) {TO} '{LOCATION}' "
    "{AUTHORIZATION} 'aws_access_key_id=AAAAAAAAAAAAAAAAAAAA;"
    "aws_secret_access_key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' "
    "{OPTIONAL_ARGS}"
)


def fetch_values_from_table_and_assert(engine):
    with engine.connect() as conn:
        execute = conn.execute(text("SELECT * from test_s3_copy_into_redshift"))
    results = list(execute)
    assert len(results) == len(original_data)
    for index, val in enumerate(results):
        assert empty_as_string(results[index]) == empty_as_string(original_data[index])


def fetch_and_assert_psycopg2(cursor):
    cursor.execute("SELECT * from test_s3_copy_into_redshift")
    results = cursor.fetchall()
    assert len(results) == len(original_data)
    for result, original in zip(results, original_data):
        og_data = empty_as_string(original)
        expected_result = tuple(og_data.values())
        print(result)
        print(expected_result)
        assert result == expected_result


def setup_table_and_bucket(redshift, file_name="file.csv", create_bucket=True, cursor=False):
    statement = (
        "CREATE TABLE test_s3_copy_into_redshift (i INT, f FLOAT, c CHAR(1), v VARCHAR(16));"
    )
    if cursor:
        redshift.execute(statement)
    else:
        with redshift.begin() as conn:
            conn.execute(text(statement))

    conn = boto3.resource(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="AAAAAAAAAAAAAAAAAAAA",
        aws_secret_access_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    if create_bucket:
        conn.create_bucket(Bucket="mybucket")

    conn.Object("mybucket", file_name).put(Body=get_data_csv(original_data, data_columns))


def setup_table_and_insert_data(engine, cursor=False):
    create = "CREATE TABLE test_s3_unload_from_redshift (i INT, f FLOAT, c CHAR(1), v VARCHAR(16))"
    insert = (
        "INSERT INTO test_s3_unload_from_redshift(i, f, c, v)"
        " values(3342, 32434.0, 'a', 'gfhsdgaf'), (3343, 0, 'b', NULL), "
        "(0, 32434.0, NULL, 'gfhsdgaf')"
    )

    if cursor:
        engine.execute(create)
        engine.execute(insert)
        engine.execute("COMMIT;")
    else:
        with engine.begin() as conn:
            conn.execute(text(create))
            conn.execute(text(insert))


def fetch_values_from_s3_and_assert(
    engine, file_name="myfile.csv", is_gzipped=False, delimiter="|"
):
    s3 = boto3.client(
        "s3",
        aws_access_key_id="AAAAAAAAAAAAAAAAAAAA",
        aws_secret_access_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    response = s3.get_object(Bucket="mybucket", Key=file_name)
    data = read_data_csv(response["Body"].read(), is_gzipped=is_gzipped, delimiter=delimiter)
    assert data == [empty_as_string(f, stringify_value=True, c_space=False) for f in original_data]


def randomcase(s):
    return "".join(c.upper() if random.randint(0, 1) else c.lower() for c in s)


def copy_fn_to_test_create_engine_patch(redshift):
    with moto.mock_s3():
        engine = create_engine(redshift.url)
        setup_table_and_bucket(redshift)

        with engine.begin() as conn:
            conn.execute(
                text(
                    COPY_TEMPLATE.format(
                        COMMAND="COPY",
                        LOCATION="s3://mybucket/file.csv",
                        COLUMNS="",
                        FROM="from",
                        CREDENTIALS="credentials",
                        OPTIONAL_ARGS="",
                    )
                )
            )

        fetch_values_from_table_and_assert(engine)


def copy_fn_to_test_psycopg2_connect_patch(config):
    with moto.mock_s3():
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        setup_table_and_bucket(cursor, cursor=True)

        cursor.execute(
            COPY_TEMPLATE.format(
                COMMAND="COPY",
                LOCATION="s3://mybucket/file.csv",
                COLUMNS="(i, f, c, v)",
                FROM="from",
                CREDENTIALS="credentials",
                OPTIONAL_ARGS="EMPTYASNULL",
            )
        )

        fetch_and_assert_psycopg2(cursor)


def copy_fn_to_test_psycopg2_connect_patch_as_context_manager(config):
    with moto.mock_s3():
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cursor:
                setup_table_and_bucket(cursor, cursor=True)

                cursor.execute(
                    COPY_TEMPLATE.format(
                        COMMAND="COPY",
                        LOCATION="s3://mybucket/file.csv",
                        COLUMNS="(i, f, c, v)",
                        FROM="from",
                        CREDENTIALS="credentials",
                        OPTIONAL_ARGS="",
                    )
                )

                fetch_and_assert_psycopg2(cursor)


def unload_fn_to_test_create_engine_patch(redshift):
    with moto.mock_s3():
        engine = create_engine(redshift.url)
        setup_table_and_insert_data(engine)
        with engine.begin() as conn:
            conn.execute(
                text(
                    UNLOAD_TEMPLATE.format(
                        COMMAND="UNLOAD",
                        SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
                        TO="TO",
                        LOCATION="s3://mybucket/myfile.csv",
                        AUTHORIZATION="AUTHORIZATION",
                        OPTIONAL_ARGS="",
                    )
                )
            )

        fetch_values_from_s3_and_assert(engine, is_gzipped=False)


def unload_fn_to_test_psycopg2_connect_patch(config):
    with moto.mock_s3():
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        setup_table_and_insert_data(cursor, cursor=True)

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


def unload_fn_to_test_psycopg2_connect_patch_as_context_manager(config):
    with moto.mock_s3():
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cursor:
                setup_table_and_insert_data(cursor, cursor=True)

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
