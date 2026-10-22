## Breaking changes in 7.6

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.6.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

//NOTE: The notable-breaking-changes tagged regions are re-used in the
//Installation and Upgrade Guide

//tag::notable-breaking-changes[]
### Security changes

#### Elasticsearch API key privileges

If you use an API key to create another API key (sometimes called a
_derived key_), its behavior is impacted by the fix for
[CVE-2020-7009](https://www.elastic.co/community/security).

When you make a request to create API keys, you can specify an expiration and
privileges for the API key. Previously, when you created a derived key, it had
no privileges. This behavior disregarded any privileges that you specified in
the {ref}/security-api-create-api-key.html[create API key API].

As of 7.6.2, this behavior changes. To create a derived key, you must explicitly
specify a role descriptor with no privileges:

[source,js]
```
...
"role_descriptors": {
    "no-privilege": {
    }
}
...
```
// NOTCONSOLE

//end::notable-breaking-changes[]

### Search changes

#### Aggregating and sorting on `_id` is deprecated
It's possible to aggregate and sort on the built-in `_id` field by loading an
expensive data structure called fielddata. This was deprecated in 7.6 and will
be disallowed by default in 8.0. As an alternative, the `_id` field's contents
can be duplicated into another field with docvalues enabled (note that this
does not apply to auto-generated IDs).

#### Deprecation of sparse vector fields
The `sparse_vector` field type has been deprecated and will be removed in 8.0.
We have not seen much interest in this experimental field type, and don't see
a clear use case as it's currently designed. If you have feedback or
suggestions around sparse vector functionality, please let us know through
GitHub or the 'discuss' forums.

#### Update to vector function signatures
The vector functions of the form `function(query, doc['field'])` are
deprecated, and the form `function(query, 'field')` should be used instead.
For example, `cosineSimilarity(query, doc['field'])` is replaced by
`cosineSimilarity(query, 'field')`.

#### Disallow use of the `nGram` and `edgeNGram` tokenizer names

The `nGram` and `edgeNGram` tokenizer names haven been deprecated with 7.6.
Mappings for indices created after 7.6 will continue to work but emit a
deprecation warning. The tokenizer name should be changed to the fully
equivalent `ngram` or `edge_ngram` names for new indices and in index
templates.