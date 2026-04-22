from datetime import date, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import InternalError

from pytest_mock_resources import create_redshift_fixture

redshift = create_redshift_fixture()


class TestUdf:
    @pytest.mark.parametrize(
        "interval_str,num,date_or_datetime,expected",
        (
            ("second", 1, date(2018, 1, 1), datetime(2018, 1, 1, 0, 0, 1)),
            ("minute", 1, date(2018, 1, 1), datetime(2018, 1, 1, 0, 1, 0)),
            ("hour", 1, date(2018, 1, 1), datetime(2018, 1, 1, 1, 0, 0)),
            ("day", 1, date(2018, 1, 1), datetime(2018, 1, 2, 0, 0, 0)),
            ("week", 1, date(2018, 1, 1), datetime(2018, 1, 8, 0, 0, 0)),
            ("month", 1, date(2018, 1, 1), datetime(2018, 2, 1, 0, 0, 0)),
            ("year", 1, date(2018, 1, 1), datetime(2019, 1, 1, 0, 0, 0)),
            ("second", 1, datetime(2018, 1, 1), datetime(2018, 1, 1, 0, 0, 1)),
            ("minute", 1, datetime(2018, 1, 1), datetime(2018, 1, 1, 0, 1, 0)),
            ("hour", 1, datetime(2018, 1, 1), datetime(2018, 1, 1, 1, 0, 0)),
            ("day", 1, datetime(2018, 1, 1), datetime(2018, 1, 2, 0, 0, 0)),
            ("week", 1, datetime(2018, 1, 1), datetime(2018, 1, 8, 0, 0, 0)),
            ("month", 1, datetime(2018, 1, 1), datetime(2018, 2, 1, 0, 0, 0)),
            ("year", 1, datetime(2018, 1, 1), datetime(2019, 1, 1, 0, 0, 0)),
            (
                "second",
                1,
                datetime(2018, 1, 1),
                datetime(2018, 1, 1, 0, 0, 1),
            ),
            (
                "minute",
                1,
                datetime(2018, 1, 1),
                datetime(2018, 1, 1, 0, 1, 0),
            ),
            (
                "hour",
                1,
                datetime(2018, 1, 1),
                datetime(2018, 1, 1, 1, 0, 0),
            ),
            (
                "day",
                1,
                datetime(2018, 1, 1),
                datetime(2018, 1, 2, 0, 0, 0),
            ),
            (
                "week",
                1,
                datetime(2018, 1, 1),
                datetime(2018, 1, 8, 0, 0, 0),
            ),
            (
                "month",
                1,
                datetime(2018, 1, 1),
                datetime(2018, 2, 1, 0, 0, 0),
            ),
            (
                "year",
                1,
                datetime(2018, 1, 1),
                datetime(2019, 1, 1, 0, 0, 0),
            ),
        ),
    )
    def test_date_add(self, redshift, interval_str, num, date_or_datetime, expected):
        with redshift.begin() as conn:
            result = conn.execute(
                text("SELECT DATE_ADD(:interval_str, :num, :date_or_datetime);"),
                {
                    "interval_str": interval_str,
                    "num": num,
                    "date_or_datetime": date_or_datetime,
                },
            )

            result = result.fetchall()

        assert len(result) == 1
        assert len(result[0]) == 1
        assert result[0][0] == expected

    @pytest.mark.parametrize(
        "interval_str,date_or_datetime_1,date_or_datetime_2,expected",
        (
            ("second", date(2018, 1, 1), date(2018, 1, 2), 86400),
            ("minute", date(2018, 1, 1), date(2018, 1, 2), 1440),
            ("hour", date(2018, 1, 1), date(2018, 1, 2), 24),
            ("day", date(2018, 1, 1), date(2018, 1, 2), 1),
            ("week", date(2018, 1, 1), date(2018, 1, 31), 4),
            ("month", date(2018, 1, 1), date(2018, 2, 1), 1),
            ("year", date(2018, 1, 1), date(2018, 12, 31), 0),
            ("year", date(2018, 12, 31), date(2019, 1, 1), 1),
            ("second", datetime(2018, 1, 1), datetime(2018, 1, 2), 86400),
            ("minute", datetime(2018, 1, 1), datetime(2018, 1, 2), 1440),
            ("hour", datetime(2018, 1, 1), datetime(2018, 1, 2), 24),
            ("day", datetime(2018, 1, 1), datetime(2018, 1, 2), 1),
            ("week", datetime(2018, 1, 1), datetime(2018, 1, 31), 4),
            ("month", datetime(2018, 1, 1), datetime(2018, 2, 1), 1),
            ("year", datetime(2018, 1, 1), datetime(2018, 12, 31), 0),
            ("year", datetime(2018, 12, 31), datetime(2019, 1, 1), 1),
            (
                "second",
                datetime(2018, 1, 1),
                datetime(2018, 1, 2),
                86400,
            ),
            (
                "minute",
                datetime(2018, 1, 1),
                datetime(2018, 1, 2),
                1440,
            ),
            (
                "hour",
                datetime(2018, 1, 1),
                datetime(2018, 1, 2),
                24,
            ),
            (
                "day",
                datetime(2018, 1, 1),
                datetime(2018, 1, 2),
                1,
            ),
            (
                "week",
                datetime(2018, 1, 1),
                datetime(2018, 1, 31),
                4,
            ),
            (
                "month",
                datetime(2018, 1, 1),
                datetime(2018, 2, 1),
                1,
            ),
            (
                "year",
                datetime(2018, 1, 1),
                datetime(2018, 12, 31),
                0,
            ),
            (
                "year",
                datetime(2018, 12, 31),
                datetime(2019, 1, 1),
                1,
            ),
        ),
    )
    def test_datediff(
        self, redshift, interval_str, date_or_datetime_1, date_or_datetime_2, expected
    ):
        with redshift.connect() as conn:
            result = conn.execute(
                text("SELECT DATEDIFF(:interval_str, :date_or_datetime_1, :date_or_datetime_2);"),
                {
                    "interval_str": interval_str,
                    "date_or_datetime_1": date_or_datetime_1,
                    "date_or_datetime_2": date_or_datetime_2,
                },
            )

            result = result.fetchall()

        assert len(result) == 1
        assert len(result[0]) == 1
        assert result[0][0] == expected

        with redshift.connect() as conn:
            result = conn.execute(
                text("SELECT DATEDIFF(:interval_str, :date_or_datetime_2, :date_or_datetime_1);"),
                {
                    "interval_str": interval_str,
                    "date_or_datetime_2": date_or_datetime_2,
                    "date_or_datetime_1": date_or_datetime_1,
                },
            )

            result = result.fetchall()

        assert len(result) == 1
        assert len(result[0]) == 1
        assert result[0][0] == expected * -1

    def test_datediff_invalid_unit(self, redshift):
        with redshift.connect() as conn, pytest.raises(InternalError):
            conn.execute(
                text("SELECT DATEDIFF(:interval_str, :date_or_datetime_2, :date_or_datetime_1);"),
                {
                    "interval_str": "invalid",
                    "date_or_datetime_2": date(2018, 1, 1),
                    "date_or_datetime_1": date(2018, 1, 1),
                },
            )

    def test_left_integer(self, redshift):
        with redshift.connect() as conn:
            result = conn.execute(text("SELECT LEFT(1234, 2)"))
            result = result.fetchone()
            assert result[0] == 12

    def test_right_integer(self, redshift):
        with redshift.connect() as conn:
            result = conn.execute(text("SELECT RIGHT(1234, 2)"))
            result = result.fetchone()
            assert result[0] == 34

    def test_len(self, redshift):
        with redshift.connect() as conn:
            result = conn.execute(text("SELECT len('1234')"))
            result = result.fetchone()
            assert result[0] == 4

    @pytest.mark.parametrize(
        "from_,to,date_,expected",
        [
            (
                "UTC",
                "America/New_York",
                "2018-01-01 00:00:00",
                datetime(2017, 12, 31, 19, 0, 0),
            ),
            (
                "America/New_York",
                "UTC",
                "2018-01-01 00:00:00",
                datetime(2018, 1, 1, 5, 0, 0),
            ),
            (
                "UTC",
                "Europe/Paris",
                "2024-06-01 10:00:00",
                datetime(2024, 6, 1, 12, 0, 0),
            ),
            (
                "UTC",
                "UTC",
                "2018-01-01 00:00:00",
                datetime(2018, 1, 1, 0, 0, 0),
            ),
        ],
    )
    def test_convert_timezone(self, redshift, from_, to, date_, expected):
        with redshift.connect() as conn:
            result = conn.execute(text(f"SELECT CONVERT_TIMEZONE('{from_}', '{to}', '{date_}')"))
            result = result.fetchone()
            assert result[0] == expected

    @pytest.mark.parametrize(
        "to,date_,expected",
        [
            (
                "America/New_York",
                "2018-01-01 00:00:00",
                datetime(2017, 12, 31, 19, 0, 0),
            ),
            (
                "UTC",
                "2018-01-01 00:00:00",
                datetime(2018, 1, 1, 0, 0, 0),
            ),
            (
                "Europe/Paris",
                "2024-06-01 10:00:00",
                datetime(2024, 6, 1, 12, 0, 0),
            ),
        ],
    )
    def test_convert_timezone_no_source(self, redshift, to, date_, expected):
        with redshift.connect() as conn:
            result = conn.execute(text(f"SELECT CONVERT_TIMEZONE('{to}', '{date_}')"))
            result = result.fetchone()
            assert result[0] == expected

    def test_median_odd_count(self, redshift):
        # odd number of values: the middle value is returned.
        with redshift.connect() as conn:
            conn.execute(text("CREATE TEMP TABLE t_median (v NUMERIC)"))
            conn.execute(text("INSERT INTO t_median VALUES (1), (2), (3), (4), (5)"))
            result = conn.execute(text("SELECT MEDIAN(v) FROM t_median")).fetchone()
            assert result[0] == 3

    def test_median_even_count(self, redshift):
        # even number of values: the average of the two middle values.
        with redshift.connect() as conn:
            conn.execute(text("CREATE TEMP TABLE t_median_even (v NUMERIC)"))
            conn.execute(text("INSERT INTO t_median_even VALUES (1), (2), (3), (4)"))
            result = conn.execute(text("SELECT MEDIAN(v) FROM t_median_even")).fetchone()
            assert result[0] == 2.5

    def test_median_ignores_nulls(self, redshift):
        # null values must be excluded from the computation.
        with redshift.connect() as conn:
            conn.execute(text("CREATE TEMP TABLE t_median_nulls (v NUMERIC)"))
            conn.execute(text("INSERT INTO t_median_nulls VALUES (1), (NULL), (3), (NULL), (5)"))
            result = conn.execute(text("SELECT MEDIAN(v) FROM t_median_nulls")).fetchone()
            assert result[0] == 3

    def test_median_grouped(self, redshift):
        # median per group should work like any aggregate.
        with redshift.connect() as conn:
            conn.execute(text("CREATE TEMP TABLE t_median_grp (g TEXT, v NUMERIC)"))
            conn.execute(
                text(
                    "INSERT INTO t_median_grp VALUES "
                    "('a', 1), ('a', 3), ('a', 5), ('b', 10), ('b', 20)"
                )
            )
            result = conn.execute(
                text("SELECT g, MEDIAN(v) FROM t_median_grp GROUP BY g ORDER BY g")
            ).fetchall()
            assert result == [("a", 3), ("b", 15)]

    def test_median_double_precision(self, redshift):
        # the double precision overload should work independently.
        with redshift.connect() as conn:
            conn.execute(text("CREATE TEMP TABLE t_median_dp (v DOUBLE PRECISION)"))
            conn.execute(text("INSERT INTO t_median_dp VALUES (1.5), (2.5), (3.5)"))
            result = conn.execute(text("SELECT MEDIAN(v) FROM t_median_dp")).fetchone()
            assert result[0] == 2.5

    def test_listagg_with_delimiter(self, redshift):
        # basic concatenation with a delimiter argument.
        with redshift.connect() as conn:
            conn.execute(text("CREATE TEMP TABLE t_listagg (v TEXT)"))
            conn.execute(text("INSERT INTO t_listagg VALUES ('a'), ('b'), ('c')"))
            result = conn.execute(
                text("SELECT LISTAGG(v, ',') FROM (SELECT v FROM t_listagg ORDER BY v) s")
            ).fetchone()
            assert result[0] == "a,b,c"

    def test_listagg_no_delimiter(self, redshift):
        # redshift supports LISTAGG(col) which concatenates with no separator.
        with redshift.connect() as conn:
            conn.execute(text("CREATE TEMP TABLE t_listagg_nd (v TEXT)"))
            conn.execute(text("INSERT INTO t_listagg_nd VALUES ('x'), ('y'), ('z')"))
            result = conn.execute(
                text("SELECT LISTAGG(v) FROM (SELECT v FROM t_listagg_nd ORDER BY v) s")
            ).fetchone()
            assert result[0] == "xyz"

    def test_listagg_ignores_nulls(self, redshift):
        # null values should be skipped entirely, not produce empty segments.
        with redshift.connect() as conn:
            conn.execute(text("CREATE TEMP TABLE t_listagg_nulls (v TEXT)"))
            conn.execute(text("INSERT INTO t_listagg_nulls VALUES ('a'), (NULL), ('b'), (NULL)"))
            result = conn.execute(
                text("SELECT LISTAGG(v, '|') FROM (SELECT v FROM t_listagg_nulls ORDER BY v) s")
            ).fetchone()
            assert result[0] == "a|b"

    def test_listagg_grouped(self, redshift):
        # listagg per group should work like any aggregate.
        with redshift.connect() as conn:
            conn.execute(text("CREATE TEMP TABLE t_listagg_grp (g TEXT, v TEXT)"))
            conn.execute(
                text(
                    "INSERT INTO t_listagg_grp VALUES "
                    "('a', 'x'), ('a', 'y'), ('b', 'p'), ('b', 'q')"
                )
            )
            result = conn.execute(
                text(
                    "SELECT g, LISTAGG(v, ',') "
                    "FROM (SELECT g, v FROM t_listagg_grp ORDER BY g, v) s "
                    "GROUP BY g ORDER BY g"
                )
            ).fetchall()
            assert result == [("a", "x,y"), ("b", "p,q")]
