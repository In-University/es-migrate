### Binary datatype

The `binary` type accepts a binary value as a
[Base64](https://en.wikipedia.org/wiki/Base64) encoded string. The field is not
stored by default and is not searchable:

[source,js]
--------------------------------------------------
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "name": {
          "type": "text"
        },
        "blob": {
          "type": "binary"
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "name": "Some binary blob",
  "blob": "U29tZSBiaW5hcnkgYmxvYg==" <1>
}
--------------------------------------------------
// CONSOLE
<1> The Base64 encoded binary value must not have embedded newlines `\n`.

#### Parameters for `binary` fields

The following parameters are accepted by `binary` fields:

[horizontal]

**[`doc_values`](#doc-values)**:

    Should the field be stored on disk in a column-stride fashion, so that it
    can later be used for sorting, aggregations, or scripting? Accepts `true`
    or `false` (default).

**[`store`](#mapping-store)**:

    Whether the field value should be stored and retrievable separately from
    the [`_source`](#mapping-source-field) field. Accepts `true` or `false`
    (default).