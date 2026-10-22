**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 8.11

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.11.

See also [*What’s new in 8.17*](release-highlights.html) and [Release notes](es-release-notes.html).

### Breaking changes

The following changes in Elasticsearch 8.11 might affect your applications
and prevent them from operating normally.
Before upgrading to 8.11, review these changes and take the described steps
to mitigate the impact.

There are no notable breaking changes in Elasticsearch 8.11.
But there are some less critical breaking changes.

#### REST API changes

Remove `transport_versions` from cluster state API

**Details**

The `transport_versions` subobject of the response to `GET _cluster/state` has been replaced by the `nodes_versions` subobject.

**Impact**

If needed, retrieve the per-node transport versions from the `nodes_versions` subobject.

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.11
and will be removed in a future version.
While this won’t have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.11.

To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Rollup deprecations

Rollup functionality is now deprecated

**Details**

[Rollup functionality](xpack-rollup.html) has been deprecated and will be removed in a future release. Previously, rollups were available in technical preview.

**Impact**

Use [downsampling](downsampling.html) to reduce storage costs for time series data by storing it at reduced granularity.