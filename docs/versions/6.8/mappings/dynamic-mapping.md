## Dynamic Mapping

One of the most important features of Elasticsearch is that it tries to get
out of your way and let you start exploring your data as quickly as possible.
To index a document, you don't have to first create an index, define a mapping
type, and define your fields -- you can just index a document and the index,
type, and fields will spring to life automatically:

[source,js]
--------------------------------------------------
PUT data/_doc/1 <1>
{ "count": 5 }
--------------------------------------------------
// CONSOLE
<1> Creates the `data` index, the `_doc` mapping type, and a field
    called `count` with datatype `long`.

The automatic detection and addition of new fields is called
_dynamic mapping_. The dynamic mapping rules can be customised to suit your
purposes with:

**[Dynamic field mappings](#dynamic-field-mapping)**:

    The rules governing dynamic field detection.

**[Dynamic templates](#dynamic-templates)**:

    Custom rules to configure the mapping for dynamically added fields.

TIP: [Index templates](#indices-templates) allow you to configure the default
mappings, settings and aliases for new indices, whether created
automatically or explicitly.

include::dynamic/field-mapping.asciidoc[]

include::dynamic/templates.asciidoc[]

include::dynamic/default-mapping.asciidoc[]