**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 7.14

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.14.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

* [Cluster changes](migrating-7.14.html#breaking_714_cluster_changes)

* [Cross-cluster replication (CCR) deprecations](migrating-7.14.html#breaking_714_ccr_changes)

* [Core deprecations](migrating-7.14.html#breaking_714_core_deprecations)

* [Search deprecations](migrating-7.14.html#breaking_714_search_deprecations)

* [Security deprecations](migrating-7.14.html#breaking_714_security_changes)

### Breaking changes

The following changes in Elasticsearch 7.14 might affect your applications
and prevent them from operating normally.
Before upgrading to 7.14, review these changes and take the described steps
to mitigate the impact.

Breaking changes introduced in minor versions are
normally limited to security and bug fixes.
Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Cluster changes

Version barrier applies to all upgrades

**Details**

If a failure occurs during a rolling upgrade then Elasticsearch may prematurely conclude
that the upgrade is complete and enable functionality which is incompatible
with earlier versions. In versions before 7.14 Elasticsearch would accept older nodes
into the cluster after completing the upgrade despite having enabled
incompatible functionality, as long as the older nodes were from the same major
series. From 7.14 onwards Elasticsearch will not accept any older nodes into a
fully-upgraded cluster.

**Impact**

If a failure occurs during a rolling upgrade and older nodes cannot rejoin the
cluster then you must upgrade the affected nodes. Once upgraded, they will join
the cluster again.

### Deprecations

The following functionality has been deprecated in Elasticsearch 7.14 and will be removed
in 8.0. While this won’t have an immediate impact on your applications, we
strongly encourage you take the described steps to update your code after
upgrading to 7.14.

Significant changes in behavior are deprecated in a minor release and the
old behavior is supported until the next major release. To find out if you are
using any deprecated functionality, enable [deprecation
logging](logging.html#deprecation-logging).

#### Cross-cluster replication (CCR) deprecations

Auto-follow remote system indices is deprecated.

**Details**

Currently, remote system indices matching an
[auto-follow pattern](/guide/en/elasticsearch/reference/7.17/ccr-auto-follow.html) are configured as a follower
index automatically, this behavior is deprecated.

**Impact**

In 8.0.0, remote system indices matching an
[auto-follow pattern](/guide/en/elasticsearch/reference/7.17/ccr-auto-follow.html) won’t be configured as a
follower index automatically. In order to adapt to this new behaviour it is
advised to exclude patterns matching system indices such as `.tasks` and
`kibana-*`.

#### Core deprecations

Setting `cluster.routing.allocation.disk.watermark.enable_for_single_data_node=false` is deprecated.

**Details**

The setting `cluster.routing.allocation.disk.watermark.enable_for_single_data_node`
should never be explicitly set to false. In 8.0, the only legal value will be
true. In a future release, the setting will be removed completely, with same
behavior as if the setting was `true`.

**Impact**

If your cluster has a single data node then set
`cluster.routing.allocation.disk.watermark.enable_for_single_data_node: true`
to opt in to the future behaviour today. If you wish to disable the disk
watermarks then set `cluster.routing.allocation.disk.threshold_enabled: false`.

If your cluster has multiple data nodes then the
`cluster.routing.allocation.disk.watermark.enable_for_single_data_node` setting
has no effect and you should discontinue its use.

#### Search deprecations

The `geo_bounding_box` query’s `type` parameter is deprecated.

**Details**

The `geo_bounding_box` query’s `type` parameter has been deprecated in 7.14.0.
This parameter is a no-op and has no effect on the query.

**Impact**

Discontinue use of the `type` parameter in `geo_bounding_box` queries.

#### Security deprecations

Having security disabled by default on basic and trial licenses is deprecated.

**Details**

Elasticsearch security features are disabled by default when operating on a basic or
trial license if `xpack.security.enabled` is not set to `true`. In Elasticsearch 8.0.0,
security features will be enabled by default for all licenses unless you
explicitly disable security by setting `xpack.security.enabled` to `false`
(not recommended).

Before migrating to Elasticsearch 8.0.0, you must explicitly set a value for
`xpack.security.enabled` or Elasticsearch will fail to start. If you have already
enabled security features by explicitly setting `xpack.security.enabled` to
`true`, your configuration will be respected in 8.0.0.

Otherwise, on every node in your cluster, enable Elasticsearch security features by
setting `xpack.security.enabled` to `true` in `elasticsearch.yml`. You then
configure security for the transport layer on each node, which requires
generating a certificate authority (if you don’t have one), creating node
security certificates, and configuring internode communication. Refer to
[set up basic security for the Elastic Stack](security-basic-setup.html) for steps on
configuring security.

Configuring a realm name with a leading underscore is deprecated.

**Details**

Elasticsearch creates "synthetic" realm names on the fly for services like API keys.
These synthetic realm names are prefixed with an underscore.
Currently, user configured realms can also be given a name with a leading underscore.
This creates confusion since realm names are meant to be unique for a node.

**Impact**

Configuring a realm name with a leading underscore is deprecated. In a future release of Elasticsearch
it will result in an error on startup if any user configured realm has a name
with a leading underscore.