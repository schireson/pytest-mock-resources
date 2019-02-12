import enum

from pytest_mock_resources.fixture.database import Statements


@enum.unique
class UdfLanguage(enum.Enum):
    PLPGSQL = "plpgsql"
    PLPYTHON = "plpythonu"
    SQL = "SQL"


def create_udf(name, args, returns, body, language, schema="public"):
    _template = """
    CREATE FUNCTION {schema}.{name} ({args}) RETURNS {returns} AS $${body}$$ LANGUAGE {language};
    """

    return _template.format(
        schema=schema, name=name, args=args, returns=returns, body=body, language=language
    )


dateadd_kwargs = dict(body="SELECT d + (n::VARCHAR || i)::INTERVAL", language=UdfLanguage.SQL.value)

dateadd_date = create_udf(
    name="DATEADD",
    args="i VARCHAR, n INTEGER, d DATE",
    returns="TIMESTAMP WITHOUT TIME ZONE",
    **dateadd_kwargs
)

dateadd_timestamp = create_udf(
    name="DATEADD",
    args="i VARCHAR, n INTEGER, d TIMESTAMP WITHOUT TIME ZONE",
    returns="TIMESTAMP WITHOUT TIME ZONE",
    **dateadd_kwargs
)

dateadd_timestamptz = create_udf(
    name="DATEADD",
    args="i VARCHAR, n INTEGER, d TIMESTAMP WITH TIME ZONE",
    returns="TIMESTAMP WITH TIME ZONE",
    **dateadd_kwargs
)

date_add_date = create_udf(
    name="DATE_ADD",
    args="i VARCHAR, n INTEGER, d DATE",
    returns="TIMESTAMP WITHOUT TIME ZONE",
    **dateadd_kwargs
)

date_add_timestamp = create_udf(
    name="DATE_ADD",
    args="i VARCHAR, n INTEGER, d TIMESTAMP WITHOUT TIME ZONE",
    returns="TIMESTAMP WITHOUT TIME ZONE",
    **dateadd_kwargs
)

date_add_timestamptz = create_udf(
    name="DATE_ADD",
    args="i VARCHAR, n INTEGER, d TIMESTAMP WITH TIME ZONE",
    returns="TIMESTAMP WITH TIME ZONE",
    **dateadd_kwargs
)


datediff_kwargs = dict(
    returns="BIGINT",
    # Credit: https://gist.github.com/JoshuaGross/18b9bb1db8021efc88884cbd8dc8fddb
    body="""
       DECLARE
         diff_interval INTERVAL;
         diff INT = 0;
         years_diff INT = 0;

       BEGIN
         IF units NOT IN (
         'y', 'yr', 'yrs', 'year', 'years',
         'month', 'months', 'mon', 'mons',
         'week', 'weeks', 'w',
         'day', 'days', 'd',
         'hour', 'hours', 'h', 'hr', 'hrs',
         'minute', 'minutes', 'm', 'min', 'mins',
         'second', 'seconds'
         ) THEN
           RAISE EXCEPTION 'Invalid unit %% specified', units;
         END IF;

         IF units IN (
         'y', 'yr', 'yrs', 'year', 'years',
         'month', 'months', 'mon', 'mons'
         ) THEN
           years_diff = DATE_PART('year', end_t) - DATE_PART('year', start_t);

           IF units IN ('y', 'yr', 'yrs', 'year', 'years') THEN
             RETURN years_diff::BIGINT;
           ELSE
             RETURN (
             years_diff * 12 + (DATE_PART('month', end_t) - DATE_PART('month', start_t))
             )::BIGINT;
           END IF;
         END IF;

         IF pg_typeof(start_t) = pg_typeof(DATE('2000-01-01')) THEN
           diff_interval = (end_t - start_t) * '1 day'::INTERVAL;
         ELSE
           diff_interval = (end_t - start_t);
         END IF;

         diff = diff + DATE_PART('day', diff_interval);

         IF units IN ('week', 'weeks', 'w') THEN
           diff = diff/7;
           RETURN diff::BIGINT;
         END IF;

         IF units IN ('day', 'days', 'd') THEN
           RETURN diff::BIGINT;
         END IF;

         diff = diff * 24 + DATE_PART('hour', diff_interval);

         IF units IN ('hour', 'hours', 'h', 'hr', 'hrs') THEN
            RETURN diff::BIGINT;
         END IF;

         diff = diff * 60 + DATE_PART('minute', diff_interval);

         IF units IN ('minute', 'minutes', 'm', 'min', 'mins') THEN
            RETURN diff::BIGINT;
         END IF;

         diff = diff * 60 + DATE_PART('second', diff_interval);

         RETURN diff::BIGINT;

       END;
    """,
    language=UdfLanguage.PLPGSQL.value,
)

datediff_date = create_udf(
    name="DATEDIFF", args="units VARCHAR, start_t DATE, end_t DATE", **datediff_kwargs
)

datediff_timestamp = create_udf(
    name="DATEDIFF", args="units VARCHAR, start_t TIMESTAMP, end_t TIMESTAMP", **datediff_kwargs
)

datediff_timestamptz = create_udf(
    name="DATEDIFF",
    args="units VARCHAR, start_t TIMESTAMP WITH TIME ZONE, end_t TIMESTAMP WITH TIME ZONE",
    **datediff_kwargs
)

REDSHIFT_UDFS = Statements(
    dateadd_date,
    dateadd_timestamp,
    dateadd_timestamptz,
    date_add_date,
    date_add_timestamp,
    date_add_timestamptz,
    datediff_date,
    datediff_timestamp,
    datediff_timestamptz,
)
