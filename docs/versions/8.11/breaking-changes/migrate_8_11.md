## Migrating to 8.11

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.11.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

### Breaking changes

The following changes in Elasticsearch 8.11 might affect your applications
and prevent them from operating normally.
Before upgrading to 8.11, review these changes and take the described steps
to mitigate the impact.

There are no notable breaking changes in Elasticsearch 8.11.
But there are some less critical breaking changes.

#### REST API changes

.Remove `transport_versions` from cluster state API
[%collapsible]
====
*Details* +
The `transport_versions` subobject of the response to `GET _cluster/state` has been replaced by the `nodes_versions` subobject.

*Impact* +
If needed, retrieve the per-node transport versions from the `nodes_versions` subobject.
====

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.11
and will be removed in a future version.
While this won't have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.11.

To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

#### Rollup deprecations

.Rollup functionality is now deprecated
[%collapsible]
====
*Details* +
[Rollup functionality](#xpack-rollup) has been deprecated and will be removed in a future release. Previously, rollups were available in technical preview.

*Impact* +
Use [downsampling](#downsampling) to reduce storage costs for time series data by storing it at reduced granularity.
====