### Date datatype

JSON doesn't have a date datatype, so dates in Elasticsearch can either be:

* strings containing formatted dates, e.g. `"2015-01-01"` or `"2015/01/01 12:10:30"`.
* a long number representing _milliseconds-since-the-epoch_.
* an integer representing _seconds-since-the-epoch_.

Internally, dates are converted to UTC (if the time-zone is specified) and
stored as a long number representing milliseconds-since-the-epoch.

Queries on dates are internally converted to range queries on this long
representation, and the result of aggregations and stored fields is converted
back to a string depending on the date format that is associated with the field.

NOTE: Dates will always be rendered as strings, even if they were initially
supplied as a long in the JSON document.

Date formats can be customised, but if no `format` is specified then it uses
the default:

    "strict_date_optional_time||epoch_millis"

This means that it will accept dates with optional timestamps, which conform
to the formats supported by [`strict_date_optional_time`](#strict-date-time)
or milliseconds-since-the-epoch.

For instance:

[source,js]
--------------------------------------------------
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "date": {
          "type": "date" <1>
        }
      }
    }
  }
}

PUT my_index/_doc/1
{ "date": "2015-01-01" } <2>

PUT my_index/_doc/2
{ "date": "2015-01-01T12:10:30Z" } <3>

PUT my_index/_doc/3
{ "date": 1420070400001 } <4>

GET my_index/_search
{
  "sort": { "date": "asc"} <5>
}
--------------------------------------------------
// CONSOLE
<1> The `date` field uses the default `format`.
<2> This document uses a plain date.
<3> This document includes a time.
<4> This document uses milliseconds-since-the-epoch.
<5> Note that the `sort` values that are returned are all in milliseconds-since-the-epoch.

#### Multiple date formats

Multiple formats can be specified by separating them with `||` as a separator.
Each format will be tried in turn until a matching format is found.  The first
format will be used to convert the _milliseconds-since-the-epoch_ value back
into a string.

[source,js]
--------------------------------------------------
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "date": {
          "type":   "date",
          "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
        }
      }
    }
  }
}
--------------------------------------------------
// CONSOLE

#### Parameters for `date` fields

The following parameters are accepted by `date` fields:

[horizontal]

**[`boost`](#mapping-boost)**:

    Mapping field-level query time boosting. Accepts a floating point number, defaults
    to `1.0`.

**[`doc_values`](#doc-values)**:

    Should the field be stored on disk in a column-stride fashion, so that it
    can later be used for sorting, aggregations, or scripting? Accepts `true`
    (default) or `false`.

**[`format`](#mapping-date-format)**:

    The date format(s) that can be parsed.  Defaults to
    `strict_date_optional_time||epoch_millis`.

**`locale`**:

    The locale to use when parsing dates since months do not have the same names
    and/or abbreviations in all languages. The default is the
    [`ROOT` locale](https://docs.oracle.com/javase/8/docs/api/java/util/Locale.html#ROOT),

**[`ignore_malformed`](#ignore-malformed)**:

    If `true`, malformed numbers are ignored. If `false` (default), malformed
    numbers throw an exception and reject the whole document.

**[`index`](#mapping-index)**:

    Should the field be searchable? Accepts `true` (default) and `false`.

**[`null_value`](#null-value)**:

    Accepts a date value in one of the configured +format+'s as the field
    which is substituted for any explicit `null` values.  Defaults to `null`,
    which means the field is treated as missing.

**[`store`](#mapping-store)**:

    Whether the field value should be stored and retrievable separately from
    the [`_source`](#mapping-source-field) field. Accepts `true` or `false`
    (default).