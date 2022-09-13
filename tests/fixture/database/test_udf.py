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
                dict(interval_str=interval_str, num=num, date_or_datetime=date_or_datetime),
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
                dict(
                    interval_str=interval_str,
                    date_or_datetime_1=date_or_datetime_1,
                    date_or_datetime_2=date_or_datetime_2,
                ),
            )

            result = result.fetchall()

        assert len(result) == 1
        assert len(result[0]) == 1
        assert result[0][0] == expected

        with redshift.connect() as conn:
            result = conn.execute(
                text("SELECT DATEDIFF(:interval_str, :date_or_datetime_2, :date_or_datetime_1);"),
                dict(
                    interval_str=interval_str,
                    date_or_datetime_2=date_or_datetime_2,
                    date_or_datetime_1=date_or_datetime_1,
                ),
            )

            result = result.fetchall()

        assert len(result) == 1
        assert len(result[0]) == 1
        assert result[0][0] == expected * -1

    def test_datediff_invalid_unit(self, redshift):
        with redshift.connect() as conn, pytest.raises(InternalError):
            conn.execute(
                text("SELECT DATEDIFF(:interval_str, :date_or_datetime_2, :date_or_datetime_1);"),
                dict(
                    interval_str="invalid",
                    date_or_datetime_2=date(2018, 1, 1),
                    date_or_datetime_1=date(2018, 1, 1),
                ),
            )

    def test_left_integer(self, redshift):
        with redshift.connect() as conn:
            result = conn.execute(
                text("SELECT LEFT(1234, 2)")
            )

            result = result.fetchone()

            assert result[0] == 12

    def test_right_integer(self, redshift):
        with redshift.connect() as conn:
            result = conn.execute(
                text("SELECT RIGHT(1234, 2)")
            )

            result = result.fetchone()

            assert result[0] == 34
