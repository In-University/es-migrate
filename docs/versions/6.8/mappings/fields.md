## Meta-Fields

Each document has metadata associated with it, such as the `_index`, mapping
[`_type`](#mapping-type-field), and `_id` meta-fields.  The behaviour of some of these meta-fields
can be customised when a mapping type is created.

[float]
### Identity meta-fields

[horizontal]
**[`_index`](#mapping-index-field)**:

    The index to which the document belongs.

**[`_uid`](#mapping-uid-field)**:

    A composite field consisting of the `_type` and the `_id`.

**[`_type`](#mapping-type-field)**:

    The document's [mapping type](#mapping-type).

**[`_id`](#mapping-id-field)**:

    The document's ID.

[float]
### Document source meta-fields

**[`_source`](#mapping-source-field)**:

    The original JSON representing the body of the document.

**{plugins}/mapper-size.html[`_size`]**:

    The size of the `_source` field in bytes, provided by the
    {plugins}/mapper-size.html[`mapper-size` plugin].

[float]
### Indexing meta-fields

**[`_all`](#mapping-all-field)**:

    A _catch-all_  field that indexes the values of all other fields. Disabled by default.

**[`_field_names`](#mapping-field-names-field)**:

    All fields in the document which contain non-null values.

**[`_ignored`](#mapping-ignored-field)**:

    All fields in the document that have been ignored at index time because of
    [`ignore_malformed`](#ignore-malformed).

[float]
### Routing meta-field

**[`_routing`](#mapping-routing-field)**:

    A custom routing value which routes a document to a particular shard.

[float]
### Other meta-field

**[`_meta`](#mapping-meta-field)**:

    Application specific metadata.

include::fields/all-field.asciidoc[]

include::fields/field-names-field.asciidoc[]

include::fields/ignored-field.asciidoc[]

include::fields/id-field.asciidoc[]

include::fields/index-field.asciidoc[]

include::fields/meta-field.asciidoc[]

include::fields/routing-field.asciidoc[]

include::fields/source-field.asciidoc[]

include::fields/type-field.asciidoc[]

include::fields/uid-field.asciidoc[]