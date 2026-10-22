**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/field-data-types).

## Field datatypes

Elasticsearch supports a number of different datatypes for the fields in a
document:

### Core datatypes

string

[`text`](text.html) and [`keyword`](keyword.html)

[Numeric datatypes](number.html)

`long`, `integer`, `short`, `byte`, `double`, `float`, `half_float`, `scaled_float`

[Date datatype](date.html)

`date`

[Boolean datatype](boolean.html)

`boolean`

[Binary datatype](binary.html)

`binary`

[Range datatypes](range.html)

`integer_range`, `float_range`, `long_range`, `double_range`, `date_range`, `ip_range`

### Complex datatypes

[Object datatype](object.html)

`object` for single JSON objects

[Nested datatype](nested.html)

`nested` for arrays of JSON objects

### Geo datatypes

[Geo-point datatype](geo-point.html)

`geo_point` for lat/lon points

[Geo-Shape datatype](geo-shape.html)

`geo_shape` for complex shapes like polygons

### Specialised datatypes

[IP datatype](ip.html)

`ip` for IPv4 and IPv6 addresses

[Completion datatype](search-suggesters-completion.html)

`completion` to provide auto-complete suggestions

[Token count datatype](token-count.html)

`token_count` to count the number of tokens in a string

[`mapper-murmur3`](/guide/en/elasticsearch/plugins/6.8/mapper-murmur3.html)

`murmur3` to compute hashes of values at index-time and store them in the index

[`mapper-annotated-text`](/guide/en/elasticsearch/plugins/6.8/mapper-annotated-text.html)

`annotated-text` to index text containing special markup (typically used for identifying named entities)

[Percolator type](percolator.html)

Accepts queries from the query-dsl

[`join` datatype](parent-join.html)

Defines parent/child relation for documents within the same index

[Alias datatype](alias.html)

Defines an alias to an existing field.

### Arrays

In Elasticsearch, arrays do not require a dedicated field datatype. Any field can contain
zero or more values by default, however, all values in the array must be of the
same datatype. See [Arrays](array.html).

### Multi-fields

It is often useful to index the same field in different ways for different
purposes. For instance, a `string` field could be mapped as
a `text` field for full-text search, and as a `keyword` field for
sorting or aggregations.  Alternatively, you could index a text field with
the [`standard` analyzer](analysis-standard-analyzer.html), the
[`english`](analysis-lang-analyzer.html#english-analyzer) analyzer, and the
[`french` analyzer](analysis-lang-analyzer.html#french-analyzer).

This is the purpose of *multi-fields*.  Most datatypes support multi-fields
via the [`fields`](multi-fields.html) parameter.