import csv
import random
from io import BytesIO

import boto3
import pandas as pd
import sqlalchemy
from moto import mock_s3
from pandas.util.testing import assert_frame_equal
from sqlalchemy.sql import text

from pytest_mock_resources import create_redshift_fixture

redshift = create_redshift_fixture()

original_df = pd.DataFrame(
    data=[(3342, 32434.0, "a", "gfhsdgaf"), (3343, 0, "b", None), (0, 32434.0, None, "gfhsdgaf")],
    columns=["i", "f", "c", "v"],
)

values_as_list = original_df.get_values().tolist()

UNLOAD_TEMPLATE = (
    "{COMMAND} ({SELECT_STATEMENT}) {TO} '{LOCATION}' "
    "{AUTHORIZATION} 'aws_access_key_id=AAAAAAAAAAAAAAAAAAAA;"
    "aws_secret_access_key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' "
    "{OPTIONAL_ARGS}"
)


def _get_dataframe_csv(dataframe, is_gzipped=False, **additional_to_csv_options):
    """Converts a Pandas DF to CSV."""
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


def _read_dataframe_csv(file, is_gzipped=False, sep="|"):
    compression = "infer"
    if is_gzipped:
        compression = "gzip"

    return pd.read_csv(
        BytesIO(file),
        sep=sep,
        encoding="utf8",
        quoting=csv.QUOTE_NONE,
        doublequote=False,
        escapechar="\\",
        low_memory=False,
        compression=compression,
    )


def _setup_table_and_insert_data(engine):
    engine.execute(
        "CREATE TEMP TABLE test_s3_unload_from_redshift (i INT, f FLOAT, c CHAR(1), v VARCHAR(16));"
    )

    engine.execute(
        (
            "INSERT INTO test_s3_unload_from_redshift(i, f, c, v)"
            " values(3342, 32434.0, 'a', 'gfhsdgaf'), (3343, 0, 'b', NULL), "
            "(0, 32434.0, NULL, 'gfhsdgaf')"
        )
    )


def _fetch_values_from_s3_and_assert(file_name="myfile.csv", is_gzipped=False, sep="|"):
    s3 = boto3.client(
        "s3",
        aws_access_key_id="AAAAAAAAAAAAAAAAAAAA",
        aws_secret_access_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    response = s3.get_object(Bucket="mybucket", Key=file_name)
    dataframe = _read_dataframe_csv(response["Body"].read(), is_gzipped, sep)
    assert_frame_equal(dataframe, original_df)


def _randomcase(s):
    return "".join(c.upper() if random.randint(0, 1) else c.lower() for c in s)


@mock_s3
def test_unload(redshift):
    """Test if a file is created with the appropriate data."""
    _setup_table_and_insert_data(redshift)

    redshift.execute(
        UNLOAD_TEMPLATE.format(
            COMMAND="UNLOAD",
            SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
            TO="TO",
            LOCATION="s3://mybucket/myfile.csv",
            AUTHORIZATION="AUTHORIZATION",
            OPTIONAL_ARGS="",
        )
    )

    _fetch_values_from_s3_and_assert(is_gzipped=False)


@mock_s3
def test_unload_case_senesitivity(redshift):
    """Test case sensitivity for UNLOAD command."""
    _setup_table_and_insert_data(redshift)

    redshift.execute(
        UNLOAD_TEMPLATE.format(
            COMMAND=_randomcase("UNLOAD"),
            SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
            TO=_randomcase("TO"),
            LOCATION="s3://mybucket/myfile.csv",
            AUTHORIZATION=_randomcase("AUTHORIZATION"),
            OPTIONAL_ARGS="",
        )
    )

    _fetch_values_from_s3_and_assert(is_gzipped=False)


@mock_s3
def test_unload_gzipped(redshift):
    """Test gzip support."""
    _setup_table_and_insert_data(redshift)

    redshift.execute(
        UNLOAD_TEMPLATE.format(
            COMMAND="UNLOAD",
            SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
            TO="TO",
            LOCATION="s3://mybucket/myfile.csv.gz",
            AUTHORIZATION="AUTHORIZATION",
            OPTIONAL_ARGS="GZIP",
        )
    )

    _fetch_values_from_s3_and_assert(file_name="myfile.csv.gz", is_gzipped=True)


@mock_s3
def test_inverted_credentials_string(redshift):
    """Test parsing with an inverted credentials string."""
    _setup_table_and_insert_data(redshift)

    redshift.execute(
        (
            "{COMMAND} ({SELECT_STATEMENT}) {TO} '{LOCATION}' "
            "{AUTHORIZATION} 'aws_secret_access_key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA;"
            "aws_access_key_id=AAAAAAAAAAAAAAAAAAAA'"
            "{OPTIONAL_ARGS};"
        ).format(
            COMMAND="UNLOAD",
            SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
            TO="TO",
            LOCATION="s3://mybucket/myfile.csv",
            AUTHORIZATION="AUTHORIZATION",
            OPTIONAL_ARGS="",
        )
    )

    _fetch_values_from_s3_and_assert(is_gzipped=False)


@mock_s3
def test_optional_keywords(redshift):
    """Test command with optimal keyword arguments."""
    _setup_table_and_insert_data(redshift)

    redshift.execute(
        UNLOAD_TEMPLATE.format(
            COMMAND="UNLOAD",
            SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
            TO="TO",
            LOCATION="s3://mybucket/myfile.csv",
            AUTHORIZATION="WITH AUTHORIZATION AS",
            OPTIONAL_ARGS="DELIMITER AS ','",
        )
    )

    _fetch_values_from_s3_and_assert(is_gzipped=False, sep=",")


@mock_s3
def test_random_spacing(redshift):
    """Test command with random spaces."""
    _setup_table_and_insert_data(redshift)

    redshift.execute(
        UNLOAD_TEMPLATE.format(
            COMMAND="  UNLOAD           ",
            SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
            TO="   TO          ",
            LOCATION="s3://mybucket/myfile.csv",
            AUTHORIZATION="   AUTHORIZATION         ",
            OPTIONAL_ARGS="   DELIMITER     AS      ','",
        )
    )

    _fetch_values_from_s3_and_assert(is_gzipped=False, sep=",")


@mock_s3
def test_ignores_sqlalchmey_text_obj(redshift):
    """Test command ignores SQLAlchemy Text Objects and raises error."""
    _setup_table_and_insert_data(redshift)
    try:
        redshift.execute(
            text(
                UNLOAD_TEMPLATE.format(
                    COMMAND=" UNLOAD",
                    SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
                    TO="TO",
                    LOCATION="s3://mybucket/myfile.csv",
                    AUTHORIZATION="AUTHORIZATION",
                    OPTIONAL_ARGS="DELIMITER AS ','",
                )
            )
        )

    # The default engine will try to execute an `UNLOAD` command and will fail, raising a
    # ProgrammingError
    except sqlalchemy.exc.ProgrammingError:
        return


@mock_s3
def test_multiple_sql_statemts(redshift):
    redshift.execute(
        (
            "CREATE TEMP TABLE test_s3_unload_from_redshift "
            "(i INT, f FLOAT, c CHAR(1), v VARCHAR(16));"
            "INSERT INTO test_s3_unload_from_redshift(i, f, c, v)"
            " values(3342, 32434.0, 'a', 'gfhsdgaf'), (3343, 0, 'b', NULL), "
            "(0, 32434.0, NULL, 'gfhsdgaf');"
            "{COMMAND} ({SELECT_STATEMENT}) {TO} '{LOCATION}' "
            "{AUTHORIZATION} 'aws_access_key_id=AAAAAAAAAAAAAAAAAAAA;"
            "aws_secret_access_key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' "
            "{OPTIONAL_ARGS}".format(
                COMMAND="UNLOAD",
                SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
                TO="TO",
                LOCATION="s3://mybucket/myfile.csv",
                AUTHORIZATION="AUTHORIZATION",
                OPTIONAL_ARGS="",
            )
        )
    )

    _fetch_values_from_s3_and_assert(is_gzipped=False)
