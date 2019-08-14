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


date_add_kwargs = dict(
    body="SELECT d + (n::VARCHAR || i)::INTERVAL", language=UdfLanguage.SQL.value
)

date_add_date = create_udf(
    name="DATE_ADD",
    args="i VARCHAR, n INTEGER, d DATE",
    returns="TIMESTAMP WITHOUT TIME ZONE",
    **date_add_kwargs
)

date_add_timestamp = create_udf(
    name="DATE_ADD",
    args="i VARCHAR, n INTEGER, d TIMESTAMP WITHOUT TIME ZONE",
    returns="TIMESTAMP WITHOUT TIME ZONE",
    **date_add_kwargs
)

date_add_timestamptz = create_udf(
    name="DATE_ADD",
    args="i VARCHAR, n INTEGER, d TIMESTAMP WITH TIME ZONE",
    returns="TIMESTAMP WITH TIME ZONE",
    **date_add_kwargs
)


date_diff_kwargs = dict(
    returns="BIGINT",
    # Credit: https://gist.github.com/JoshuaGross/18b9bb1db8021efc88884cbd8dc8fddb
    body="""
       DECLARE
         diff_interval INTERVAL;
         diff INT = 0;
         years_diff INT = 0;

       BEGIN
         IF units NOT IN (
         'year',
         'month',
         'week',
         'day',
         'hour',
         'minute',
         'second'
         ) THEN
           RAISE EXCEPTION 'Invalid unit %% specified', units;
         END IF;

         IF units IN (
         'year',
         'month'
         ) THEN
           years_diff = DATE_PART('year', end_t) - DATE_PART('year', start_t);

           IF units = 'year' THEN
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

         IF units = 'week' THEN
           diff = diff/7;
           RETURN diff::BIGINT;
         END IF;

         IF units = 'day' THEN
           RETURN diff::BIGINT;
         END IF;

         diff = diff * 24 + DATE_PART('hour', diff_interval);

         IF units = 'hour' THEN
            RETURN diff::BIGINT;
         END IF;

         diff = diff * 60 + DATE_PART('minute', diff_interval);

         IF units = 'minute' THEN
            RETURN diff::BIGINT;
         END IF;

         diff = diff * 60 + DATE_PART('second', diff_interval);

         RETURN diff::BIGINT;

       END;
    """,
    language=UdfLanguage.PLPGSQL.value,
)

date_diff_date = create_udf(
    name="DATE_DIFF", args="units VARCHAR, start_t DATE, end_t DATE", **date_diff_kwargs
)

date_diff_timestamp = create_udf(
    name="DATE_DIFF", args="units VARCHAR, start_t TIMESTAMP, end_t TIMESTAMP", **date_diff_kwargs
)

date_diff_timestamptz = create_udf(
    name="DATE_DIFF",
    args="units VARCHAR, start_t TIMESTAMP WITH TIME ZONE, end_t TIMESTAMP WITH TIME ZONE",
    **date_diff_kwargs
)

PRESTO_UDFS = Statements(
    date_add_date,
    date_add_timestamp,
    date_add_timestamptz,
    date_diff_date,
    date_diff_timestamp,
    date_diff_timestamptz,
)
