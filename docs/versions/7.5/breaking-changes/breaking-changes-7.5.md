**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 7.5

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.5.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

* [Allocation deprecations](breaking-changes-7.5.html#breaking_75_allocation_deprecations)

* [Search Changes](breaking-changes-7.5.html#breaking_75_search_changes)

### Allocation deprecations

#### The `cluster.routing.allocation.disk.include_relocations` setting is deprecated.

The `cluster.routing.allocation.disk.include_relocations` cluster setting is now
deprecated. In future versions, Elasticsearch will account for the sizes of relocating
shards when making allocation decisions based on the disk usage of nodes in the
cluster.

Currently, you can set `cluster.routing.allocation.disk.include_relocations` to
`false` to disable this accounting. This can result in poor allocation decisions
that might overshoot watermarks and require significant work to correct.

To avoid deprecation warnings, discontinue use of the setting.

### Search Changes

#### Stricter checking for wildcard queries on _index

Previously, a wildcard query on the `_index` field matched directly against the
fully-qualified index name. Now, in order to match against remote indices like
`cluster:index`, the query must contain a colon, as in `cl*ster:inde*`. This
behavior aligns with the way indices are matched in the search endpoint.