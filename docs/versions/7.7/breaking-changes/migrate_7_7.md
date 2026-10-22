## Breaking changes in 7.7

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.7.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

//NOTE: The notable-breaking-changes tagged regions are re-used in the
//Installation and Upgrade Guide

//tag::notable-breaking-changes[]
### Indices deprecations

#### Translog retention settings are deprecated.

The `index.translog.retention.age` and `index.translog.retention.size` index
settings are now deprecated. These settings have been ignored since 7.4 in favor
of {ref}/index-modules-history-retention.html[soft deletes].

To avoid deprecation warnings, discontinue use of the settings.

### Logging changes

#### Loggers under `org.elasticsearch.action` now log at `INFO` level by default

The default log level for most loggers is `INFO`, but in earlier versions
loggers in the `org.elasticsearch.action.*` hierarchy emitted log messages at
`DEBUG` level by default. This sometimes resulted in a good deal of unnecessary
log noise. From 7.7 onwards the default log level for logger in this hierarchy
is now `INFO`, in line with most other loggers. If needed, you can recover the
pre-7.7 default behaviour by adjusting your {ref}/logging.html[logging].

### Mapping changes

#### Validation for dynamic templates

So far misconfiguration of dynamic templates have been discovered when indexing
a document with an unmapped field only. In Elasticsearch 8.0 and later versions, dynamic mappings
have stricter validation, done at mapping update time. Invalid updates, such as using
incorrect analyzer settings or unknown field types, fail. For
indices created in Elasticsearch 7.7 and later version, the update succeeds but emits a warning.

### Settings changes

#### `thread_pool.listener.size` and `thread_pool.listener.queue_size` have been deprecated
The listener thread pool is no longer used internally by Elasticsearch.
Therefore, these settings have been deprecated. You can safely remove these
settings from the configuration of your nodes.

#### `cluster.remote.connect` is deprecated in favor of `node.remote_cluster_client`
Previously the setting `cluster.remote.connect` was used to configure whether or
not the local node is capable of acting as a remote cluster client in
cross-cluster search and cross-cluster replication. This setting is deprecated
in favor of `node.remote_cluster_client` serves the same purpose and identifies
the local node as having the `remote_cluster_client` role.

#### Authentication realm `order` will be a required config in version 8.0.0.

The `order` config will be required in version 8.0.0 for authentication realm
configuration of any type. If the `order` config is missing for a realm, the node
will fail to start.

#### Authentication realm `order` uniqueness will be enforced in version 8.0.0.

The `order` config of authentication realms must be unique in version 8.0.0.
If you configure more than one realm of any type with the same order, the node will fail to start.

#### Deprecation of insecure monitoring password setting

The `auth.password` setting for the monitoring HTTP exporter has been deprecated and will be
removed in version 8.0.0. Please use the `auth.secure_password` setting instead.

#### Settings used to defer cluster recovery pending a certain number of master nodes are deprecated.

The following cluster settings are now deprecated:

* `gateway.expected_nodes`
* `gateway.expected_master_nodes`
* `gateway.recover_after_nodes`
* `gateway.recover_after_master_nodes`

It is safe to recover the cluster as soon as a majority of master-eligible nodes
have joined. There is no benefit in waiting for any additional master-eligible
nodes to start.

To avoid deprecation warnings, discontinue use of the deprecated settings. If
needed, use `gateway.expected_data_nodes` or `gateway.recover_after_data_nodes`
to defer cluster recovery pending a certain number of data nodes.

### Search changes

#### Consistent rounding of range queries on `date_range` fields
`range` queries on `date_range` field currently can have slightly differently
boundaries than their equivalent query on a pure `date` field. This can e.g.
happen when using date math or dates that don't specify up to the last
millisecond. While queries on `date` field round up to the latest millisecond
for `gt` and `lte` boundaries, the same queries on `date_range` fields didn't
do this. The behavior is now the same for both field types like documented in
{ref}/query-dsl-range-query.html#range-query-date-math-rounding[Date math and rounding].

#### Pipeline aggregation validation errors
The pipeline aggregation validation has been moved to the coordinating node.
Those errors that used to return HTTP 500s/Internal Server Errors now return
400/Bad Request and we now return a list of validation errors rather than the
first one we encounter.

### Highlighters changes

#### Ignored keyword values are no longer highlighted
If a keyword value was ignored during indexing because of its length
(`ignore_above` parameter was applied), Elasticsearch doesn't attempt to
highlight it anymore, which means no highlights are produced for
ignored values.
//end::notable-breaking-changes[]