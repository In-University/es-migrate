## Field datatypes

Elasticsearch supports a number of different datatypes for the fields in a
document:

[float]
### Core datatypes

string::        [`text`](#text) and [`keyword`](#keyword)
[number](#number)::    `long`, `integer`, `short`, `byte`, `double`, `float`, `half_float`, `scaled_float`
[date](#date)::      `date`
[boolean](#boolean)::   `boolean`
[binary](#binary)::    `binary`
[range](#range)::     `integer_range`, `float_range`, `long_range`, `double_range`, `date_range`, `ip_range`

[float]
### Complex datatypes
[object](#object)::    `object` for single JSON objects
[nested](#nested)::    `nested` for arrays of JSON objects

[float]
### Geo datatypes

[geo-point](#geo-point)::     `geo_point` for lat/lon points
[geo-shape](#geo-shape)::     `geo_shape` for complex shapes like polygons

[float]
### Specialised datatypes

[ip](#ip)::            `ip` for IPv4 and IPv6 addresses
**[Completion datatype](#search-suggesters-completion)**:
                    `completion` to provide auto-complete suggestions
[token-count](#token-count)::   `token_count` to count the number of tokens in a string
{plugins}/mapper-murmur3.html[`mapper-murmur3`]:: `murmur3` to compute hashes of values at index-time and store them in the index
{plugins}/mapper-annotated-text.html[`mapper-annotated-text`]:: `annotated-text` to index text containing special markup (typically used for identifying named entities)

[percolator](#percolator)::    Accepts queries from the query-dsl

[parent-join](#parent-join)::   Defines parent/child relation for documents within the same index

[alias](#alias)::         Defines an alias to an existing field.

[float]
### Arrays
In Elasticsearch, arrays do not require a dedicated field datatype. Any field can contain
zero or more values by default, however, all values in the array must be of the
same datatype. See [array](#array).

[float]
### Multi-fields

It is often useful to index the same field in different ways for different
purposes. For instance, a `string` field could be mapped as
a `text` field for full-text search, and as a `keyword` field for
sorting or aggregations.  Alternatively, you could index a text field with
the [`standard` analyzer](#analysis-standard-analyzer), the
[`english`](#english-analyzer) analyzer, and the
[`french` analyzer](#french-analyzer).

This is the purpose of _multi-fields_.  Most datatypes support multi-fields
via the [multi-fields](#multi-fields) parameter.

include::types/alias.asciidoc[]

include::types/array.asciidoc[]

include::types/binary.asciidoc[]

include::types/range.asciidoc[]

include::types/boolean.asciidoc[]

include::types/date.asciidoc[]

include::types/geo-point.asciidoc[]

include::types/geo-shape.asciidoc[]

include::types/ip.asciidoc[]

include::types/keyword.asciidoc[]

include::types/nested.asciidoc[]

include::types/numeric.asciidoc[]

include::types/object.asciidoc[]

include::types/text.asciidoc[]

include::types/token-count.asciidoc[]

include::types/percolator.asciidoc[]

include::types/parent-join.asciidoc[]