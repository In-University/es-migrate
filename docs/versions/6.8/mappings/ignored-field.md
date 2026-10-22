### `_ignored` field

added[6.4.0]

The `_ignored` field indexes and stores the names of every field in a document
that has been ignored because it was malformed and
[`ignore_malformed`](#ignore-malformed) was turned on.

This field is searchable with [`term`](#query-dsl-term-query),
[`terms`](#query-dsl-terms-query) and [`exists`](#query-dsl-exists-query)
queries, and is returned as part of the search hits.

For instance the below query matches all documents that have one or more fields
that got ignored:

[source,js]
--------------------------------------------------
GET _search
{
  "query": {
    "exists": {
      "field": "_ignored"
    }
  }
}
--------------------------------------------------
// CONSOLE

Similarly, the below query finds all documents whose `@timestamp` field was
ignored at index time:

[source,js]
--------------------------------------------------
GET _search
{
  "query": {
    "term": {
      "_ignored": "@timestamp"
    }
  }
}
--------------------------------------------------
// CONSOLE