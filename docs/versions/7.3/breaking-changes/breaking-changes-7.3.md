**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 7.3

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.3.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

### API changes

#### Transform API changes

It is no longer possible to supply the `format` parameter when you define a
`date_histogram` transform pivot. Previously constructed transforms
will still run but the configured `format` will be ignored.

### Mapping changes

`dense_vector` field now requires `dims` parameter, specifying the number of
dimensions for document and query vectors for this field.

#### Defining multi-fields within multi-fields

Previously, it was possible to define a multi-field within a multi-field.
Defining chained multi-fields is now deprecated and will no longer be supported
in 8.0. To resolve the issue, all instances of `fields` that occur within a
`fields` block should be removed from the mappings, either by flattening the
chained `fields` blocks into a single level, or by switching to `copy_to` if
appropriate.

### Plugins changes

#### IndexStorePlugin changes

IndexStore and DirectoryService have been replaced by a stateless and simple
DirectoryFactory interface to create custom Lucene directory instances per shard.

### Search changes

#### Deprecation of queries

The `common` query has been deprecated. The same functionality can be achieved
by the `match` query if the total number of hits is not tracked.

##### Deprecation of query parameters

The `cutoff_frequency` parameter has been deprecated for `match` and `multi_match`
queries. The same functionality can be achieved without any configuration provided
that the total number of hits is not tracked.

### CCR changes

#### Directly modifying aliases of follower indices is no longer allowed

Aliases are now replicated to a follower from its leader, so directly modifying
aliases on follower indices is no longer allowed.

### Security deprecations

#### The `transport.profiles.*.xpack.security.type` setting is deprecated.

The `transport.profiles.*.xpack.security.type` setting is now deprecated. In
8.0, the Java transport client will be removed. All client traffic will use the
HTTP interface instead.

To avoid deprecation warnings,
[migrate any code for the Java
transport client](/guide/en/elasticsearch/client/java-rest/7.15/java-rest-high-level-migration.html). Then remove any transport profiles using the deprecated
setting.