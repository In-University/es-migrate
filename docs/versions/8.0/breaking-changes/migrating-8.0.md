**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 8.0

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.0.

See also [*What’s new in 8.17*](release-highlights.html) and [Release notes](es-release-notes.html).

### Breaking changes

The following changes in Elasticsearch 8.0 might affect your applications
and prevent them from operating normally.
Before upgrading to 8.0, review these changes and take the described steps
to mitigate the impact.

#### Cluster and node setting changes

https://cloud.elastic.co/registration?page=docs&placement=docs-body indicates a change to a supported [user setting](/guide/en/cloud/current/ec-add-user-settings.html) for Elasticsearch Service.

`action.destructive_requires_name` now defaults to `true`. https://cloud.elastic.co/registration?page=docs&placement=docs-body

**Details**

The default for the `action.destructive_requires_name` setting changes from `false`
to `true` in Elasticsearch 8.0.0.

Previously, defaulting to `false` allowed users to use wildcard
patterns to delete, close, or change index blocks on indices.
To prevent the accidental deletion of indices that happen to match a
wildcard pattern, we now default to requiring that destructive
operations explicitly name the indices to be modified.

**Impact**

To use wildcard patterns for destructive actions, set
`action.destructive_requires_name` to `false` using the
[https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cluster-update-settings.html](/guide/en/elasticsearch/reference/8.17/cluster-update-settings.html) cluster settings API].

You can no longer set `xpack.searchable.snapshot.shared_cache.size` on non-frozen nodes.

**Details**

You can no longer set
[`xpack.searchable.snapshot.shared_cache.size`](/guide/en/elasticsearch/reference/8.17/searchable-snapshots.html#searchable-snapshots-shared-cache)
on a node that doesn’t have the `data_frozen` node role. This setting reserves
disk space for the shared cache of partially mounted indices. Elasticsearch only
allocates partially mounted indices to nodes with the `data_frozen` role.

**Impact**

Remove `xpack.searchable.snapshot.shared_cache.size` from `elasticsearch.yml`
for nodes that don’t have the `data_frozen` role. Specifying the setting on a
non-frozen node will result in an error on startup.

`indices.query.bool.max_clause_count` is deprecated and has no effect.

**Details**

Elasticsearch will now dynamically set the maximum number of allowed clauses
in a query, using a heuristic based on the size of the search thread pool and
the size of the heap allocated to the JVM. This limit has a minimum value of
1024 and will in most cases be larger (for example, a node with 30Gb RAM and
48 CPUs will have a maximum clause count of around 27,000). Larger heaps lead
to higher values, and larger thread pools result in lower values.

**Impact**

Queries with many clauses should be avoided whenever possible.
If you previously bumped this setting to accommodate heavy queries,
you might need to increase the amount of memory available to Elasticsearch,
or to reduce the size of your search thread pool so that more memory is
available to each concurrent search.

In previous versions of Lucene you could get around this limit by nesting
boolean queries within each other, but the limit is now based on the total
number of leaf queries within the query as a whole and this workaround will
no longer help.

Specifying `indices.query.bool.max_clause_count` will have no effect
but will generate deprecation warnings. To avoid these warnings, remove the
setting from `elasticsearch.yml` during an upgrade or node restart.

`indices.lifecycle.poll_interval` must be greater than `1s`.

**Details**

Setting `indices.lifecycle.poll_interval` too low can cause
excessive load on a cluster. The poll interval must now be at least `1s` (one second).

**Impact**

Set `indices.lifecycle.poll_interval` setting to `1s` or
greater in `elasticsearch.yml` or through the
[cluster update settings API](/guide/en/elasticsearch/reference/8.17/cluster-update-settings.html).

Setting `indices.lifecycle.poll_interval` to less than `1s` in
`elasticsearch.yml` will result in an error on startup.
[Cluster update settings API](/guide/en/elasticsearch/reference/8.17/cluster-update-settings.html) requests that
set `indices.lifecycle.poll_interval` to less than `1s` will return an error.

The file and native realms are now enabled unless explicitly disabled.

**Details**

The file and native realms are now enabled unless explicitly disabled. If
explicitly disabled, the file and native realms remain disabled at all times.

Previously, the file and native realms had the following implicit behaviors:

* If the file and native realms were not configured, they were implicitly disabled
if any other realm was configured.

* If no other realm was available because realms were either not configured,
not permitted by license, or explicitly disabled, the file and native realms
were enabled, even if explicitly disabled.

**Impact**

To explicitly disable the file or native realm, set the respective
`file.<realm-name>.enabled` or `native.<realm-name>.enabled` setting to `false`
under the `xpack.security.authc.realms` namespace in `elasticsearch.yml`.

The following configuration example disables the native realm and the file realm.

```
xpack.security.authc.realms:

  native.realm1.enabled: false
  file.realm2.enabled: false

  ...
```

The realm `order` setting is now required.

**Details**

The `xpack.security.authc.realms.{type}.{name}.order` setting is now required and must be
specified for each explicitly configured realm. Each value must be unique.

**Impact**

The cluster will fail to start if the requirements are not met.

For example, the following configuration is invalid:

```
xpack.security.authc.realms.kerberos.kerb1:
  keytab.path: es.keytab
  remove_realm_name: false
```

And must be configured as:

```
xpack.security.authc.realms.kerberos.kerb1:
  order: 0
  keytab.path: es.keytab
  remove_realm_name: false
```

`cluster.routing.allocation.disk.include_relocations` has been removed.

**Details**

Elasticsearch now always accounts for the sizes of relocating shards when making
allocation decisions based on the disk usage of the nodes in the cluster. In
earlier versions, you could disable this by setting `cluster.routing.allocation.disk.include_relocations` to `false`.
That could result in poor allocation decisions that could overshoot watermarks and require significant
extra work to correct. The `cluster.routing.allocation.disk.include_relocations` setting has been removed.

**Impact**

Remove the `cluster.routing.allocation.disk.include_relocations`
setting. Specifying this setting in `elasticsearch.yml` will result in an error
on startup.

`cluster.join.timeout` has been removed.

**Details**

The `cluster.join.timeout` setting has been removed. Join attempts no longer
time out.

**Impact**

Remove `cluster.join.timeout` from `elasticsearch.yml`.

`discovery.zen` settings have been removed.

**Details**

All settings under the `discovery.zen` namespace are no longer supported. They existed only only for BWC reasons in 7.x. This includes:

* `discovery.zen.minimum_master_nodes`

* `discovery.zen.no_master_block`

* `discovery.zen.hosts_provider`

* `discovery.zen.publish_timeout`

* `discovery.zen.commit_timeout`

* `discovery.zen.publish_diff.enable`

* `discovery.zen.ping.unicast.concurrent_connects`

* `discovery.zen.ping.unicast.hosts.resolve_timeout`

* `discovery.zen.ping.unicast.hosts`

* `discovery.zen.ping_timeout`

* `discovery.zen.unsafe_rolling_upgrades_enabled`

* `discovery.zen.fd.connect_on_network_disconnect`

* `discovery.zen.fd.ping_interval`

* `discovery.zen.fd.ping_timeout`

* `discovery.zen.fd.ping_retries`

* `discovery.zen.fd.register_connection_listener`

* `discovery.zen.join_retry_attempts`

* `discovery.zen.join_retry_delay`

* `discovery.zen.join_timeout`

* `discovery.zen.max_pings_from_another_master`

* `discovery.zen.send_leave_request`

* `discovery.zen.master_election.wait_for_joins_timeout`

* `discovery.zen.master_election.ignore_non_master_pings`

* `discovery.zen.publish.max_pending_cluster_states`

* `discovery.zen.bwc_ping_timeout`

**Impact**

Remove the `discovery.zen` settings from `elasticsearch.yml`. Specifying these settings will result in an error on startup.

`http.content_type.required` has been removed.

**Details**

The `http.content_type.required` setting was deprecated in Elasticsearch 6.0
and has been removed in Elasticsearch 8.0. The setting was introduced in
Elasticsearch 5.3 to prepare users for Elasticsearch 6.0, where content type
auto detection was removed for HTTP requests.

**Impact**

Remove the `http.content_type.required` setting from `elasticsearch.yml`. Specifying this setting  will result in an error on startup.

`http.tcp_no_delay` has been removed.

**Details**

The `http.tcp_no_delay` setting was deprecated in 7.x and has been removed in 8.0. Use `http.tcp.no_delay` instead.

**Impact**

Replace the `http.tcp_no_delay` setting with `http.tcp.no_delay`.
Specifying  `http.tcp_no_delay` in `elasticsearch.yml` will
result in an error on startup.

`network.tcp.connect_timeout` has been removed.

**Details**

The `network.tcp.connect_timeout` setting was deprecated in 7.x and has been removed in 8.0. This setting
was a fallback setting for `transport.connect_timeout`.

**Impact**

Remove the `network.tcp.connect_timeout` setting.
Use the `transport.connect_timeout` setting to change the default connection
timeout for client connections. Specifying
`network.tcp.connect_timeout` in `elasticsearch.yml` will result in an
error on startup.

`node.max_local_storage_nodes` has been removed.

**Details**

The `node.max_local_storage_nodes` setting was deprecated in 7.x and
has been removed in 8.0. Nodes should be run on separate data paths
to ensure that each node is consistently assigned to the same data path.

**Impact**

Remove the `node.max_local_storage_nodes` setting. Specifying this
setting in `elasticsearch.yml` will result in an error on startup.

The `accept_default_password` setting has been removed.

**Details**

The `xpack.security.authc.accept_default_password` setting has not had any affect
since the 6.0 release of Elasticsearch and is no longer allowed.

**Impact**

Remove  the `xpack.security.authc.accept_default_password` setting from `elasticsearch.yml`.
Specifying this setting will result in an error on startup.

The `roles.index.cache.*` settings have been removed.

**Details**

The `xpack.security.authz.store.roles.index.cache.max_size` and
`xpack.security.authz.store.roles.index.cache.ttl` settings have
been removed. These settings have been redundant and deprecated
since the 5.2 release of Elasticsearch.

**Impact**

Remove the `xpack.security.authz.store.roles.index.cache.max_size`
and `xpack.security.authz.store.roles.index.cache.ttl` settings from `elasticsearch.yml` .
Specifying these settings will result in an error on startup.

The `transport.profiles.*.xpack.security.type` setting has been removed.

**Details**

The `transport.profiles.*.xpack.security.type` setting is no longer supported.
The Transport Client has been removed and all client traffic now uses
the HTTP transport. Transport profiles using this setting should be removed.

**Impact**

Remove the `transport.profiles.*.xpack.security.type` setting from `elasticsearch.yml`.
Specifying this setting in a transport profile will result in an error on startup.

The `nameid_format` SAML realm setting no longer has a default value.

**Details**

In SAML, Identity Providers (IdPs) can either be explicitly configured to
release a `NameID` with a specific format, or configured to attempt to conform
with the requirements of a Service Provider (SP). The SP declares its
requirements in the `NameIDPolicy` element of a SAML Authentication Request.
In Elasticsearch, the `nameid_format` SAML realm setting controls the `NameIDPolicy`
value.

Previously, the default value for `nameid_format` was
`urn:oasis:names:tc:SAML:2.0:nameid-format:transient`. This setting created
authentication requests that required the IdP to release `NameID` with a
`transient` format.

The default value has been removed, which means that Elasticsearch will create SAML Authentication Requests by default that don’t put this requirement on the
IdP. If you want to retain the previous behavior, set `nameid_format` to
`urn:oasis:names:tc:SAML:2.0:nameid-format:transient`.

**Impact**

If you currently don’t configure `nameid_format` explicitly, it’s possible
that your IdP will reject authentication requests from Elasticsearch because the requests
do not specify a `NameID` format (and your IdP is configured to expect one).
This mismatch can result in a broken SAML configuration. If you’re unsure whether
your IdP is explicitly configured to use a certain `NameID` format and you want to retain current behavior
, try setting `nameid_format` to `urn:oasis:names:tc:SAML:2.0:nameid-format:transient` explicitly.

The `xpack.security.transport.ssl.enabled` setting is now required to configure `xpack.security.transport.ssl` settings.

**Details**

It is now an error to configure any SSL settings for
`xpack.security.transport.ssl` without also configuring
`xpack.security.transport.ssl.enabled`.

**Impact**

If using other `xpack.security.transport.ssl` settings, you must explicitly
specify the `xpack.security.transport.ssl.enabled` setting.

If you do not want to enable SSL and are currently using other
`xpack.security.transport.ssl` settings, do one of the following:

* Explicitly specify `xpack.security.transport.ssl.enabled` as `false`

* Discontinue use of other `xpack.security.transport.ssl` settings

If you want to enable SSL, follow the instructions in
[Encrypting communications between nodes
in a cluster](/guide/en/elasticsearch/reference/8.17/configuring-tls.html#tls-transport). As part of this configuration, explicitly specify
`xpack.security.transport.ssl.enabled` as `true`.

For example, the following configuration is invalid:

```
xpack.security.transport.ssl.keystore.path: elastic-certificates.p12
xpack.security.transport.ssl.truststore.path: elastic-certificates.p12
```

And must be configured as:

```
xpack.security.transport.ssl.enabled: true 
xpack.security.transport.ssl.keystore.path: elastic-certificates.p12
xpack.security.transport.ssl.truststore.path: elastic-certificates.p12
```

|  | or false . |
| --- | --- |

The `xpack.security.http.ssl.enabled` setting is now required to configure `xpack.security.http.ssl` settings.

**Details**

It is now an error to configure any SSL settings for
`xpack.security.http.ssl` without also configuring
`xpack.security.http.ssl.enabled`.

**Impact**

If using other `xpack.security.http.ssl` settings, you must explicitly
specify the `xpack.security.http.ssl.enabled` setting.

If you do not want to enable SSL and are currently using other
`xpack.security.http.ssl` settings, do one of the following:

* Explicitly specify `xpack.security.http.ssl.enabled` as `false`

* Discontinue use of other `xpack.security.http.ssl` settings

If you want to enable SSL, follow the instructions in
[Encrypting HTTP client communications](/guide/en/elasticsearch/reference/8.17/security-basic-setup-https.html#encrypt-http-communication). As part
of this configuration, explicitly specify `xpack.security.http.ssl.enabled`
as `true`.

For example, the following configuration is invalid:

```
xpack.security.http.ssl.certificate: elasticsearch.crt
xpack.security.http.ssl.key: elasticsearch.key
xpack.security.http.ssl.certificate_authorities: [ "corporate-ca.crt" ]
```

And must be configured as either:

```
xpack.security.http.ssl.enabled: true 
xpack.security.http.ssl.certificate: elasticsearch.crt
xpack.security.http.ssl.key: elasticsearch.key
xpack.security.http.ssl.certificate_authorities: [ "corporate-ca.crt" ]
```

|  | or false . |
| --- | --- |

A `xpack.security.transport.ssl` certificate and key are now required to enable SSL for the transport interface.

**Details**

It is now an error to enable SSL for the transport interface without also configuring
a certificate and key through use of the `xpack.security.transport.ssl.keystore.path`
setting or the `xpack.security.transport.ssl.certificate` and
`xpack.security.transport.ssl.key` settings.

**Impact**

If `xpack.security.transport.ssl.enabled` is set to `true`, provide a
certificate and key using the `xpack.security.transport.ssl.keystore.path`
setting or the `xpack.security.transport.ssl.certificate` and
`xpack.security.transport.ssl.key` settings. If a certificate and key is not
provided, Elasticsearch will return in an error on startup.

A `xpack.security.http.ssl` certificate and key are now required to enable SSL for the HTTP server.

**Details**

It is now an error to enable SSL for the HTTP (Rest) server without also configuring
a certificate and key through use of the `xpack.security.http.ssl.keystore.path`
setting or the `xpack.security.http.ssl.certificate` and
`xpack.security.http.ssl.key` settings.

**Impact**

If `xpack.security.http.ssl.enabled` is set to `true`, provide a certificate and
key using the `xpack.security.http.ssl.keystore.path` setting or the
`xpack.security.http.ssl.certificate` and `xpack.security.http.ssl.key`
settings. If certificate and key is not provided, Elasticsearch will return in an error
on startup.

PKCS#11 keystores and trustores cannot be configured in `elasticsearch.yml`

**Details**

The settings `*.ssl.keystore.type` and `*.ssl.truststore.type` no longer accept "PKCS11" as a valid type.
This applies to all SSL settings in Elasticsearch, including

* `xpack.security.http.keystore.type`

* `xpack.security.transport.keystore.type`

* `xpack.security.http.truststore.type`

* `xpack.security.transport.truststore.type`

As well as SSL settings for security realms, watcher and monitoring.

Use of a PKCS#11 keystore or truststore as the JRE’s default store is not affected.

**Impact**

If you have a PKCS#11 keystore configured within your `elasticsearch.yml` file, you must remove that
configuration and switch to a supported keystore type, or configure your PKCS#11 keystore as the
JRE default store.

The `kibana` user has been replaced by `kibana_system`.

**Details**

The `kibana` user was historically used to authenticate Kibana to Elasticsearch.
The name of this user was confusing, and was often mistakenly used to login to Kibana.
This has been renamed to `kibana_system` in order to reduce confusion, and to better
align with other built-in system accounts.

**Impact**

Replace any use of the `kibana` user with the `kibana_system` user. Specifying
the `kibana` user in `kibana.yml` will result in an error on startup.

If your `kibana.yml` used to contain:

```
elasticsearch.username: kibana
```

then you should update to use the new `kibana_system` user instead:

```
elasticsearch.username: kibana_system
```

The new `kibana_system` user does not preserve the previous `kibana`
user password. You must explicitly set a password for the `kibana_system` user.

The `search.remote.*` settings have been removed.

**Details**

In 6.5 these settings were deprecated in favor of `cluster.remote`. In 7.x we
provided automatic upgrading of these settings to their `cluster.remote`
counterparts. In 8.0.0, these settings have been removed. Elasticsearch will
refuse to start if you have these settings in your configuration or cluster
state.

**Impact**

Use the replacement `cluster.remote` settings. Discontinue use of the
`search.remote.*` settings. Specifying these settings in `elasticsearch.yml`
will result in an error on startup.

The `pidfile` setting has been replaced by `node.pidfile`.

**Details**

To ensure that all settings are in a proper namespace, the `pidfile` setting was
previously deprecated in version 7.4.0 of Elasticsearch, and is removed in
version 8.0.0. Instead, use `node.pidfile`.

**Impact**

Use the `node.pidfile` setting. Discontinue use of the `pidfile` setting.
Specifying the `pidfile` setting in `elasticsearch.yml` will result in an error
on startup.

The `processors` setting has been replaced by `node.processors`.

**Details**

To ensure that all settings are in a proper namespace, the `processors` setting
was previously deprecated in version 7.4.0 of Elasticsearch, and is removed in
version 8.0.0. Instead, use `node.processors`.

**Impact**

Use the `node.processors` setting. Discontinue use of the `processors` setting.
Specifying the `processors` setting in `elasticsearch.yml` will result in an
error on startup.

The `node.processors` setting can no longer exceed the available number of processors.

**Details**

Previously it was possible to set the number of processors used to set the
default sizes for the thread pools to be more than the number of available
processors. As this leads to more context switches and more threads but without
an increase in the number of physical CPUs on which to schedule these additional
threads, the `node.processors` setting is now bounded by the number of available
processors.

**Impact**

If specified, ensure the value of `node.processors` setting does not exceed the
number of available processors. Setting the `node.processors` value greater than
the number of available processors in `elasticsearch.yml` will result in an
error on startup.

The `cluster.remote.connect` setting has been removed.

**Details**

In Elasticsearch 7.7.0, the setting `cluster.remote.connect` was deprecated in
favor of setting `node.remote_cluster_client`. In Elasticsearch 8.0.0, the
setting `cluster.remote.connect` is removed.

**Impact**

Use the `node.remote_cluster_client` setting. Discontinue use of the
`cluster.remote.connect` setting. Specifying the `cluster.remote.connect`
setting in `elasticsearch.yml` will result in an error on startup.

The `node.local_storage` setting has been removed.

**Details**

In Elasticsearch 7.8.0, the setting `node.local_storage` was deprecated and
beginning in Elasticsearch 8.0.0 all nodes will require local storage. Therefore,
the `node.local_storage` setting has been removed.

**Impact**

Discontinue use of the `node.local_storage` setting. Specifying this setting in
`elasticsearch.yml` will result in an error on startup.

The `auth.password` setting for HTTP monitoring has been removed.

**Details**

In Elasticsearch 7.7.0, the setting `xpack.monitoring.exporters.<exporterName>.auth.password`
was deprecated in favor of setting `xpack.monitoring.exporters.<exporterName>.auth.secure_password`.
In Elasticsearch 8.0.0, the setting `xpack.monitoring.exporters.<exporterName>.auth.password` is
removed.

**Impact**

Use the `xpack.monitoring.exporters.<exporterName>.auth.secure_password`
setting. Discontinue use of the
`xpack.monitoring.exporters.<exporterName>.auth.password` setting. Specifying
the `xpack.monitoring.exporters.<exporterName>.auth.password` setting in
`elasticsearch.yml` will result in an error on startup.

Settings used to disable basic license features have been removed.

**Details**

The following settings were deprecated in Elasticsearch 7.8.0 and have been removed
in Elasticsearch 8.0.0:

* `xpack.enrich.enabled`

* `xpack.flattened.enabled`

* `xpack.ilm.enabled`

* `xpack.monitoring.enabled`

* `xpack.rollup.enabled`

* `xpack.slm.enabled`

* `xpack.sql.enabled`

* `xpack.transform.enabled`

* `xpack.vectors.enabled`

These basic license features are now always enabled.

If you have disabled ILM so that you can use another tool to manage Watcher
indices, the newly introduced `xpack.watcher.use_ilm_index_management` setting
may be set to false.

**Impact**

Discontinue use of the removed settings. Specifying these settings in
`elasticsearch.yml` will result in an error on startup.

Settings used to defer cluster recovery pending a certain number of master nodes have been removed.

**Details**

The following cluster settings have been removed:

* `gateway.expected_nodes`

* `gateway.expected_master_nodes`

* `gateway.recover_after_nodes`

* `gateway.recover_after_master_nodes`

It is safe to recover the cluster as soon as a majority of master-eligible
nodes have joined so there is no benefit in waiting for any additional
master-eligible nodes to start.

**Impact**

Discontinue use of the removed settings. If needed, use
`gateway.expected_data_nodes` or `gateway.recover_after_data_nodes` to defer
cluster recovery pending a certain number of data nodes.

Legacy role settings have been removed.

**Details**

The legacy role settings:

* `node.data`

* `node.ingest`

* `node.master`

* `node.ml`

* `node.remote_cluster_client`

* `node.transform`

* `node.voting_only`

have been removed. Instead, use the `node.roles` setting. If you were previously
using the legacy role settings on a 7.13 or later cluster, you will have a
deprecation log message on each of your nodes indicating the exact replacement
value for `node.roles`.

**Impact**

Discontinue use of the removed settings. Specifying these settings in
`elasticsearch.yml` will result in an error on startup.

The system call filter setting has been removed.

**Details**

Elasticsearch uses system call filters to remove its ability to fork another
process. This is useful to mitigate remote code exploits. These system call
filters are enabled by default, and were previously controlled via the setting
`bootstrap.system_call_filter`. Starting in Elasticsearch 8.0, system call
filters will be required. As such, the setting `bootstrap.system_call_filter`
was deprecated in Elasticsearch 7.13.0, and is removed as of Elasticsearch
8.0.0.

**Impact**

Discontinue use of the removed setting. Specifying this setting in Elasticsearch
configuration will result in an error on startup.

Tier filtering settings have been removed.

**Details**

The cluster and index level settings ending in `._tier` used for filtering the allocation of a shard
to a particular set of nodes have been removed. Instead, the
[tier
preference setting](/guide/en/elasticsearch/reference/8.17/data-tier-shard-filtering.html#tier-preference-allocation-filter), `index.routing.allocation.include._tier_preference` should
be used. The removed settings are:

Cluster level settings:

* `cluster.routing.allocation.include._tier`

* `cluster.routing.allocation.exclude._tier`

* `cluster.routing.allocation.require._tier`

Index settings:

* `index.routing.allocation.include._tier`

* `index.routing.allocation.exclude._tier`

* `index.routing.allocation.require._tier`

**Impact**

Discontinue use of the removed settings. Specifying any of these cluster settings in Elasticsearch
configuration will result in an error on startup. Any indices using these settings will have the
settings archived (and they will have no effect) when the index metadata is loaded.

Shared data path and per index data path settings are deprecated.

**Details**

Elasticsearch uses the shared data path as the base path of per index data
paths. This feature was previously used with shared replicas. Starting in
7.13.0, these settings are deprecated. Starting in 8.0 only existing
indices created in 7.x will be capable of using the shared data path and
per index data path settings.

**Impact**

Discontinue use of the deprecated settings.

The single data node watermark setting is deprecated and now only accepts `true`.

**Details**

In 7.14, setting `cluster.routing.allocation.disk.watermark.enable_for_single_data_node`
to false was deprecated. Starting in 8.0, the only legal value will be
true. In a future release, the setting will be removed completely, with same
behavior as if the setting was `true`.

If the old behavior is desired for a single data node cluster, disk based
allocation can be disabled by setting
`cluster.routing.allocation.disk.threshold_enabled: false`

**Impact**

Discontinue use of the deprecated setting.

The `gateway.auto_import_dangling_indices` setting has been removed.

**Details**

The `gateway.auto_import_dangling_indices` cluster setting has been removed.
Previously, you could use this setting to automatically import
[dangling indices](modules-gateway.html#dangling-indices). However,
automatically importing dangling indices is unsafe. Use the
[dangling indices APIs](/guide/en/elasticsearch/reference/8.17/indices.html#dangling-indices-api) to manage and
import dangling indices instead.

**Impact**

Discontinue use of the removed setting. Specifying the setting in
`elasticsearch.yml` will result in an error on startup.

The `listener` thread pool has been removed.

**Details**

Previously, the transport client used the thread pool to ensure listeners aren’t
called back on network threads. The transport client has been removed
in 8.0, and the thread pool is no longer needed.

**Impact**

Remove `listener` thread pool settings from `elasticsearch.yml` for any nodes.
Specifying `listener` thread pool settings in `elasticsearch.yml` will result in
an error on startup.

The `fixed_auto_queue_size` thread pool type has been removed.

**Details**

The `fixed_auto_queue_size` thread pool type, previously marked as an
experimental feature, was deprecated in 7.x and has been removed in 8.0.
The `search` and `search_throttled` thread pools have the `fixed` type now.

**Impact**

No action needed.

Several `transport` settings have been replaced.

**Details**

The following settings have been deprecated in 7.x and removed in 8.0. Each setting has a replacement
setting that was introduced in 6.7.

* `transport.tcp.port` replaced by `transport.port`

* `transport.tcp.compress` replaced by `transport.compress`

* `transport.tcp.connect_timeout` replaced by `transport.connect_timeout`

* `transport.tcp_no_delay` replaced by `transport.tcp.no_delay`

* `transport.profiles.profile_name.tcp_no_delay` replaced by `transport.profiles.profile_name.tcp.no_delay`

* `transport.profiles.profile_name.tcp_keep_alive` replaced by `transport.profiles.profile_name.tcp.keep_alive`

* `transport.profiles.profile_name.reuse_address` replaced by `transport.profiles.profile_name.tcp.reuse_address`

* `transport.profiles.profile_name.send_buffer_size` replaced by `transport.profiles.profile_name.tcp.send_buffer_size`

* `transport.profiles.profile_name.receive_buffer_size` replaced by `transport.profiles.profile_name.tcp.receive_buffer_size`

**Impact**

Use the replacement settings. Discontinue use of the removed settings.
Specifying the removed settings in `elasticsearch.yml` will result in an error
on startup.

Selective transport compression has been enabled by default.

**Details**

Prior to 8.0, transport compression was disabled by default. Starting in 8.0,
`transport.compress` defaults to `indexing_data`. This configuration means that
the propagation of raw indexing data will be compressed between nodes.

**Impact**

Inter-node transit will get reduced along the indexing path. In some scenarios,
CPU usage could increase.

Transport compression defaults to lz4.

**Details**

Prior to 8.0, the `transport.compression_scheme` setting defaulted to `deflate`. Starting in
8.0,  `transport.compress_scheme` defaults to `lz4`.

Prior to 8.0, the `cluster.remote.<cluster_alias>.transport.compression_scheme`
setting defaulted to `deflate` when `cluster.remote.<cluster_alias>.transport.compress`
was explicitly configured. Starting in 8.0,
`cluster.remote.<cluster_alias>.transport.compression_scheme` will fallback to
`transport.compression_scheme` by default.

**Impact**

This configuration means that transport compression will produce somewhat lower
compression ratios in exchange for lower CPU load.

The `repositories.fs.compress` node-level setting has been removed.

**Details**

For shared file system repositories (`"type": "fs"`), the node level setting `repositories.fs.compress` could
previously be used to enable compression for all shared file system repositories where `compress` was not specified.
The `repositories.fs.compress` setting has been removed.

**Impact**

Discontinue use of the `repositories.fs.compress` node-level setting. Use the
repository-specific `compress` setting to enable compression instead. Refer to
[Shared
file system repository settings](/guide/en/elasticsearch/reference/8.17/snapshots-filesystem-repository.html#filesystem-repository-settings).

When FIPS mode is enabled the default password hash is now PBKDF2_STRETCH

**Details**

If `xpack.security.fips_mode.enabled` is true (see [FIPS 140-2](fips-140-compliance.html)),
the value of `xpack.security.authc.password_hashing.algorithm` now defaults to
`pbkdf2_stretch`.

In earlier versions this setting would always default to `bcrypt` and a runtime
check would prevent a node from starting unless the value was explicitly set to
a "pbkdf2" variant.

There is no change for clusters that do not enable FIPS 140 mode.

**Impact**

This change should not have any impact on upgraded nodes.
Any node with an explicitly configured value for the password hashing algorithm
will continue to use that configured value.
Any node that did not have an explicitly configured password hashing algorithm in
Elasticsearch 6.x or Elasticsearch 7.x would have failed to start.

The `xpack.monitoring.history.duration` will not delete indices created by metricbeat or elastic agent

**Details**

Prior to 8.0, Elasticsearch would internally handle removal of all monitoring indices according to the
`xpack.monitoring.history.duration` setting.

When using metricbeat or elastic agent >= 8.0 to collect monitoring data, indices are managed via an ILM policy. If the setting is present, the policy will be created using the `xpack.monitoring.history.duration` as an initial retention period.

If you need to customize retention settings for monitoring data collected with metricbeat, please update the `.monitoring-8-ilm-policy` ILM policy directly.

The `xpack.monitoring.history.duration` setting will only apply to monitoring indices written using (legacy) internal
collection, not indices created by metricbeat or agent.

**Impact**

After upgrading, insure that the `.monitoring-8-ilm-policy` ILM policy aligns with your desired retention settings.

If you only use
metricbeat or agent to collect monitoring data, you can also remove any custom `xpack.monitoring.history.duration`
settings.

#### Command line tool changes

If you use Elasticsearch Service, skip this section. Elasticsearch Service handles these changes for you.

The `elasticsearch-migrate` tool has been removed.

**Details**

The `elasticsearch-migrate` tool provided a way to convert file
realm users and roles into the native realm. It has been deprecated
since Elasticsearch 7.2.0. Users and roles should now be created in the native
realm directly.

**Impact**

Discontinue use of the `elasticsearch-migrate` tool. Attempts to use the
`elasticsearch-migrate` tool will result in an error.

#### Index setting changes

Direct access to system indices is deprecated.

**Details**

Directly accessing system indices is deprecated, and may be prevented in a
future version. If you must access a system index, create a security role with
an index permission that targets the specific index and set the
`allow_restricted_indices` permission to `true`. Refer to
[indices privileges](/guide/en/elasticsearch/reference/8.17/defining-roles.html#roles-indices-priv) for
information on adding this permission to an index privilege.

**Impact**

Accessing system indices directly results in warnings in the header of API
responses. If available, use Kibana or the associated feature’s Elasticsearch APIs to
manage the data that you want to access.

`index.merge.policy.max_merge_at_once_explicit` is deprecated and has no effect.

**Details**

The `index.merge.policy.max_merge_at_once_explicit` index setting is deprecated
and has no effect.

Previously, you could specify `index.merge.policy.max_merge_at_once_explicit` to
set the maximum number of segments to merge at the same time during a force
merge or when expunging deleted documents. In 8.0, this number is unlimited,
regardless of the setting.

**Impact**

Specifying `index.merge.policy.max_merge_at_once_explicit` will have no effect
but will generate deprecation warnings.

To avoid these deprecation warnings, discontinue use of the setting. Don’t
specify the setting when creating new indices, and remove the setting from
index and component templates.

To remove the setting from an existing data stream or index, specify the
setting’s value as `null` using the update index settings API.

```
response = client.indices.put_settings(
  index: 'my-index-000001',
  body: {
    'index.merge.policy.max_merge_at_once_explicit' => nil
  }
)
puts response
```

```
PUT my-index-000001/_settings
{
  "index.merge.policy.max_merge_at_once_explicit": null
}
```

The `index.max_adjacency_matrix_filters` index setting has been removed.

**Details**

The `index.max_adjacency_matrix_filters` index setting has been removed.
Previously, you could use this setting to configure the maximum number of
filters for the
[adjacency
matrix aggregation](/guide/en/elasticsearch/reference/8.17/search-aggregations-bucket-adjacency-matrix-aggregation.html). The `indices.query.bool.max_clause_count` index setting now
determines the maximum number of filters for the aggregation.

**Impact**

Discontinue use of the `index.max_adjacency_matrix_filters` index setting.

Requests that include the index setting will return an error. If you upgrade a
cluster with a 7.x index that already contains the setting, Elasticsearch will
[archive the setting](/guide/en/elasticsearch/reference/8.17/archived-settings.html#archived-index-settings).

Remove the index setting from index and component templates. Attempts to use a
template that contains the setting will fail and return an error. This includes
automated operations, such the ILM rollover action.

The `index.force_memory_term_dictionary` setting has been removed.

**Details**

The `index.force_memory_term_dictionary` setting was introduced in 7.0 as a
temporary measure to allow users to opt-out of the optimization that leaves the
term dictionary on disk when appropriate. This optimization is now mandatory
and the setting is removed.

**Impact**

Discontinue use of the `index.force_memory_term_dictionary` index setting.
Requests that include this setting will return an error.

The `index.soft_deletes.enabled` setting has been removed.

**Details**

Creating indices with soft deletes disabled was deprecated in 7.6 and
is no longer supported in 8.0. The `index.soft_deletes.enabled` setting
can no longer be set to `false`.

**Impact**

Discontinue use of the `index.soft_deletes.enabled` index setting. Requests that
set `index.soft_deletes.enabled` to `false` will return an error.

The `index.translog.retention.age` and `index.translog.retention.size` settings have been removed.

**Details**

Translog retention settings `index.translog.retention.age` and
`index.translog.retention.size` were effectively ignored in 7.4, deprecated in
7.7, and removed in 8.0 in favor of
[soft deletes](/guide/en/elasticsearch/reference/8.17/index-modules-history-retention.html).

**Impact**

Discontinue use of the `index.translog.retention.age` and
`index.translog.retention.size` index settings. Requests that
include these settings will return an error.

#### Java API changes

The `indexlifecycle` package has been renamed `ilm` in the Java High Level REST Client.

**Details**

In the high level REST client, the `indexlifecycle` package has been
renamed to `ilm` to match the package rename inside the Elasticsearch code.

**Impact**

Update your workflow and applications to use the `ilm` package in place of
`indexlifecycle`.

Changes to `Fuzziness`.

**Details**

To create `Fuzziness` instances, use the `fromString` and `fromEdits` method
instead of the `build` method that used to accept both Strings and numeric
values. Several fuzziness setters on query builders (e.g.
MatchQueryBuilder#fuzziness) now accept only a `Fuzziness` instance instead of
an Object.

Fuzziness used to be lenient when it comes to parsing arbitrary numeric values
while silently truncating them to one of the three allowed edit distances 0, 1
or 2. This leniency is now removed and the class will throw errors when trying
to construct an instance with another value (e.g. floats like 1.3 used to get
accepted but truncated to 1).

**Impact**

Use the available constants (e.g. `Fuzziness.ONE`, `Fuzziness.AUTO`) or build
your own instance using the above mentioned factory methods. Use only allowed
`Fuzziness` values.

Changes to `Repository`.

**Details**

Repository has no dependency on IndexShard anymore. The contract of restoreShard
and snapshotShard has been reduced to Store and MappingService in order to improve
testability.

**Impact**

No action needed.

#### JVM option changes

If you use Elasticsearch Service, skip this section. Elasticsearch Service handles these changes for you.

`es.disk.auto_release_flood_stage_block` has been removed.

**Details**

If a node exceeds the flood-stage disk watermark then we add a block to all of
its indices to prevent further writes as a last-ditch attempt to prevent the
node completely exhausting its disk space. By default, from 7.4 onwards the
block is automatically removed when a node drops below the high watermark
again, but this behaviour could be disabled by setting the system property
`es.disk.auto_release_flood_stage_block` to `false`. This behaviour is no
longer optional, and this system property must now not be set.

**Impact**

Discontinue use of the `es.disk.auto_release_flood_stage_block` system property.
Setting this system property will result in an error on startup.

`es.rest.url_plus_as_space` has been removed.

**Details**

Starting in version 7.4, a `+` in a URL will be encoded as `%2B` by all REST API functionality. Prior versions handled a `+` as a single space.
In these previous versions, if your application required handling `+` as a single space, you could return to the old behaviour by setting the system property
`es.rest.url_plus_as_space` to `true`. Note that this behaviour is deprecated and setting this system property to `true` will cease
to be supported in version 8.

**Impact**

Update your application or workflow to assume `+` in a URL is encoded as `%2B`.

`es.unsafely_permit_handshake_from_incompatible_builds` has been removed.

**Details**

Elasticsearch has a check that verifies that communicating pairs of nodes of the same
version are running exactly the same build and therefore using the same wire
format as each other. In previous versions this check can be bypassed by
setting the system property
`es.unsafely_permit_handshake_from_incompatible_builds` to `true`. The use of
this system property is now forbidden.

**Impact**

Discontinue use of the `es.unsafely_permit_handshake_from_incompatible_builds`
system property, and ensure that all nodes of the same version are running
exactly the same build. Setting this system property will result in an error
on startup.

#### Logging changes

Elasticsearch JSON logs now comply with ECS.

**Details**

Elasticsearch’s [JSON logs](/guide/en/elasticsearch/reference/8.17/logging.html) now comply with the
[Elastic Common Schema (ECS)](/guide/en/ecs/8.17/index.html). Previously, Elasticsearch’s JSON logs
used a custom schema.

**Impact**

If your application parses Elasticsearch’s JSON logs, update it to support the new ECS
format.

Elasticsearch no longer emits deprecation logs or slow logs in plaintext.

**Details**

Elasticsearch no longer emits a plaintext version of the following logs:

* Deprecation logs

* Indexing slow logs

* Search slow logs

These logs are now only available in JSON.

Server logs are still available in both a JSON and plaintext format.

**Impact**

If your application parses Elasticsearch’s plaintext logs, update it to use the new ECS
JSON logs.

Audit logs are rolled-over and archived by size.

**Details**

In addition to the existing daily rollover, the security audit logs are
now rolled-over by disk size limit as well. Moreover, the rolled-over logs
are also gzip compressed.

**Impact**

The names of rolled over audit log files (but not the name of the current log)
have changed.
If you’ve set up automated tools to consume these files, you must configure them
to use the new names and to possibly account for `gzip` archives instead of
plain text. The Docker build of Elasticsearch is not affected because it logs on `stdout`,
where rollover is not performed.

#### Mapping changes

Indices created in Elasticsearch 6.x and earlier versions are not supported.

**Details**

Elasticsearch 8.0 can read indices created in version 7.0 or above. An
Elasticsearch 8.0 node will not start in the presence of indices created in a
version of Elasticsearch before 7.0.

**Impact**

Reindex indices created in Elasticsearch 6.x or before with Elasticsearch 7.x if they need to be carried forward to  Elasticsearch 8.x.

Closed indices created in Elasticsearch 6.x and earlier versions are not supported.

**Details**

In earlier versions a node would start up even if it had data from indices
created in a version before the previous major version, as long as those
indices were closed. Elasticsearch now ensures that it is compatible with every index,
open or closed, at startup time.

**Impact**

Reindex closed indices created in Elasticsearch 6.x or before with Elasticsearch 7.x if they need
to be carried forward to Elasticsearch 8.x.

The maximum number of completion contexts per field is now 10.

**Details**

The number of completion contexts within a single completion field
has been limited to 10.

**Impact**

Use a maximum of 10 completion contexts in a completion field. Specifying more
than 10 completion contexts will return an error.

Multi-fields within multi-fields is no longer supported.

**Details**

Previously, it was possible to define a multi-field within a multi-field.
Defining chained multi-fields was deprecated in 7.3 and is now no longer
supported.

**Impact**

To migrate mappings, all instances of `fields` that occur within
a `fields` block should be removed, either by flattening the chained `fields`
blocks into a single level, or by switching to `copy_to` if appropriate.

The `_field_names` metadata field’s `enabled` parameter has been removed.

**Details**

The setting has been deprecated with 7.5 and is no longer supported on new indices.
Mappings for older indices will continue to work but emit a deprecation warning.

**Impact**

The `enabled` setting for `_field_names` should be removed from templates and mappings.
Disabling _field_names is not necessary because it no longer carries a large index overhead.

The `boost` parameter on field mappings has been removed.

**Details**

Index-time boosts have been deprecated since the 5x line, but it was still possible
to declare field-specific boosts in the mappings. This is now removed completely.
Indexes built in 7x that contain mapping boosts will emit warnings, and the boosts
will have no effect in 8.0. New indexes will not permit boosts to be set in their
mappings at all.

**Impact**

The `boost` setting should be removed from templates and mappings. Use boosts
directly on queries instead.

Java-time date formats replace joda-time formats.

**Details**

In 7.0, Elasticsearch switched from joda time to java time for date-related parsing,
formatting, and calculations. Indices created in 7.0 and later versions are
already required to use mappings with java-time date formats. However,
earlier indices using joda-time formats must be reindexed to use
mappings with java-time formats.

**Impact**

For a detailed migration guide, see the [Java
time migration guide](/guide/en/elasticsearch/reference/8.17/migrate-to-java-time.html).

Several `geo_shape` mapping parameters have been removed.

**Details**

The following `geo_shape` mapping parameters were deprecated in 6.6:

* `tree`

* `tree_levels`

* `strategy`

* `distance_error_pct`

These parameters have been removed in 8.0.0.

**Impact**

In 8.0, you can no longer create mappings that include these parameters.
However, 7.x indices that use these mapping parameters will continue to work.

The `sparse_vector` field data type has been removed.

**Details**

The `sparse_vector` field type was deprecated in 7.6 and is now removed in
8.0. We have not seen much interest in this experimental field type, and don’t
see a clear use case as it’s currently designed. If you have feedback or
suggestions around sparse vector functionality, please let us know through
GitHub or the *discuss* forums.

**Impact**

Discontinue use of the `sparse_vector` field data type. Requests containing
a mapping for this field data type will return an error.

#### Packaging changes

If you use Elasticsearch Service, skip this section. Elasticsearch Service handles these changes for you.

The layout of the data folder has changed.

**Details**

Each node’s data is now stored directly in the data directory set by the
`path.data` setting, rather than in `${path.data}/nodes/0`, because the removal
of the `node.max_local_storage_nodes` setting means that nodes may no longer
share a data path.

**Impact**

At startup, Elasticsearch will automatically migrate the data path to the new layout.
This automatic migration will not proceed if the data path contains data for
more than one node. You should move to a configuration in which each node has
its own data path before upgrading.

If you try to upgrade a configuration in which there is data for more than one
node in a data path then the automatic migration will fail and Elasticsearch
will refuse to start. To resolve this you will need to perform the migration
manually. The data for the extra nodes are stored in folders named
`${path.data}/nodes/1`, `${path.data}/nodes/2` and so on, and you should move
each of these folders to an appropriate location and then configure the
corresponding node to use this location for its data path. If your nodes each
have more than one data path in their `path.data` settings then you should move
all the corresponding subfolders in parallel. Each node uses the same subfolder
(e.g. `nodes/2`) across all its data paths.

The default Maxmind geoip databases have been removed.

**Details**

The default Maxmind geoip databases that shipped by default with Elasticsearch
have been removed. These databases are out dated and stale and using these
databases will likely result in incorrect geoip lookups.

By default since 7.13, these pre-packaged geoip databases
were used in case no database were specified in the config directory or before
the geoip downloader downloaded the geoip databases. When the geoip database
downloader completed downloading the new databases then these pre-packaged
databases were no longer used.

**Impact**

If the geoip downloader is disabled and no geoip databases are provided
in the config directory of each ingest node then the geoip processor will
no longer perform geoip lookups and tag these documents with the fact that
the requested database is no longer available.

After a cluster has been started and before the geoip downloader has completed
downloading the most up to data databases, the geoip processor will not perform
any geoip lookups and tag documents that the requested database is not available.
After the geoip downloader has completed downloading the most up to data databases
then the geoip processor will function as normal. The window of time that the
geoip processor can’t do geoip lookups after cluster startup should be very small.

#### Painless changes

The `JodaCompatibleZonedDateTime` class has been removed.

**Details**

As a transition from Joda datetime to Java datetime, scripting used
an intermediate class called `JodaCompatibleZonedDateTime`. This class
has been removed and is replaced by `ZonedDateTime`. Any use of casting
to a `JodaCompatibleZonedDateTime` or use of method calls only available
in `JodaCompatibleZonedDateTime` in a script will result in a compilation
error, and may not allow the upgraded node to start.

**Impact**

Before upgrading, replace `getDayOfWeek` with `getDayOfWeekEnum().value` in any
scripts. Any use of `getDayOfWeek` expecting a return value of `int` will result
in a compilation error or runtime error and may not allow the upgraded node to
start.

The following `JodaCompatibleZonedDateTime` methods must be replaced using
`ZonedDateTime` methods prior to upgrade:

* `getMillis()` → `toInstant().toEpochMilli()`

* `getCenturyOfEra()` → `get(ChronoField.YEAR_OF_ERA) / 100`

* `getEra()` → `get(ChronoField.ERA)`

* `getHourOfDay()` → `getHour()`

* `getMillisOfDay()` → `get(ChronoField.MILLI_OF_DAY)`

* `getMillisOfSecond()` → `get(ChronoField.MILLI_OF_SECOND)`

* `getMinuteOfDay()` → `get(ChronoField.MINUTE_OF_DAY)`

* `getMinuteOfHour()` → `getMinute()`

* `getMonthOfYear()` → `getMonthValue()`

* `getSecondOfDay()` → `get(ChronoField.SECOND_OF_DAY)`

* `getSecondOfMinute()` → `getSecond()`

* `getWeekOfWeekyear()` → `get(IsoFields.WEEK_OF_WEEK_BASED_YEAR)`

* `getWeekyear()` → `get(IsoFields.WEEK_BASED_YEAR)`

* `getYearOfCentury()` → `get(ChronoField.YEAR_OF_ERA) % 100`

* `getYearOfEra()` → `get(ChronoField.YEAR_OF_ERA)`

* `toString(String)` → a DateTimeFormatter

* `toString(String, Locale)` → a DateTimeFormatter

#### Plugin changes

If you use Elasticsearch Service, skip this section. Elasticsearch Service handles these changes for you.

The S3, GCS and Azure repository plugins are now included in Elasticsearch

**Details**

In previous versions of Elasticsearch, in order to register a snapshot repository
backed by Amazon S3, Google Cloud Storage (GCS) or Microsoft Azure Blob
Storage, you first had to install the corresponding Elasticsearch plugin,
for example `repository-s3`. These plugins are now included in Elasticsearch by
default.

**Impact**

You no longer need to install the following plugins, and not should attempt
to do so.

* `repository-azure`

* `repository-gcs`

* `repository-s3`

Elasticsearch and the `elasticsearch-plugin` CLI tool have been changed to tolerate
attempted installation and removal of these plugins in order to avoid
breaking any existing automation. In the future, attempting to install
these plugins will be an error.

Specifically, the `elasticsearch-plugin` CLI tool will not fail if you
attempt to install any of the above plugins, and will instead print a
warning and skip the plugins. If any of these plugins are already
installed, for example because you installed them when running an older
version of Elasticsearch, then you can still remove them with
`elasticsearch-plugin`. Attempting to remove them if they are not installed
will succeed but print a warnings.

If you run Elasticsearch using Docker and you are managing plugins using a
[configuration file](/guide/en/elasticsearch/plugins/8.17/manage-plugins-using-configuration-file.html), then when
Elasticsearch first starts after you upgrade it, it will remove the above plugins if
they already installed. If any of these plugins are specified in your
configuration file, Elasticsearch will ignore them and emit a warning log message.

Third party plugins can no longer intercept REST requests (`RestHandlerWrapper`)

**Details**

In previous versions of Elasticsearch, third-party plugins could implement the
`getRestHandlerWrapper` method to intercept all REST requests to the node. A
common use of this feature was to implement custom security plugins to replace
the built-in security features. This extension point is no longer available
to third-party plugins.

**Impact**

Some third-party plugins that were designed to work with earlier versions of
Elasticsearch might not be compatible with Elasticsearch version 8.0 or later.

If you depend on any plugins that are not produced and supported by Elastic,
check with the plugin author and ensure that the plugin is available for your
target version of Elasticsearch before upgrading.

#### REST API changes

REST API endpoints containing `_xpack` have been removed.

**Details**

In 7.0, we deprecated REST endpoints that contain `_xpack` in their path. These
endpoints are now removed in 8.0. Each endpoint that was deprecated and removed
is replaced with a new endpoint that does not contain `_xpack`. As an example,
`/{index}/_xpack/graph/_explore` is replaced by `/{index}/_graph/explore`.

**Impact**

Use the replacement REST API endpoints. Requests submitted to the `_xpack`
API endpoints will return an error.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), any requests that include
the`_xpack` prefix are rerouted to the corresponding URL without the `_xpack`
prefix.

REST API endpoints containing mapping types have been removed.

**Details**

Mapping types have been removed. API endpoints that contain a mapping type have
also been removed. Use a typeless endpoint instead.

| API | Typed API endpoint | Typeless API endpoint |
| --- | --- | --- |
| Bulk | <target>/<type>/_bulk | <target>/_bulk |
| Count | <target>/<type>/_count | <target>/_count |
| Delete | <index>/<type>/<_id> | <index>/_doc/<_id> |
| Delete by query | <target>/<type>/_delete_by_query | <target>/_delete_by_query |
| Explain | <index>/<type>/<_id>/_explain | <index>/_explain/<_id> |
| Get | <index>/<type>/<_id> | <index>/_doc/<_id> |
|  | <index>/<type>/<_id>/_source | <index>/_source/<_id> |
| Get field mapping | _mapping/<type>/field/<field> | _mapping/field/<field> |
|  | <target>/_mapping/<type>/field/<field> | <target>/_mapping/field/<field> |
| Get mapping | _mapping/<type> | _mapping or <target>/_mapping |
|  | <target>/<type>/_mapping | <target>/_mapping |
|  | <target>/_mapping/<type> | <target>/_mapping |
| Graph explore | <index>/<type>/_graph/explore | <index>/_graph/explore |
| Index | <target>/<type>/<_id>/_create | <target>/_create/<_id> |
|  | <target>/<type> | <target>/_doc |
|  | <target>/<type>/<_id> | <target>/_doc/<_id> |
| Multi get | <index>/<type>/_mget | <index>/_mget |
| Multi search | <target>/<type>/_msearch | <target>/_msearch |
| Multi search template | <target>/<type>/_msearch/template | <target>/_msearch/template |
| Multi term vectors | <index>/<type>/_mtermvectors | <index>/_mtermvectors |
| Rollup search | <target>/<type>/_rollup_search | <target>/_rollup_search |
| Search | <target>/<type>/_search | <target>/_search |
| Search template | <target>/<type>/_search/template | <target>/_search/template |
| Term vectors | <index>/<mapping_type>/<_id>/_termvectors | <index>/_termvectors<_id> |
|  | <index>/<mapping_type>/_termvectors | <index>/_termvectors |
| Update | <index>/<type>/<_id>/_update | <index>/_update/<_id> |
| Update by query | <target>/<type>/_update_by_query | <target>/_update_by_query |
| Update mapping | <target>/<type>/_mapping | <target>/_mapping |
|  | <target>/_mapping/<type> | <target>/_mapping |
|  | _mapping/<type> | <target>/_mapping |
| Validate | <target>/<type>/_validate/query | <target>/_validate/query |

**Impact**

Update your application to use typeless REST API endpoints. Requests to
endpoints that contain a mapping type will return an error.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), if a request includes a custom
mapping type it is ignored. The request is rerouted to the corresponding
typeless URL. Custom mapping types in request bodies and type related HTTP
parameters are ignored, and responses, where warranted, include `_type` :
`_doc`.

Cross-cluster search (CCS) is now only backward-compatible with the previous minor version.

**Details**

In 8.0+, Elastic supports searches from a local cluster to a remote cluster
running:

* The previous minor version.

* The same version.

* A newer minor version in the same major version.

Elastic also supports searches from a local cluster running the last minor
version of a major version to a remote cluster running any minor version in the
following major version. For example, a local 7.17 cluster can search any
remote 8.x cluster.

|  | Remote cluster version |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Local cluster version | 6.8 | 7.1–7.16 | 7.17 | 8.0 | 8.1 | 8.2 | 8.3 | 8.4 | 8.5 | 8.6 | 8.7 | 8.8 | 8.9 | 8.10 | 8.11 | 8.12 | 8.13 | 8.14 | 8.15 | 8.16 | 8.17 |
| 6.8 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 7.1–7.16 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 7.17 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.0 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.2 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.3 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.4 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.5 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.6 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.7 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.8 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.9 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.10 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.11 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.12 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.13 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.14 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.15 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.16 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8.17 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

For the [EQL search API](/guide/en/elasticsearch/reference/8.17/eql-search-api.html), the local and
remote clusters must use the same Elasticsearch version if they have versions prior to 7.17.7 (included) or prior to 8.5.1 (included).

For example, a local 8.0 cluster can search a remote 7.17 or any remote 8.x
cluster. However, a search from a local 8.0 cluster to a remote 7.16 or 6.8
cluster is not supported.

Previously, we also supported searches on remote clusters running:

* Any minor version of the local cluster’s major version.

* The last minor release of the previous major version.

However, such searches can result in undefined behavior.

**Impact**

If you only run cross-cluster searches on remote clusters using the same or a
newer version, no changes are needed.

If you previously searched remote clusters running an earlier version of Elasticsearch,
see [Ensure cross-cluster search
support](/guide/en/elasticsearch/reference/8.17/modules-cross-cluster-search.html#ensure-ccs-support) for recommended solutions.

A cross-cluster search using an unsupported configuration may still work. However, such
searches aren’t tested by Elastic, and their behavior isn’t guaranteed.

The `terms` aggregation no longer supports the `_term` order key.

**Details**

The `terms` aggregation no longer supports the `_term` key in `order` values. To
sort buckets by their term, use `_key` instead.

**Impact**

Discontinue use of the `_term` order key. Requests that include a `_term` order
key will return an error.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), the `_term` order is ignored and
`key` is used instead.

The `date_histogram` aggregation no longer supports the `_time` order key.

**Details**

The `date_histogram` aggregation no longer supports the `_time` key in `order`
values. To sort buckets by their key, use `_key` instead.

**Impact**

Discontinue use of the `_time` order key. Requests that include a `_time` order
key will return an error.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), the `_time` order is ignored and
`_key` is used instead.

The `moving_avg` aggregation has been removed.

**Details**

The `moving_avg` aggregation was deprecated in 6.4 and has been removed. To
calculate moving averages, use the
[`moving_fn`
aggregation](/guide/en/elasticsearch/reference/8.17/search-aggregations-pipeline-movfn-aggregation.html) instead.

**Impact**

Discontinue use of the `moving_avg` aggregation. Requests that include the
`moving_avg` aggregation will return an error.

The `percentiles` aggregation’s `percents` parameter no longer supports duplicate values.

**Details**

If you specify the `percents` parameter with the
[`percentiles` aggregation](/guide/en/elasticsearch/reference/8.17/search-aggregations-metrics-percentile-aggregation.html),
its values must be unique. Otherwise, an exception occurs.

**Impact**

Use unique values in the `percents` parameter of the `percentiles` aggregation.
Requests containing duplicate values in the `percents` parameter will return
an error.

The `date_histogram` aggregation’s `interval` parameter is no longer valid.

**Details**

It is now an error to specify the `interval` parameter to the
[`date_histogram`
aggregation](/guide/en/elasticsearch/reference/8.17/search-aggregations-bucket-datehistogram-aggregation.html) or the
[https://www.elastic.co/guide/en/elasticsearch/reference/8.17/search-aggregations-bucket-composite-aggregation.html#_date_histogram](/guide/en/elasticsearch/reference/8.17/search-aggregations-bucket-composite-aggregation.html#_date_histogram)[`composite
date_histogram` source.  Instead, please use either `calendar_interval` or
`fixed_interval` as appropriate.

**Impact**

Uses of the `interval` parameter in either the `date_histogram` aggregation or
the `date_histogram` composite source will now generate an error.  Instead
please use the more specific `fixed_interval` or `calendar_interval`
parameters.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), the `interval` parameter is
adapted to either a fixed or calendar interval.

The `nGram` and `edgeNGram` token filter names have been removed.

**Details**

The `nGram` and `edgeNGram` token filter names that have been deprecated since
version 6.4 have been removed. Both token filters can only be used by their
alternative names `ngram` and `edge_ngram` since version 7.0.

**Impact**

Use the equivalent `ngram` and `edge_ngram` token filters. Requests containing
the `nGram` and `edgeNGram` token filter names will return an error.

The `nGram` and `edgeNGram` tokenizer names have been removed.

**Details**

The `nGram` and `edgeNGram` tokenizer names haven been deprecated with 7.6 and are no longer
supported on new indices. Mappings for indices created after 7.6 will continue to work but
emit a deprecation warning. The tokenizer name should be changed to the fully equivalent
`ngram` or `edge_ngram` names for new indices and in index templates.

**Impact**

Use the `ngram` and `edge_ngram` tokenizers. Requests to create new indices
using the `nGram` and `edgeNGram` tokenizer names will return an error.

The `in_flight_requests` stat has been renamed `inflight_requests` in logs and diagnostic APIs.

**Details**

The name of the in flight requests circuit breaker in log output and diagnostic APIs (such as the node stats API) changes from `in_flight_requests` to `inflight_requests` to align it with the name of the corresponding settings.

**Impact**

Update your workflow and applications to use the `inflight_requests` stat in
place of `in_flight_requests`.

The voting configuration exclusions API endpoint has changed.

**Details**

The `POST /_cluster/voting_config_exclusions/{node_filter}` API has been
removed in favour of `POST /_cluster/voting_config_exclusions?node_names=...`
and `POST /_cluster/voting_config_exclusions?node_ids=...` which allow you to
specify the names or IDs of the nodes to exclude.

**Impact**

Use `POST /_cluster/voting_config_exclusions?node_ids=...` and specify the nodes
to exclude instead of using a node filter. Requests submitted to the
`/_cluster/voting_config_exclusions/{node_filter}` endpoint will return an
error.

Remote system indices are not followed automatically if they match an auto-follow pattern.

**Details**

Remote system indices matching an [auto-follow
pattern](/guide/en/elasticsearch/reference/8.17/ccr-auto-follow.html) won’t be configured as a follower index automatically.

**Impact**

Explicitly [create a follower index](/guide/en/elasticsearch/reference/8.17/ccr-put-follow.html) to follow a remote
system index if that’s the wanted behaviour.

The EQL `wildcard` function has been removed.

**Details**

The `wildcard` function was deprecated in Elasticsearch 7.13.0 and has been removed.

**Impact**

Use the `like` or `regex` [keywords](/guide/en/elasticsearch/reference/8.17/eql-syntax.html#eql-syntax-pattern-comparison-keywords) instead.

The ILM `freeze` action is now a no-op.

**Details**

The ILM freeze action is now a no-op and performs no action on the index, as the freeze API endpoint
has been removed in 8.0.

**Impact**

Update your ILM policies to remove the `freeze` action from the `cold` phase.

Additional validation for ILM policies.

**Details**

Creating or updating an ILM policy now requires that any referenced snapshot repositories and SLM
policies exist.

**Impact**

Update your code or configuration management to ensure that repositories and SLM policies are created
before any policies that reference them.

The deprecated `_upgrade` API has been removed.

**Details**

Previously, the `_upgrade` API upgraded indices from the previous major
version to the current version. The `_reindex` API should be used
instead for that purpose.

**Impact**

Requests made to the old `_upgrade` API will return an error.

The deprecated freeze index API has been removed.

**Details**

The freeze index API (`POST /<index>/_freeze`) has been removed.
[Improvements
in heap memory usage](/blog/significantly-decrease-your-elasticsearch-heap-memory-usage) have eliminated the reason to freeze indices.
You can still unfreeze existing frozen indices using the
[unfreeze index API](/guide/en/elasticsearch/reference/8.17/unfreeze-index-api.html). For some use cases, the
frozen tier may be a suitable replacement for frozen indices. See
[data tiers](/guide/en/elasticsearch/reference/8.17/data-tiers.html) for more information.

**Impact**

Requests made to the old freeze index API will return an error.

The force merge API’s `max_num_segments` and `only_expunge_deletes` parameters cannot both be specified in the same request.

**Details**

Previously, the force merge API allowed the parameters `only_expunge_deletes`
and `max_num_segments` to be set to a non default value at the same time. But
the `max_num_segments` was silently ignored when `only_expunge_deletes` is set
to `true`, leaving the false impression that it has been applied.

**Impact**

When using the [force merge API](/guide/en/elasticsearch/reference/8.17/indices-forcemerge.html), do not specify
values for both the `max_num_segments` and `only_expunge_deletes` parameters.
Requests that include values for both parameters will return an error.

The create or update index template API’s `template` parameter has been removed.

**Details**

In 6.0, we deprecated the `template` parameter in create or update index
template requests in favor of using `index_patterns`. Support for the `template`
parameter is now removed in 8.0.

**Impact**

Use the [create or update index template API](/guide/en/elasticsearch/reference/8.17/indices-templates-v1.html)'s
`index_patterns` parameter. Requests that include the `template` parameter will
return an error.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), the `template` parameter is mapped
to `index_patterns`.

Synced flush has been removed.

**Details**

Synced flush was deprecated in 7.6 and is removed in 8.0. Use a regular flush
instead as it has the same effect as a synced flush in 7.6 and later.

**Impact**

Use the [flush API](/guide/en/elasticsearch/reference/8.17/indices-flush.html). Requests to the
`/<index>/flush/synced` or `/flush/synced` endpoints will return an error.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), the request to synced flush is
routed to the equivalent non-synced flush URL.

The default for the `?wait_for_active_shards` parameter on the close index API has changed.

**Details**

When closing an index in earlier versions, by default Elasticsearch would not wait for
the shards of the closed index to be properly assigned before returning. From
version 8.0 onwards the default behaviour is to wait for shards to be assigned
according to the
[`index.write.wait_for_active_shards`
index setting](/guide/en/elasticsearch/reference/8.17/docs-index_.html#index-wait-for-active-shards).

**Impact**

Accept the new behaviour, or specify `?wait_for_active_shards=0` to preserve
the old behaviour if needed.

The index stats API’s `types` query parameter has been removed.

**Details**

The index stats API’s `types` query parameter has been removed. Previously, you
could combine `types` with the `indexing` query parameter to return indexing
stats for specific mapping types. Mapping types have been removed in 8.0.

**Impact**

Discontinue use of the `types` query parameter. Requests that include the
parameter will return an error.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), the `types` query parameter is
ignored and stats are returned for the entire index.

The `user_agent` ingest processor’s `ecs` parameter has no effect.

**Details**

In 7.2, we deprecated the `ecs` parameter for the `user_agent` ingest processor.
In 8.x, the `user_agent` ingest processor will only return [Elastic
Common Schema (ECS)](/guide/en/ecs/8.17) fields, regardless of the `ecs` value.

**Impact**

To avoid deprecation warnings, remove the parameter from your ingest pipelines.
If a pipeline specifies an `ecs` value, the value is ignored.

The `include_type_name` query parameter has been removed.

**Details**

The `include_type_name` query parameter has been removed from the index
creation, index template, and mapping APIs. Previously, you could set
`include_type_name` to `true` to indicate that requests and responses should
include a mapping type name. Mapping types have been removed in 8.x.

**Impact**

Discontinue use of the `include_type_name` query parameter. Requests that
include the parameter will return an error.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), the `include_type_name` query
parameter is ignored and any custom mapping types in the request are removed.

Reindex from remote now re-encodes URL-encoded index names.

**Details**

Reindex from remote would previously allow URL-encoded index names and not
re-encode them when generating the search request for the remote host. This
leniency has been removed such that all index names are correctly encoded when
reindex generates remote search requests.

**Impact**

Specify unencoded index names for reindex from remote requests.

In the reindex, delete by query, and update by query APIs, the `size` parameter has been renamed.

**Details**

Previously, a `_reindex` request had two different size specifications in the body:

* Outer level, determining the maximum number of documents to process

* Inside the `source` element, determining the scroll/batch size.

The outer level `size` parameter has now been renamed to `max_docs` to
avoid confusion and clarify its semantics.

Similarly, the `size` parameter has been renamed to `max_docs` for
`_delete_by_query` and `_update_by_query` to keep the 3 interfaces consistent.

**Impact**

Use the replacement parameters. Requests containing the `size` parameter will
return an error.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), the `size` parameter is mapped to
the `max_docs` parameter.

The update by query API now rejects unsupported `script` fields.

**Details**

An update by query API request that includes an unsupported field in the
`script` object now returns an error. Previously, the API would silently ignore
these unsupported fields.

**Impact**

To avoid errors, remove unsupported fields from the `script` object.

The cat node API’s `local` query parameter has been removed.

**Details**

The `?local` parameter to the `GET _cat/nodes` API was deprecated in 7.x and is
rejected in 8.0. This parameter caused the API to use the local cluster state
to determine the nodes returned by the API rather than the cluster state from
the master, but this API requests information from each selected node
regardless of the `?local` parameter which means this API does not run in a
fully node-local fashion.

**Impact**

Discontinue use of the `?local` query parameter. [cat node
API](/guide/en/elasticsearch/reference/8.17/cat-nodes.html) requests that include this parameter will return an error.

The cat shard API’s `local` query parameter has been removed.

**Details**

The `?local` parameter to the `GET _cat/shards` API was deprecated in 7.x and is
rejected in 8.0. This parameter caused the API to use the local cluster state
to determine the nodes returned by the API rather than the cluster state from
the master, but this API requests information from each selected node
regardless of the `?local` parameter which means this API does not run in a
fully node-local fashion.

**Impact**

Discontinue use of the `?local` query parameter. [cat shards
API](/guide/en/elasticsearch/reference/8.17/cat-shards.html) requests that include this parameter will return an error.

The cat indices API’s `local` query parameter has been removed.

**Details**

The `?local` parameter to the `GET _cat/indices` API was deprecated in 7.x and is
rejected in 8.0. This parameter caused the API to use the local cluster state
to determine the nodes returned by the API rather than the cluster state from
the master, but this API requests information from each selected node
regardless of the `?local` parameter which means this API does not run in a
fully node-local fashion.

**Impact**

Discontinue use of the `?local` query parameter. [cat indices
API](/guide/en/elasticsearch/reference/8.17/cat-indices.html) requests that include this parameter will return an error.

The get field mapping API’s `local` query parameter has been removed.

**Details**

The `local` parameter for get field mapping API was deprecated in 7.8 and is
removed in 8.0. This parameter is a no-op and field mappings are always retrieved
locally.

**Impact**

Discontinue use of the `local` query parameter.
[get field mapping API](/guide/en/elasticsearch/reference/8.17/indices-get-field-mapping.html) requests that
include this parameter will return an error.

Post data to jobs API is deprecated.

**Details**

The machine learning [post data to jobs API](/guide/en/elasticsearch/reference/8.17/ml-post-data.html) is deprecated starting in 7.11.0
and will be removed in a future major version.

**Impact**

Use [datafeeds](/guide/en/elasticsearch/reference/8.17/ml-ad-apis.html#ml-api-datafeed-endpoint) instead.

The `job_id` property of the Update datafeeds API has been removed.

**Details**

The ability to update a `job_id` in a datafeed was deprecated in 7.3.0. and is
removed in 8.0.

**Impact**

It is not possible to move datafeeds between anomaly detection jobs.

Create repository and delete repository API’s return `409` status code when a repository is in use instead of `500`.

**Details**

The [Create or update snapshot repository API](/guide/en/elasticsearch/reference/8.17/put-snapshot-repo-api.html) and
[Delete snapshot repository API](/guide/en/elasticsearch/reference/8.17/delete-snapshot-repo-api.html) return `409`
status code when the request is attempting to modify an existing repository that’s in use instead of status code `500`.

**Impact**

Update client code that handles creation and deletion of repositories to reflect this change.

The `allow_no_datafeeds` property has been removed from machine learning APIs.

**Details**

The `allow_no_datafeeds` property was deprecated in the
[cat datafeeds](/guide/en/elasticsearch/reference/8.17/cat-datafeeds.html),
[get datafeeds](/guide/en/elasticsearch/reference/8.17/ml-get-datafeed.html),
[get datafeed statistics](/guide/en/elasticsearch/reference/8.17/ml-get-datafeed-stats.html), and
[stop datafeeds](/guide/en/elasticsearch/reference/8.17/ml-stop-datafeed.html) APIs in 7.10.0.

**Impact**

Use `allow_no_match` instead.

The `allow_no_jobs` property has been removed from machine learning APIs.

**Details**

The `allow_no_jobs` property was deprecated in the
[cat anomaly detectors](/guide/en/elasticsearch/reference/8.17/cat-anomaly-detectors.html),
[close anomaly detection jobs](/guide/en/elasticsearch/reference/8.17/ml-close-job.html),
[get anomaly detection jobs](/guide/en/elasticsearch/reference/8.17/ml-get-job.html),
[get anomaly detection job statistics](/guide/en/elasticsearch/reference/8.17/ml-get-job-stats.html), and
[get overall buckets](/guide/en/elasticsearch/reference/8.17/ml-get-overall-buckets.html) APIs in 7.10.0.

**Impact**

Use `allow_no_match` instead.

The StartRollupJob endpoint now returns a success status if a job has already started.

**Details**

Previously, attempting to start an already-started rollup job would
result in a `500 InternalServerError: Cannot start task for Rollup Job
[job] because state was [STARTED]` exception.

Now, attempting to start a job that is already started will just
return a successful `200 OK: started` response.

**Impact**

Update your workflow and applications to assume that a 200 status in response to
attempting to start a rollup job means the job is in an actively started state.
The request itself may have started the job, or it was previously running and so
the request had no effect.

Stored scripts no longer support empty scripts or search templates.

**Details**

The [create or update stored script API](/guide/en/elasticsearch/reference/8.17/create-stored-script-api.html)'s
`source` parameter cannot be empty.

**Impact**

Before upgrading, use the [delete stored
script API](/guide/en/elasticsearch/reference/8.17/delete-stored-script-api.html) to delete any empty stored scripts or search templates.
In 8.0, Elasticsearch will drop any empty stored scripts or empty search templates from
the cluster state. Requests to create a stored script or search template with
an empty `source` will return an error.

The create or update stored script API’s `code` parameter has been removed.

**Details**

The [create or update stored script API](/guide/en/elasticsearch/reference/8.17/create-stored-script-api.html)'s
`code` parameter has been removed. Use the `source` parameter instead.

**Impact**

Discontinue use of the `code` parameter. Requests that include the parameter
will return an error.

Searches on the `_type` field are no longer supported.

**Details**

In 8.x, the `_type` metadata field has been removed. Elasticsearch now handles a search
on the `_type` field as a search on a non-existent field. A search on a
non-existent field matches no documents, regardless of the query string.

In 7.x, a search for `_doc` in the `_type` field would match the same documents
as a `match_all` query.

**Impact**

Remove queries on the `_type` field from your search requests and search
templates. Searches that include these queries may return no results.

The multi search API now parses an empty first line as action metadata in text files.

**Details**

The multi search API now parses an empty first line as empty action metadata
when you provide a text file as the request body, such as when using curl’s
`--data-binary` flag.

The API no longer supports text files that contain:

* An empty first line followed by a line containing only `{}`.

* An empty first line followed by another empty line.

**Impact**

Don’t provide an unsupported text file to the multi search API. Requests that
include an unsupported file will return an error.

The `unmapped_type: string` sort option has been removed.

**Details**

Search requests no longer support the `unmapped_type: string` sort option.
Instead, use `unmapped_type: keyword` to handle an unmapped field as if it had
the `keyword` field type but ignore its values for sorting.

**Impact**

Discontinue use of `unmapped_type: string`. Search requests that include the
`unmapped_type: string` sort option will return shard failures.

Aggregating and sorting on `_id` is disallowed by default.

**Details**

Previously, it was possible to aggregate and sort on the built-in `_id` field
by loading an expensive data structure called fielddata. This was deprecated
in 7.6 and is now disallowed by default in 8.0.

**Impact**

Aggregating and sorting on `_id` should be avoided. As an alternative, the
`_id` field’s contents can be duplicated into another field with docvalues
enabled (note that this does not apply to auto-generated IDs).

The `common` query has been removed.

**Details**

The `common` query, deprecated in 7.x, has been removed in 8.0.
The same functionality can be achieved by the `match` query if the total number of hits is not tracked.

**Impact**

Discontinue use of the `common` query. Search requests containing a `common`
query will return an error.

The `cutoff_frequency` parameter has been removed from the `match` and `multi_match` query.

**Details**

The `cutoff_frequency` parameter, deprecated in 7.x, has been removed in 8.0 from `match` and `multi_match` queries.
The same functionality can be achieved without any configuration provided that the total number of hits is not tracked.

**Impact**

Discontinue use of the `cutoff_frequency` parameter. Search requests containing
this parameter in a `match` or `multi_match` query will return an error.

The `nested_filter` and `nested_path` properties have been removed from the search API’s `sort` request body parameter.

**Details**

The `nested_filter` and `nested_path` options, deprecated in 6.x, have been removed in favor of the `nested` context.

**Impact**

Discontinue use of the `sort` request body parameter’s `nested_filter` and
`nested_path` properties. Requests containing these properties will return an
error.

Search and get requests are now routed to shards using adaptive replica selection by default.

**Details**

Elasticsearch will no longer prefer using shards in the same location (with the same awareness attribute values) to process
`_search` and `_get` requests. Adaptive replica selection (activated by default in this version) will route requests
more efficiently using the service time of prior inter-node communications.

**Impact**

No action needed.

Vector functions using `(query, doc['field'])` are no longer supported.

**Details**

The vector functions of the form `function(query, doc['field'])` were
deprecated in 7.6, and are now removed in 8.x. The form
`function(query, 'field')` should be used instead. For example,
`cosineSimilarity(query, doc['field'])` is replaced by
`cosineSimilarity(query, 'field')`.

**Impact**

Use the `function(query, 'field')` form. Discontinue use of the `function(query,
doc['field'])` form. Requests containing the `function(query,
doc['field'])` form will return an error.

The search API’s `indices_boost` request body parameter no longer accepts object values.

**Details**

The `indices_boost` option in the search request used to accept the boosts
both as an object and as an array. The object format has been deprecated since
5.2 and is now removed in 8.0.

**Impact**

Use only array values in the `indices_boost` parameter. Requests containing an
object value in the `indices_boost` parameter will return an error.

The search API’s `use_field_mapping` request body parameter has been removed.

**Details**

In 7.0, we began formatting `docvalue_fields` by default using each field’s
mapping definition. To ease the transition from 6.x, we added the format
option `use_field_mapping`. This parameter was deprecated in 7.0, and is now
removed in 8.0.

**Impact**

Discontinue use of the `use_field_mapping` request body parameter. Requests
containing this parameter will return an error.

**Compatibility**

When [rest-api-compatibility](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html) is
[requested](/guide/en/elasticsearch/reference/8.17/rest-api-compatibility.html), the `use_field_mapping` parameter
is ignored.

The search API’s `from` request body and url parameter cannot be negative.

**Details**

Search request used to accept `-1` as a `from` in the search body and the url,
treating it as the default value of 0. Other negative values got rejected with
an error already. We now also reject `-1` as an invalid value.

**Impact**

Change any use of `-1` as `from` parameter in request body or url parameters by either
setting it to `0` or omitting it entirely. Requests containing negative values will
return an error.

Range queries on date fields treat numeric values alwas as milliseconds-since-epoch.

**Details**

Range queries on date fields used to misinterpret small numbers (e.g. four digits like 1000)
as a year when no additional format was set, but would interpret other numeric values as
milliseconds since epoch. We now treat all numeric values in absence of a specific `format`
parameter as milliseconds since epoch. If you want to query for years instead, with a missing
`format` you now need to quote the input value (e.g. "1984").

**Impact**

If you query date fields without a specified `format`, check if the values in your queries are
actually meant to be milliseconds-since-epoch and use a numeric value in this case. If not, use
a string value which gets parsed by either the date format set on the field in the mappings or
by `strict_date_optional_time` by default.

The `geo_bounding_box` query’s `type` parameter has been removed.

**Details**

The `geo_bounding_box` query’s `type` parameter was deprecated in 7.14.0 and has
been removed in 8.0.0. This parameter is a no-op and has no effect on the query.

**Impact**

Discontinue use of the `type` parameter. `geo_bounding_box` queries that include
this parameter will return an error.

The `type` query has been removed.

**Details**

The `type` query has been removed. Mapping types have been removed in 8.0.

**Impact**

Discontinue use of the `type` query. Requests that include the `type` query
will return an error.

The `kibana_user` role has been renamed `kibana_admin`.

**Details**

Users who were previously assigned the `kibana_user` role should instead be assigned
the `kibana_admin` role. This role grants the same set of privileges as `kibana_user`, but has been
renamed to better reflect its intended use.

**Impact**

Assign users with the `kibana_user` role to the `kibana_admin` role.
Discontinue use of the `kibana_user` role.

For snapshot and SLM APIs, the `indices` parameter no longer resolves to system indices or system data streams.

**Details**

For snapshot and SLM APIs, the `indices` parameter no longer resolves to
system indices or system data streams.
[Feature states](/guide/en/elasticsearch/reference/8.17/snapshot-restore.html#feature-state) are now the only way
to back up and restore system indices or system data streams from a snapshot.

You can no longer use the `indices` parameter for the
[create SLM policy API](/guide/en/elasticsearch/reference/8.17/slm-api-put-policy.html) or the
[create snapshot API](/guide/en/elasticsearch/reference/8.17/create-snapshot-api.html) to include a system index in
a snapshot. To back up a system index, use the `include_global_state` and
`feature_states` parameters to include the corresponding feature state instead.
By default, the `include_global_state` and `feature_states` parameters include
all system indices.

Similarly, you can no longer use the [restore snapshot
API](/guide/en/elasticsearch/reference/8.17/restore-snapshot-api.html)'s `indices` parameter to restore a system index from a snapshot. To restore
a system index, use the `include_global_state` and `feature_states` parameters
to restore the corresponding feature state instead. By default, the
`include_global_state` and `feature_states` parameters don’t restore any system
indices.

**Impact**

If you previously used the `indices` parameter to back up or restore system
indices, update your SLM policies and application to use the
`include_global_state` and `feature_states` parameters instead.

An SLM policy that explicitly specifies a system index in the `indices`
parameter will fail to create snapshots. Similarly, a create snapshot API or
restore snapshot API request that explicitly specifies a system index in the
`indices` parameter will fail and return an error. If the `indices` value
includes a wildcard (`*`) pattern, the pattern will no longer match system
indices.

Snapshots compress metadata files by default.

**Details**

Previously, the default value for `compress` was `false`. The default has been changed to `true`.

This change will affect both newly created repositories and existing repositories where `compress=false` has not been
explicitly specified.

**Impact**

Update your workflow and applications to assume a default value of `true` for
the `compress` parameter.

S3 snapshot repositories now use a DNS-style access pattern by default.

**Details**

Starting in version 7.4, `s3` snapshot repositories no longer use the
now-deprecated path-style access pattern by default. In versions 7.0, 7.1, 7.2
and 7.3 `s3` snapshot repositories always used the path-style access pattern.
This is a breaking change for deployments that only support path-style access
but which are recognized as supporting DNS-style access by the AWS SDK. This
breaking change was made necessary by
[AWS’s
announcement](https://aws.amazon.com/blogs/aws/amazon-s3-path-deprecation-plan-the-rest-of-the-story/) that the path-style access pattern is deprecated and will be
unsupported on buckets created after September 30th 2020.

**Impact**

If your deployment only supports path-style access and is affected by this
change then you must configure the S3 client setting `path_style_access` to
`true`.

Restore requests no longer accept settings.

**Details**

In earlier versions, you could pass both `settings` and `index_settings` in the
body of a restore snapshot request, but the `settings` value was ignored. The
restore snapshot API now rejects requests that include a `settings` value.

**Impact**

Discontinue use of the `settings` parameter in restore
snapshot request. Requests that include these parameters will return an error.

The repository stats API has been removed.

**Details**

The repository stats API has been removed. We deprecated this experimental API
in 7.10.0.

**Impact**

Use the [repositories metering APIs](/guide/en/elasticsearch/reference/8.17/repositories-metering-apis.html)
instead.

Watcher history now writes to a hidden data stream.

**Details**

In 8.x, Elasticsearch writes Watcher history to a hidden
`.watcher-history-<index-template-version>` data stream. Previously, Elasticsearch wrote
Watcher history to hidden
`.watcher-history-<index-template-version>-<yyyy-MM-dd>` indices.

**Impact**

Update your requests to target the Watcher history data stream. For example, use
the `.watcher-history-*` wildcard expression. Requests that specifically target
non-existent Watcher history indices may return an error.

HTTP Status code has changed for the Cluster Health API in case of a server timeout.

**Details**

The [cluster health API](/guide/en/elasticsearch/reference/8.17/cluster-health.html) includes options for waiting
for certain health conditions to be satisfied. If the requested conditions are
not satisfied within a timeout then Elasticsearch will send back a normal response
including the field `"timed_out": true`. In earlier versions it would also use
the HTTP response code `408 Request timeout` if the request timed out, and `200
OK` otherwise. The `408 Request timeout` response code is not appropriate for
this situation, so from version 8.0.0 Elasticsearch will use the response code `200 OK`
for both cases.

**Impact**

To detect a server timeout, check the `timed_out` field of the JSON response.

The `Content-Type` response header no longer specifies the charset.

**Details**

The `Content-Type` response header no longer specifies the charset. This information is not required when transferring JSON data, because JSON text will always be encoded in Unicode, with UTF-8 being the default encoding.

**Impact**

Some applications and utilities, such as PowerShell’s [Invoke-RestMethod](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/invoke-restmethod), must receive charset information to display data correctly. If your application or utility relies on charset information in the `Content-Type` response header, UTF-8 encoded characters will be rendered incorrectly in the response body.

As a workaround, to render non-ASCII characters, include an HTTP `Accept` header in your requests, specifying the charset:

```
Accept: application/json; charset=utf-8
```

#### SQL JDBC changes

JDBC driver returns geometry objects as well-known-text string instead of `org.elasticsearch.geo` objects.

**Details**

To reduce the dependency of the JDBC driver onto Elasticsearch classes, the JDBC driver returns geometry data
as strings using the WKT (well-known text) format instead of classes from the `org.elasticsearch.geometry`.
Users can choose the geometry library desired to convert the string representation into a full-blown objects
either such as the `elasticsearch-geo` library (which returned the object `org.elasticsearch.geo` as before),
jts or spatial4j.

**Impact**

Before upgrading, replace any `org.elasticsearch.geo` classes on the `ResultSet#getObject` or `ResultSet#setObject`
Elasticsearch JDBC driver with their WKT representation by simply calling `toString` or
`org.elasticsearch.geometry.utils.WellKnownText#toWKT/fromWKT` methods.

This change does NOT impact users that do not use geometry classes.

#### System requirement changes

If you use Elasticsearch Service, skip this section. Elasticsearch Service handles these changes for you.

Several EOL operating systems are no longer supported.

**Details**

The following operating systems have reached their end of life and are no longer
supported by Elasticsearch:

* Amazon Linux

* CentOS 6

* Debian 8

* openSUSE Leap 42

* Oracle Enterprise Linux 6

* Ubuntu 16.04

We’ve also removed support for `SysV init`. No supported operating systems use
the `SysV init` process.

**Details**

Ensure your nodes use a
[supported operating system](/support/matrix#matrix_os).
Running Elasticsearch on an unsupported operating system can result in unexpected errors
or failures.

Java 17 is required.

**Details**

Java 17 or higher is now required to run Elasticsearch and any of its command
line tools.

**Impact**

Use Java 17 or higher. Attempts to run Elasticsearch 8.0 using earlier Java versions will
fail.

There is not yet a FIPS-certified security module for Java 17
that you can use when running Elasticsearch 8.0 in FIPS 140-2 mode.
If you run in FIPS 140-2 mode, you will either need to request an exception
from your security organization to upgrade to Elasticsearch 8.0,
or remain on Elasticsearch 7.x until Java 17 is certified.

`JAVA_HOME` is no longer supported.

**Details**

`JAVA_HOME` is no longer supported to set the path for the JDK. Instead, use
the bundled JDK (preferable), or set `ES_JAVA_HOME`.

**Impact**

Use the bundled JDK (preferable), or set `ES_JAVA_HOME`. `JAVA_HOME` will be
ignored.

#### Transform changes

Transforms created in 7.4 or earlier versions must be upgraded.

**Details**

Early beta versions of transforms had configuration information in a format
that is no longer supported.

**Impact**

Use the [upgrade transforms API](/guide/en/elasticsearch/reference/8.17/upgrade-transforms.html) to fix your
transforms. This upgrade does not affect the source or destination indices.

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.0
and will be removed in a future version.
While this won’t have an immediate impact on your applications,
we strongly encourage you take the described steps to update your code
after upgrading to 8.0.

To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Cluster and node setting deprecations

We no longer recommend using transient cluster settings.

**Details**

We no longer recommend using transient cluster settings. Use persistent cluster
settings instead. If a cluster becomes unstable, transient settings can clear
unexpectedly, resulting in an undesired cluster configuration.

**Impact**

Transient cluster settings are not yet deprecated, but we plan to deprecate them
in a future release. For migration steps, see the
[Transient settings migration
guide](/guide/en/elasticsearch/reference/8.17/transient-settings-migration-guide.html).

#### Command line tool deprecations

If you use Elasticsearch Service, skip this section. Elasticsearch Service handles these changes for you.

The `elasticsearch-setup-passwords` tool is deprecated.

**Details**

The `elasticsearch-setup-passwords` tool is deprecated in 8.0. To
manually reset the password for built-in users (including the `elastic` user), use
the [`elasticsearch-reset-password`](/guide/en/elasticsearch/reference/8.17/reset-password.html) tool, the Elasticsearch
[change passwords API](/guide/en/elasticsearch/reference/8.17/security-api-change-password.html), or the
User Management features in Kibana.
`elasticsearch-setup-passwords` will be removed in a future release.

**Impact**

Passwords are generated automatically for the `elastic` user when you start Elasticsearch for the first time. If you run `elasticsearch-setup-passwords` after
starting Elasticsearch, it will fail because the `elastic`
user password is already configured.