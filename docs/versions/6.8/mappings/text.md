### Text datatype

A field to index full-text values, such as the body of an email or the
description of a product. These fields are `analyzed`, that is they are passed through an
[analyzer](#analysis) to convert the string into a list of individual terms
before being indexed. The analysis process allows Elasticsearch to search for
individual words _within_  each full text field.  Text fields are not
used for sorting and seldom used for aggregations (although the
[significant text aggregation](#search-aggregations-bucket-significanttext-aggregation)
is a notable exception).

If you need to index structured content such as email addresses, hostnames, status
codes, or tags, it is likely that you should rather use a [`keyword`](#keyword) field.

Below is an example of a mapping for a text field:

[source,js]
--------------------------------
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "full_name": {
          "type":  "text"
        }
      }
    }
  }
}
--------------------------------
// CONSOLE

#### Use a field as both text and keyword
Sometimes it is useful to have both a full text (`text`) and a keyword
(`keyword`) version of the same field: one for full text search and the
other for aggregations and sorting. This can be achieved with
[multi-fields](#multi-fields).

#### Parameters for text fields

The following parameters are accepted by `text` fields:

[horizontal]

**[`analyzer`](#analyzer)**:

    The [analyzer](#analysis) which should be used for
    [`analyzed`](#mapping-index) string fields, both at index-time and at
    search-time (unless overridden by the  [`search_analyzer`](#search-analyzer)).
    Defaults to the default index analyzer, or the
    [`standard` analyzer](#analysis-standard-analyzer).

**[`boost`](#mapping-boost)**:

    Mapping field-level query time boosting. Accepts a floating point number, defaults
    to `1.0`.

**[`eager_global_ordinals`](#eager-global-ordinals)**:

    Should global ordinals be loaded eagerly on refresh? Accepts `true` or `false`
    (default). Enabling this is a good idea on fields that are frequently used for
    (significant) terms aggregations.

**[`fielddata`](#fielddata)**:

    Can the field use in-memory fielddata for sorting, aggregations,
    or scripting? Accepts `true` or `false` (default).

**[`fielddata_frequency_filter`](#field-data-filtering)**:

    Expert settings which allow to decide which values to load in memory when `fielddata`
    is enabled. By default all values are loaded.

**[`fields`](#multi-fields)**:

    Multi-fields allow the same string value to be indexed in multiple ways for
    different purposes, such as one field for search and a multi-field for
    sorting and aggregations, or the same string value analyzed by different
    analyzers.

**[`index`](#mapping-index)**:

    Should the field be searchable? Accepts `true` (default) or `false`.

**[`index_options`](#index-options)**:

    What information should be stored in the index, for search and highlighting purposes.
    Defaults to `positions`.

**[`index_prefixes`](#index-prefixes)**:

    If enabled, term prefixes of between 2 and 5 characters are indexed into a
    separate field.  This allows prefix searches to run more efficiently, at
    the expense of a larger index.

**[`index_phrases`](#index-phrases)**:

    If enabled, two-term word combinations ('shingles') are indexed into a separate
    field.  This allows exact phrase queries to run more efficiently, at the expense
    of a larger index.  Note that this works best when stopwords are not removed,
    as phrases containing stopwords will not use the subsidiary field and will fall
    back to a standard phrase query.  Accepts `true` or `false` (default).

**[`norms`](#norms)**:

    Whether field-length should be taken into account when scoring queries.
    Accepts `true` (default) or `false`.

**[`position_increment_gap`](#position-increment-gap)**:

    The number of fake term position which should be inserted between each
    element of an array of strings. Defaults to the `position_increment_gap`
    configured on the analyzer which defaults to `100`. `100` was chosen because it
    prevents phrase queries with reasonably large slops (less than 100) from
    matching terms across field values.

**[`store`](#mapping-store)**:

    Whether the field value should be stored and retrievable separately from
    the [`_source`](#mapping-source-field) field. Accepts `true` or `false`
    (default).

**[`search_analyzer`](#search-analyzer)**:

    The [`analyzer`](#analyzer) that should be used at search time on
    [`analyzed`](#mapping-index) fields. Defaults to the `analyzer` setting.

**[`search_quote_analyzer`](#search-quote-analyzer)**:

    The [`analyzer`](#analyzer) that should be used at search time when a
    phrase is encountered. Defaults to the `search_analyzer` setting.

**[`similarity`](#similarity)**:

    Which scoring algorithm or _similarity_ should be used. Defaults
    to `BM25`.

**[`term_vector`](#term-vector)**:

    Whether term vectors should be stored for an [`analyzed`](#mapping-index)
    field. Defaults to `no`.