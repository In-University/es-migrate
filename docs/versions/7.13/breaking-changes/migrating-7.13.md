**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 7.13

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.13.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

* [Mapping changes](migrating-7.13.html#breaking_713_mapping_changes)

* [SSL/TLS changes](migrating-7.13.html#breaking_713_ssl_changes)

* [Settings changes](migrating-7.13.html#breaking_713_settings_changes)

* [Aggregation deprecations](migrating-7.13.html#breaking_713_agg_deprecations)

* [Core deprecations](migrating-7.13.html#breaking_713_infra_core_deprecations)

* [EQL deprecations](migrating-7.13.html#breaking_713_eql_deprecations)

* [Security deprecations](migrating-7.13.html#breaking_713_security_deprecations)

* [Settings deprecations](migrating-7.13.html#breaking_713_settings_deprecations)

### Breaking changes

The following changes in Elasticsearch 7.13 might affect your applications
and prevent them from operating normally.
Before upgrading to 7.13, review these changes and take the described steps
to mitigate the impact.

Breaking changes introduced in minor versions are
normally limited to security and bug fixes.
Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Mapping changes

Geo mappers no longer accept external values from multifields.

**Details**

In earlier versions, geo fields could theoretically be used as a subfield
if their parent field set a geometry object as an external value during
parsing. This functionality was unused within the Elasticsearch codebase and
blocked required changes to allow index-time scripts on `geo_point` fields,
so it has been removed.

Geopoint mappers pass geohashes to subfields one-by-one.

**Details**

In earlier versions, a multiply-valued geopoint field would pass
its values as geohashes to subfields by combining them in to a single
comma-delimited string. These are now passed one-by-one as single
geohash strings.

#### SSL/TLS changes

TLSv1.1 and TLSv1.0 are disabled in the bundled JDK

**Details**

When using the bundled JDK, TLSv1.1 and TLSv1.0 are disabled by default.
This may affect SSL connections to the Rest API for some older clients.
It also has the potential to affect outgoing connections such as Watcher webhooks,
LDAP authentication or access to snapshot repositories.

Most Elasticsearch deployments will not be affected by this change, as these older
TLS versions have known vulnerabilities and are no longer heavily used.

For instructions on how to enable these older TLS versions in your Elasticsearch cluster,
see [Enabling additional
SSL/TLS versions on your JDK](/guide/en/elasticsearch/reference/7.17/jdk-tls-versions.html#jdk-enable-tls-protocol).

#### Settings changes

`xpack.searchable.snapshot.shared_cache.size` is no longer a supported user setting for Elasticsearch Service

**Details**

You can no longer configure
[`xpack.searchable.snapshot.shared_cache.size`](/guide/en/elasticsearch/reference/7.17/searchable-snapshots.html#searchable-snapshots-shared-cache)
on Elasticsearch Service deployments running Elasticsearch 7.13 or a later version. This setting reserves
disk space for the shared cache of partially mounted indices. Elasticsearch now
automatically configures the setting to 90% of total disk space for frozen data
tier nodes and to `0b` for non-frozen data tier nodes.

**Impact**

If you use Elasticsearch Service and previously configured
`xpack.searchable.snapshot.shared_cache.size`, remove it from your
[user settings](/guide/en/cloud/current/ec-add-user-settings.html) before upgrading to 7.13 or a
later version. Otherwise, attempts to upgrade the deployment will fail and
return an error.

Changes to the frozen tier and multiple data paths

**Details**

Elasticsearch 7.12 included a technical preview of the frozen tier, being able to use
partially mounted indices (searchable snapshots mounted with the shared cache
option). Trying out this feature required configuring a shared cache using the
`xpack.searchable.snapshot.shared_cache.size` setting.

In Elasticsearch 7.13+, having a non-zero `xpack.searchable.snapshot.shared_cache.size`
on nodes utilizing multiple data paths (`path.data` points to multiple
locations) is no longer supported and will prevent the node from starting. If
you do not utilize multiple data paths this will not affect you. Likewise, if
you have not set `xpack.searchable.snapshot.shared_cache.size` and have not
configured dedicated frozen nodes (nodes with the `data_frozen` role and no
other data roles) this will not affect you.

### Deprecations

The following functionality has been deprecated in Elasticsearch 7.13
and will be removed in 8.0.
While this won’t have an immediate impact on your applications,
we strongly encourage you take the described steps to update your code
after upgrading to 7.13.

Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Aggregation deprecations

Date aggregations on `boolean` fields are deprecated.

**Details**

Support for auto-interval date histogram, date histogram, and date range
aggregations on `boolean` fields is now deprecated. On `boolean` fields, these
aggregations are rarely useful and often unintended.

#### Core deprecations

Multiple data path support is deprecated.

**Details**

The `path.data` setting accepts a list of data paths, but if you specify
multiple paths then the behaviour is unintuitive and usually does not give the
desired outcomes. Support for multiple data paths is now deprecated and will be
removed in a future release.

**Impact**

To avoid deprecation warnings, specify a single path in `path.data`. If needed,
you can create a filesystem which spans multiple disks with a hardware
virtualisation layer such as RAID, or a software virtualisation layer such as
Logical Volume Manager (LVM) on Linux or Storage Spaces on Windows. If you wish
to use multiple data paths on a single machine then you must run one node for
each data path.

If you currently use multiple data paths in a
[highly available cluster](/guide/en/elasticsearch/reference/7.17/high-availability-cluster-design.html) then you
can migrate to a setup that uses a single path for each node without downtime
using a process similar to a
[rolling restart](/guide/en/elasticsearch/reference/7.17/restart-cluster.html#restart-cluster-rolling): shut each
node down in turn and replace it with one or more nodes each configured to use
a single data path. In more detail, for each node that currently has multiple
data paths you should follow the following process.

* Take a snapshot to protect your data in case of disaster.

* Optionally, migrate the data away from the target node by using an
[allocation filter](/guide/en/elasticsearch/reference/7.17/modules-cluster.html#cluster-shard-allocation-filtering):

```
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.exclude._name": "target-node-name"
  }
}
```

You can use the [cat allocation API](/guide/en/elasticsearch/reference/7.17/cat-allocation.html) to track progress
of this data migration. If some shards do not migrate then the
[cluster allocation explain API](/guide/en/elasticsearch/reference/7.17/cluster-allocation-explain.html) will help
you to determine why.

* Follow the steps in the
[rolling restart process](/guide/en/elasticsearch/reference/7.17/restart-cluster.html#restart-cluster-rolling)
up to and including shutting the target node down.

* Ensure your cluster health is `yellow` or `green`, so that there is a copy
of every shard assigned to at least one of the other nodes in your cluster.

* If applicable, remove the allocation filter applied in the earlier step.

```
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.exclude._name": null
  }
}
```

* Discard the data held by the stopped node by deleting the contents of its
data paths.

* Reconfigure your storage. For instance, combine your disks into a single
filesystem using LVM or Storage Spaces. Ensure that your reconfigured storage
has sufficient space for the data that it will hold.

* Reconfigure your node by adjusting the `path.data` setting in its
`elasticsearch.yml` file. If needed, install more nodes each with their own
`path.data` setting pointing at a separate data path.

* Start the new nodes and follow the rest of the
[rolling restart process](/guide/en/elasticsearch/reference/7.17/restart-cluster.html#restart-cluster-rolling) for
them.

* Ensure your cluster health is `green`, so that every shard has been
assigned.

You can alternatively add some number of single-data-path nodes to your
cluster, migrate all your data over to these new nodes using
[allocation filters](/guide/en/elasticsearch/reference/7.17/modules-cluster.html#cluster-shard-allocation-filtering),
and then remove the old nodes from the cluster. This approach will temporarily
double the size of your cluster so it will only work if you have the capacity to
expand your cluster like this.

If you currently use multiple data paths but your cluster is not highly
available then the you can migrate to a non-deprecated configuration by taking
a snapshot, creating a new cluster with the desired configuration and restoring
the snapshot into it.

The `action.destructive_requires_name` setting will default to `true` in 8.0.0.

**Details**

In 8.0.0, the `action.destructive_requires_name` setting will default to `true`.
Currently, the setting defaults to `false`.

**Impact**

If you use a wildcard (`*`) or `_all` to delete indices or perform other
destructive actions, use the [update cluster
settings API](/guide/en/elasticsearch/reference/7.17/cluster-update-settings.html) to set `action.destructive_requires_name` to `false` to avoid
errors in 8.0.0.

`index.indexing.slowlog.level` and `index.search.slowlog.level` are deprecated.

**Details**

The `index.indexing.slowlog.level` and `index.search.slowlog.level` index
settings are now deprecated. You use these setting to set the logging level for
the search and indexing slow logs. To reproduce similar results, use the
respective `index.indexing.slowlog.threshold.index.debug` and
`index.indexing.slowlog.threshold.index.trace` index settings instead.
The same applies to `index.search.slowlog.level` which should be replaced with
`index.search.slowlog.threshold.query.{level}`.

For example, to reproduce a `index.indexing.slowlog.level` setting of `INFO`,
set `index.indexing.slowlog.threshold.index.debug` and
`index.indexing.slowlog.threshold.index.trace` to `-1`.

**Impact**

To avoid deprecation warnings, discontinue use of the deprecated settings.

#### EQL deprecations

The `wildcard` function is deprecated.

**Impact**

Use the [`like`](/guide/en/elasticsearch/reference/7.17/eql-syntax.html#eql-syntax-pattern-comparison-keywords) or
[`regex`](/guide/en/elasticsearch/reference/7.17/eql-syntax.html#eql-syntax-pattern-comparison-keywords) keyword
instead.

#### Security deprecations

Implicit enablement of the file and native realms is deprecated.

**Details**

Currently, the file and native realms have the following implicit behaviors:

* If file and native realms are not configured, they are implicitly disabled
if there are other explicitly configured realms.

* If no realm is available because realms are unconfigured, explicitly
disabled, or not allowed by your license, the file and native realms are always
enabled, even if explicitly disabled.

**Impact**

Both of the above behaviors are deprecated. In 8.0.0, the file and
native realms will always be enabled unless explicitly disabled. If they are
explicitly disabled, they remain disabled at all times.

System call filter setting deprecated

**Details**

Elasticsearch uses system call filters to remove its ability to fork another
process. This is useful to mitigate remote code exploits. These system call
filters are enabled by default, and controlled via the setting
`bootstrap.system_call_filter`. Starting in Elasticsearch 8.0, system call
filters will be required. As such, the setting `bootstrap.system_call_filter` is
deprecated and will be removed in Elasticsearch 8.0.

**Impact**

Discontinue use of the removed setting. Specifying this setting in Elasticsearch
configuration will result in an error on startup.

#### Settings deprecations

Several tier filtering settings are deprecated.

**Details**

The following cluster settings are now deprecated:

* `cluster.routing.allocation.include._tier`

* `cluster.routing.allocation.exclude._tier`

* `cluster.routing.allocation.require._tier`

The following index settings are also now deprecated:

* `index.routing.allocation.include._tier`

* `index.routing.allocation.exclude._tier`

* `index.routing.allocation.require._tier`

These settings are used to filter the allocation of a shard to a specific set of
nodes. Instead, use the
[`index.routing.allocation.include._tier_preference`](/guide/en/elasticsearch/reference/7.17/data-tier-shard-filtering.html#tier-preference-allocation-filter)
index setting.

**Impact**

To avoid deprecation warnings, discontinue use of the deprecated settings.

The `path.shared_data` and `index.data_path` settings are deprecated.

**Details**

The `path.shared_data` node setting and `index.data_path` index setting are
now deprecated. Elasticsearch previously used these settings for
[shadow replicas](/guide/en/elasticsearch/reference/5.6/indices-shadow-replicas.html). The shadow
replicas feature was deprecated in 5.2 and removed in 6.0.

**Impact**

To avoid deprecation warnings, discontinue use of the deprecated settings.