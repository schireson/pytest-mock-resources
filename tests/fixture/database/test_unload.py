import sqlalchemy
from sqlalchemy.sql import text

from pytest_mock_resources import create_redshift_fixture
from pytest_mock_resources.compat import moto
from tests import skip_if_sqlalchemy2
from tests.fixture.database import (
    fetch_values_from_s3_and_assert,
    randomcase,
    setup_table_and_insert_data,
    UNLOAD_TEMPLATE,
)

redshift = create_redshift_fixture()


def test_unload(redshift):
    """Test if a file is created with the appropriate data."""
    with moto.mock_s3():
        setup_table_and_insert_data(redshift)

        with redshift.begin() as conn:
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

        fetch_values_from_s3_and_assert(redshift, is_gzipped=False)


def test_unload_case_senesitivity(redshift):
    """Test case sensitivity for UNLOAD command."""
    with moto.mock_s3():
        setup_table_and_insert_data(redshift)

        with redshift.begin() as conn:
            conn.execute(
                text(
                    UNLOAD_TEMPLATE.format(
                        COMMAND=randomcase("UNLOAD"),
                        SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
                        TO=randomcase("TO"),
                        LOCATION="s3://mybucket/myfile.csv",
                        AUTHORIZATION=randomcase("AUTHORIZATION"),
                        OPTIONAL_ARGS="",
                    )
                )
            )

        fetch_values_from_s3_and_assert(redshift, is_gzipped=False)


def test_unload_gzipped(redshift):
    """Test gzip support."""
    with moto.mock_s3():
        setup_table_and_insert_data(redshift)

        with redshift.begin() as conn:
            conn.execute(
                text(
                    UNLOAD_TEMPLATE.format(
                        COMMAND="UNLOAD",
                        SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
                        TO="TO",
                        LOCATION="s3://mybucket/myfile.csv.gz",
                        AUTHORIZATION="AUTHORIZATION",
                        OPTIONAL_ARGS="GZIP",
                    )
                )
            )

        fetch_values_from_s3_and_assert(redshift, file_name="myfile.csv.gz", is_gzipped=True)


def test_inverted_credentials_string(redshift):
    """Test parsing with an inverted credentials string."""
    with moto.mock_s3():
        setup_table_and_insert_data(redshift)

        with redshift.begin() as conn:
            conn.execute(
                text(
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
            )

        fetch_values_from_s3_and_assert(redshift, is_gzipped=False)


def test_optional_keywords(redshift):
    """Test command with optimal keyword arguments."""
    with moto.mock_s3():
        setup_table_and_insert_data(redshift)

        with redshift.begin() as conn:
            conn.execute(
                text(
                    UNLOAD_TEMPLATE.format(
                        COMMAND="UNLOAD",
                        SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
                        TO="TO",
                        LOCATION="s3://mybucket/myfile.csv",
                        AUTHORIZATION="WITH AUTHORIZATION AS",
                        OPTIONAL_ARGS="DELIMITER AS ','",
                    )
                )
            )

        fetch_values_from_s3_and_assert(redshift, is_gzipped=False, delimiter=",")


def test_random_spacing(redshift):
    """Test command with random spaces."""
    with moto.mock_s3():
        setup_table_and_insert_data(redshift)

        with redshift.begin() as conn:
            conn.execute(
                text(
                    UNLOAD_TEMPLATE.format(
                        COMMAND="  UNLOAD           ",
                        SELECT_STATEMENT="select * from test_s3_unload_from_redshift",
                        TO="   TO          ",
                        LOCATION="s3://mybucket/myfile.csv",
                        AUTHORIZATION="   AUTHORIZATION         ",
                        OPTIONAL_ARGS="   DELIMITER     AS      ','",
                    )
                )
            )

        fetch_values_from_s3_and_assert(redshift, is_gzipped=False, delimiter=",")


def test_ignores_sqlalchmey_text_obj(redshift):
    """Test command ignores SQLAlchemy Text Objects and raises error."""
    with moto.mock_s3():
        setup_table_and_insert_data(redshift)
        try:
            with redshift.begin() as conn:
                conn.execute(
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


@skip_if_sqlalchemy2
def test_multiple_sql_statemts(redshift):
    with moto.mock_s3():
        with redshift.begin() as conn:
            conn.execute(
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

        fetch_values_from_s3_and_assert(redshift, is_gzipped=False)
