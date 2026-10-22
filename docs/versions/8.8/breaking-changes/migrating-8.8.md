**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 8.8

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.8.

See also [*What’s new in 8.17*](release-highlights.html) and [Release notes](es-release-notes.html).

### Breaking changes

There are no breaking changes in Elasticsearch 8.8.

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.8
and will be removed in a future version.
While this won’t have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.8.

To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Cluster and node setting deprecations

Deprecate `cluster.routing.allocation.type`

**Details**

The `cluster.routing.allocation.type` setting is deprecated and will be removed in a future version.

**Impact**

Discontinue use of the `cluster.routing.allocation.type` setting.