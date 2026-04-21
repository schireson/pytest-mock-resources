import enum

from sqlalchemy import text

from pytest_mock_resources.sqlalchemy import Statements


@enum.unique
class UdfLanguage(enum.Enum):
    PLPGSQL = "plpgsql"
    PLPYTHON = "plpythonu"
    SQL = "SQL"


def create_udf(name, args, returns, body, language, schema="public"):
    _template = """
    CREATE FUNCTION {schema}.{name} ({args}) RETURNS {returns} AS $${body}$$ LANGUAGE {language};
    """

    return text(
        _template.format(
            schema=schema,
            name=name,
            args=args,
            returns=returns,
            body=body,
            language=language,
        )
    )


left_integer = create_udf(
    name="LEFT",
    args="s1 INTEGER, s2 INTEGER",
    returns="INTEGER",
    body="SELECT LEFT(s1::TEXT, s2)::INTEGER",
    language=UdfLanguage.SQL.value,
)

right_integer = create_udf(
    name="RIGHT",
    args="s1 INTEGER, s2 INTEGER",
    returns="INTEGER",
    body="SELECT RIGHT(s1::TEXT, s2)::INTEGER",
    language=UdfLanguage.SQL.value,
)

dateadd_kwargs = {
    "body": "SELECT d + (n::VARCHAR || i)::INTERVAL",
    "language": UdfLanguage.SQL.value,
}

dateadd_date = create_udf(
    name="DATEADD",
    args="i VARCHAR, n INTEGER, d DATE",
    returns="TIMESTAMP WITHOUT TIME ZONE",
    **dateadd_kwargs,
)

dateadd_timestamp = create_udf(
    name="DATEADD",
    args="i VARCHAR, n INTEGER, d TIMESTAMP WITHOUT TIME ZONE",
    returns="TIMESTAMP WITHOUT TIME ZONE",
    **dateadd_kwargs,
)

dateadd_timestamptz = create_udf(
    name="DATEADD",
    args="i VARCHAR, n INTEGER, d TIMESTAMP WITH TIME ZONE",
    returns="TIMESTAMP WITH TIME ZONE",
    **dateadd_kwargs,
)

date_add_date = create_udf(
    name="DATE_ADD",
    args="i VARCHAR, n INTEGER, d DATE",
    returns="TIMESTAMP WITHOUT TIME ZONE",
    **dateadd_kwargs,
)

date_add_timestamp = create_udf(
    name="DATE_ADD",
    args="i VARCHAR, n INTEGER, d TIMESTAMP WITHOUT TIME ZONE",
    returns="TIMESTAMP WITHOUT TIME ZONE",
    **dateadd_kwargs,
)

date_add_timestamptz = create_udf(
    name="DATE_ADD",
    args="i VARCHAR, n INTEGER, d TIMESTAMP WITH TIME ZONE",
    returns="TIMESTAMP WITH TIME ZONE",
    **dateadd_kwargs,
)

len_varchar = create_udf(
    name="LEN",
    args="s VARCHAR",
    returns="INTEGER",
    body="SELECT LENGTH(s)",
    language=UdfLanguage.SQL.value,
)

convert_timezone = create_udf(
    name="CONVERT_TIMEZONE",
    args="source_tz VARCHAR, target_tz VARCHAR, ts TIMESTAMP",
    returns="TIMESTAMP",
    body="SELECT ts AT TIME ZONE source_tz AT TIME ZONE target_tz",
    language=UdfLanguage.SQL.value,
)

convert_timezone_no_source = create_udf(
    name="CONVERT_TIMEZONE",
    args="target_tz VARCHAR, ts TIMESTAMP",
    returns="TIMESTAMP",
    body="SELECT ts AT TIME ZONE 'UTC' AT TIME ZONE target_tz",
    language=UdfLanguage.SQL.value,
)

# median is implemented by collecting inputs into an array via array_append
# and, in the final function, computing percentile_cont(0.5) over the
# unnested array. this matches redshift's MEDIAN semantics, which is
# equivalent to percentile_cont(0.5) within group (order by col).
_median_final_numeric = text(
    """
    CREATE FUNCTION public._median_final(NUMERIC[]) RETURNS NUMERIC AS $$
        SELECT (percentile_cont(0.5)
                WITHIN GROUP (ORDER BY v::double precision))::NUMERIC
        FROM unnest($1) AS v
        WHERE v IS NOT NULL;
    $$ LANGUAGE SQL IMMUTABLE;
    """
)

_median_final_double = text(
    """
    CREATE FUNCTION public._median_final(DOUBLE PRECISION[]) RETURNS DOUBLE PRECISION AS $$
        SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY v)
        FROM unnest($1) AS v
        WHERE v IS NOT NULL;
    $$ LANGUAGE SQL IMMUTABLE;
    """
)

median_numeric = text(
    """
    CREATE AGGREGATE public.median(NUMERIC) (
        SFUNC = array_append,
        STYPE = NUMERIC[],
        FINALFUNC = public._median_final,
        INITCOND = '{}'
    );
    """
)

median_double = text(
    """
    CREATE AGGREGATE public.median(DOUBLE PRECISION) (
        SFUNC = array_append,
        STYPE = DOUBLE PRECISION[],
        FINALFUNC = public._median_final,
        INITCOND = '{}'
    );
    """
)

# listagg concatenates non-null values into a single string with a
# delimiter. the two-argument state function coerces each input to text
# and appends it with the separator; the final function trims the leading
# separator. redshift also supports LISTAGG(col) without a delimiter,
# which defaults to an empty string between values.
_listagg_sfunc = text(
    """
    CREATE FUNCTION public._listagg_sfunc(state TEXT, value TEXT, delimiter TEXT)
    RETURNS TEXT AS $$
        SELECT CASE
            WHEN value IS NULL THEN state
            WHEN state IS NULL OR state = '' THEN value
            ELSE state || delimiter || value
        END;
    $$ LANGUAGE SQL IMMUTABLE;
    """
)

_listagg_sfunc_no_delim = text(
    """
    CREATE FUNCTION public._listagg_sfunc_no_delim(state TEXT, value TEXT)
    RETURNS TEXT AS $$
        SELECT CASE
            WHEN value IS NULL THEN state
            ELSE COALESCE(state, '') || value
        END;
    $$ LANGUAGE SQL IMMUTABLE;
    """
)

listagg_text_delim = text(
    """
    CREATE AGGREGATE public.listagg(TEXT, TEXT) (
        SFUNC = public._listagg_sfunc,
        STYPE = TEXT,
        INITCOND = ''
    );
    """
)

listagg_text = text(
    """
    CREATE AGGREGATE public.listagg(TEXT) (
        SFUNC = public._listagg_sfunc_no_delim,
        STYPE = TEXT,
        INITCOND = ''
    );
    """
)


datediff_kwargs = {
    "returns": "BIGINT",
    # Credit: https://gist.github.com/JoshuaGross/18b9bb1db8021efc88884cbd8dc8fddb
    "body": """
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
           RAISE EXCEPTION 'Invalid unit % specified', units;
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
    "language": UdfLanguage.PLPGSQL.value,
}

datediff_date = create_udf(
    name="DATEDIFF", args="units VARCHAR, start_t DATE, end_t DATE", **datediff_kwargs
)

datediff_timestamp = create_udf(
    name="DATEDIFF",
    args="units VARCHAR, start_t TIMESTAMP, end_t TIMESTAMP",
    **datediff_kwargs,
)

datediff_timestamptz = create_udf(
    name="DATEDIFF",
    args="units VARCHAR, start_t TIMESTAMP WITH TIME ZONE, end_t TIMESTAMP WITH TIME ZONE",
    **datediff_kwargs,
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
    left_integer,
    right_integer,
    len_varchar,
    convert_timezone,
    convert_timezone_no_source,
    _median_final_numeric,
    _median_final_double,
    median_numeric,
    median_double,
    _listagg_sfunc,
    _listagg_sfunc_no_delim,
    listagg_text_delim,
    listagg_text,
)
