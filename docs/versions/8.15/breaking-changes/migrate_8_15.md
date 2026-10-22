## Migrating to 8.15

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.15.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

coming::[8.15.0]

### Breaking changes

The following changes in Elasticsearch 8.15 might affect your applications
and prevent them from operating normally.
Before upgrading to 8.15, review these changes and take the described steps
to mitigate the impact.

#### Cluster and node setting changes

.Change `skip_unavailable` remote cluster setting default value to true
[%collapsible]
====
*Details* +
The default value of the `skip_unavailable` setting is now set to true. All existing and future remote clusters that do not define this setting will use the new default. This setting only affects cross-cluster searches using the _search or _async_search API.

*Impact* +
Unavailable remote clusters in a cross-cluster search will no longer cause the search to fail unless skip_unavailable is configured to be `false` in elasticsearch.yml or via the `_cluster/settings` API. Unavailable clusters with `skip_unavailable`=`true` (either explicitly or by using the new default) are marked as SKIPPED in the search response metadata section and do not fail the entire search. If users want to ensure that a search returns a failure when a particular remote cluster is not available, `skip_unavailable` must be now be set explicitly.
====

#### Rollup changes

.Disallow new rollup jobs in clusters with no rollup usage
[%collapsible]
====
*Details* +
The put rollup API will fail with an error when a rollup job is created in a cluster with no rollup usage

*Impact* +
Clusters with no rollup usage (either no rollup job or index) can not create new rollup jobs
====

#### REST API changes

.Interpret `?timeout=-1` as infinite ack timeout
[%collapsible]
====
*Details* +
Today Elasticsearch accepts the parameter `?timeout=-1` in many APIs, but interprets
this to mean the same as `?timeout=0`. From 8.15 onwards `?timeout=-1` will
mean to wait indefinitely, aligning the behaviour of this parameter with
other similar parameters such as `?master_timeout`.

*Impact* +
Use `?timeout=0` to force relevant operations to time out immediately
instead of `?timeout=-1`
====

.Replace `model_id` with `inference_id` in GET inference API
[%collapsible]
====
*Details* +
From 8.15 onwards the [get-inference-api](#get-inference-api) response will return an
`inference_id` field instead of a `model_id`.

*Impact* +
If your application uses the `model_id` in a GET inference API response,
switch it to use `inference_id` instead.
====

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.15
and will be removed in a future version.
While this won't have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.15.

To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

#### Cluster and node setting deprecations

.Deprecate absolute size values for `indices.breaker.total.limit` setting
[%collapsible]
====
*Details* +
Previously, the value of `indices.breaker.total.limit` could be specified as an absolute size in bytes. This setting controls the overal amount of memory the server is allowed to use before taking remedial actions. Setting this to a specific number of bytes led to strange behaviour when the node maximum heap size changed because the circut breaker limit would remain unchanged. This would either leave the value too low, causing part of the heap to remain unused; or it would leave the value too high, causing the circuit breaker to be ineffective at preventing OOM errors.  The only reasonable behaviour for this setting is that it scales with the size of the heap, and so absolute byte limits are now deprecated.

*Impact* +
Users must change their configuration to specify a percentage instead of an absolute number of bytes for `indices.breaker.total.limit`, or else accept the default, which is already specified as a percentage.
====

#### REST API deprecations

.Deprecate `text_expansion` and `weighted_tokens` queries
[%collapsible]
====
*Details* +
The `text_expansion` and `weighted_tokens` queries have been replaced by `sparse_vector`.

*Impact* +
Please update your existing `text_expansion` and `weighted_tokens` queries to use `sparse_vector.`
====

.Deprecate using slm privileges to access ilm
[%collapsible]
====
*Details* +
The `read_slm` privilege can get the ILM status, and the `manage_slm` privilege can start and stop ILM. Access to these APIs should be granted using the `read_ilm` and `manage_ilm` privileges instead. Access to ILM APIs will be removed from SLM privileges in a future major release, and is now deprecated.

*Impact* +
Users that need access to the ILM status API should now use the `read_ilm` privilege. Users that need to start and stop ILM, should use the `manage_ilm` privilege.
====