import pytest
from sqlalchemy import text

from pytest_mock_resources import create_redshift_fixture
from pytest_mock_resources.compat import psycopg2
from pytest_mock_resources.patch.redshift.redshift_ddl import (
    is_create_table,
    strip_redshift_table_options,
)


class TestStripRedshiftTableOptions:
    def test_strip_distkey(self):
        sql = "CREATE TABLE t (c INT) DISTKEY(c)"
        assert strip_redshift_table_options(sql) == "CREATE TABLE t (c INT)"

    def test_strip_sortkey_single_column(self):
        sql = "CREATE TABLE t (c INT) SORTKEY(c)"
        assert strip_redshift_table_options(sql) == "CREATE TABLE t (c INT)"

    def test_strip_sortkey_multiple_columns(self):
        sql = "CREATE TABLE t (c1 INT, c2 INT) SORTKEY(c1, c2)"
        assert strip_redshift_table_options(sql) == "CREATE TABLE t (c1 INT, c2 INT)"

    def test_strip_compound_sortkey(self):
        sql = "CREATE TABLE t (c1 INT, c2 INT) COMPOUND SORTKEY(c1, c2)"
        assert strip_redshift_table_options(sql) == "CREATE TABLE t (c1 INT, c2 INT)"

    def test_strip_interleaved_sortkey(self):
        sql = "CREATE TABLE t (c1 INT, c2 INT) INTERLEAVED SORTKEY(c1, c2)"
        assert strip_redshift_table_options(sql) == "CREATE TABLE t (c1 INT, c2 INT)"

    def test_strip_sortkey_auto(self):
        sql = "CREATE TABLE t (c INT) SORTKEY AUTO"
        assert strip_redshift_table_options(sql) == "CREATE TABLE t (c INT)"

    @pytest.mark.parametrize("style", ["AUTO", "EVEN", "KEY", "ALL"])
    def test_strip_diststyle(self, style):
        sql = f"CREATE TABLE t (c INT) DISTSTYLE {style}"
        assert strip_redshift_table_options(sql) == "CREATE TABLE t (c INT)"

    def test_strip_distkey_and_sortkey_combined(self):
        sql = "CREATE TABLE t (c1 INT, c2 VARCHAR(20)) DISTKEY(c1) SORTKEY(c1, c2);"
        assert strip_redshift_table_options(sql) == "CREATE TABLE t (c1 INT, c2 VARCHAR(20));"

    def test_strip_case_insensitive(self):
        sql = "create table t (c int) distkey(c) sortkey(c)"
        assert strip_redshift_table_options(sql) == "create table t (c int)"

    def test_passthrough_when_no_redshift_clauses(self):
        sql = "CREATE TABLE t (c INT)"
        assert strip_redshift_table_options(sql) == sql

    def test_does_not_match_keywords_inside_identifiers(self):
        sql = (
            "CREATE TABLE example_distkey_sortkey "
            "(col1 INT, col2 VARCHAR(20)) DISTKEY(col1) SORTKEY(col1, col2);"
        )
        expected = "CREATE TABLE example_distkey_sortkey (col1 INT, col2 VARCHAR(20));"
        assert strip_redshift_table_options(sql) == expected


class TestIsCreateTable:
    def test_matches_create_table(self):
        assert is_create_table("CREATE TABLE t (c INT)")

    def test_matches_create_temp_table(self):
        assert is_create_table("CREATE TEMP TABLE t (c INT)")

    def test_matches_create_temporary_table(self):
        assert is_create_table("CREATE TEMPORARY TABLE t (c INT)")

    def test_matches_with_leading_whitespace(self):
        assert is_create_table("  \n  CREATE TABLE t (c INT)")

    def test_case_insensitive(self):
        assert is_create_table("create table t (c INT)")

    def test_rejects_select(self):
        assert not is_create_table("SELECT * FROM t")

    def test_rejects_insert(self):
        assert not is_create_table("INSERT INTO t VALUES (1)")

    def test_rejects_create_index(self):
        assert not is_create_table("CREATE INDEX idx ON t (c)")


redshift = create_redshift_fixture()


def test_create_table_with_distkey_and_sortkey(redshift):
    statement = (
        "CREATE TABLE example_distkey_sortkey ("
        " col1 INT,"
        " col2 VARCHAR(20)"
        ") DISTKEY(col1) SORTKEY(col1, col2);"
    )
    with redshift.begin() as conn:
        conn.execute(text(statement))


def test_create_table_with_diststyle(redshift):
    statement = "CREATE TABLE example_diststyle (col1 INT) DISTSTYLE ALL;"
    with redshift.begin() as conn:
        conn.execute(text(statement))


def test_create_table_with_distkey_via_psycopg2(redshift):
    config = redshift.pmr_credentials.as_psycopg2_kwargs()
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cursor:
            cursor.execute("CREATE TABLE example_distkey_psycopg2 (col1 INT) DISTKEY(col1);")
