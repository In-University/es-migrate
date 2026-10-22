## Migrating to 8.6

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.6.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

### Breaking changes

There are no breaking changes in Elasticsearch 8.6.

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.6
and will be removed in a future version.
While this won't have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.6.

To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

#### CRUD deprecations

.Deprecate 'remove_binary' default of false for ingest attachment processor
[%collapsible]
====
*Details* +
The default "remove_binary" option for the attachment processor will be changed from false to true in a later Elasticsearch release. This means that the binary file sent to Elasticsearch will not be retained.

*Impact* +
Users should update the "remove_binary" option to be explicitly true or false, instead of relying on the default value, so that no default value changes will affect Elasticsearch.
====

#### Cluster and node setting deprecations

.Ensure balance threshold is at least 1
[%collapsible]
====
*Details* +
Values for `cluster.routing.allocation.balance.threshold` smaller than `1` are now ignored. Support for values less than `1` for this setting is deprecated and will be forbidden in a future version.

*Impact* +
Set `cluster.routing.allocation.balance.threshold` to be at least `1`.
====

#### Mapping deprecations

.Deprecate silently ignoring type, fields, copy_to and boost in metadata field definition
[%collapsible]
====
*Details* +
Unsupported parameters like type, fields, copy_to and boost are silently ignored when provided as part of the configuration of a metadata field in the index mappings. They will cause a deprecation warning when used in the mappings for indices that are created from 8.6 onwards.

*Impact* +
To resolve the deprecation warning, remove the mention of type, fields, copy_to or boost from any metadata field definition as part of index mappings. They take no effect so removing them won't have any impact besides resolving the deprecation warning.
====

#### REST API deprecations

.state field is deprecated in /_cluster/reroute response
[%collapsible]
====
*Details* +
`state` field is deprecated in `/_cluster/reroute` response. Cluster state does not provide meaningful information
about the result of reroute/commands execution. There are no guarantees that this exact state would be applied.

*Impact* +
Reroute API users should not rely on `state` field and instead use `explain` to request result of commands execution.
====