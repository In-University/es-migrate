## Migrating to 7.14

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.14.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

* [breaking_714_cluster_changes](#breaking_714_cluster_changes)
* [breaking_714_ccr_changes](#breaking_714_ccr_changes)
* [breaking_714_core_deprecations](#breaking_714_core_deprecations)
* [breaking_714_search_deprecations](#breaking_714_search_deprecations)
* [breaking_714_security_changes](#breaking_714_security_changes)

//NOTE: The notable-breaking-changes tagged regions are re-used in the
//Installation and Upgrade Guide

### Breaking changes

The following changes in Elasticsearch 7.14 might affect your applications
and prevent them from operating normally.
Before upgrading to 7.14, review these changes and take the described steps
to mitigate the impact.

NOTE: Breaking changes introduced in minor versions are
normally limited to security and bug fixes.
Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

// tag::notable-breaking-changes[]
#### Cluster changes

.Version barrier applies to all upgrades
[%collapsible]
====
*Details* +
If a failure occurs during a rolling upgrade then Elasticsearch may prematurely conclude
that the upgrade is complete and enable functionality which is incompatible
with earlier versions. In versions before 7.14 Elasticsearch would accept older nodes
into the cluster after completing the upgrade despite having enabled
incompatible functionality, as long as the older nodes were from the same major
series. From 7.14 onwards Elasticsearch will not accept any older nodes into a
fully-upgraded cluster.

*Impact* +
If a failure occurs during a rolling upgrade and older nodes cannot rejoin the
cluster then you must upgrade the affected nodes. Once upgraded, they will join
the cluster again.
====
// end::notable-breaking-changes[]

### Deprecations

The following functionality has been deprecated in Elasticsearch 7.14 and will be removed
in 8.0. While this won't have an immediate impact on your applications, we
strongly encourage you take the described steps to update your code after
upgrading to 7.14.

NOTE: Significant changes in behavior are deprecated in a minor release and the
old behavior is supported until the next major release. To find out if you are
using any deprecated functionality, enable [deprecation
logging](#deprecation-logging).

// tag::notable-breaking-changes[]

#### {ccr-cap} ({ccr-init}) deprecations

.Auto-follow remote system indices is deprecated.
[%collapsible]
====
*Details* +
Currently, remote system indices matching an
{ref}/ccr-auto-follow.html[auto-follow pattern] are configured as a follower
index automatically, this behavior is deprecated.

*Impact* +
In 8.0.0, remote system indices matching an
{ref}/ccr-auto-follow.html[auto-follow pattern] won't be configured as a
follower index automatically. In order to adapt to this new behaviour it is
advised to exclude patterns matching system indices such as `.tasks` and
`kibana-*`.
====

#### Core deprecations

.Setting `cluster.routing.allocation.disk.watermark.enable_for_single_data_node=false` is deprecated.
[%collapsible]
====
*Details* +
The setting `cluster.routing.allocation.disk.watermark.enable_for_single_data_node`
should never be explicitly set to false. In 8.0, the only legal value will be
true. In a future release, the setting will be removed completely, with same
behavior as if the setting was `true`.

*Impact* +

If your cluster has a single data node then set
`cluster.routing.allocation.disk.watermark.enable_for_single_data_node: true`
to opt in to the future behaviour today. If you wish to disable the disk
watermarks then set `cluster.routing.allocation.disk.threshold_enabled: false`.

If your cluster has multiple data nodes then the
`cluster.routing.allocation.disk.watermark.enable_for_single_data_node` setting
has no effect and you should discontinue its use.
====

#### Search deprecations

.The `geo_bounding_box` query's `type` parameter is deprecated.
[%collapsible]
====
*Details* +
The `geo_bounding_box` query's `type` parameter has been deprecated in 7.14.0.
This parameter is a no-op and has no effect on the query.

*Impact* +
Discontinue use of the `type` parameter in `geo_bounding_box` queries.
====

#### Security deprecations

.Having security disabled by default on basic and trial licenses is deprecated.
[%collapsible]
====
*Details* +
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
generating a certificate authority (if you don't have one), creating node
security certificates, and configuring internode communication. Refer to
[set up basic security for the {stack}](#security-basic-setup) for steps on
configuring security.
====

.Configuring a realm name with a leading underscore is deprecated.
[%collapsible]
====
*Details* +
Elasticsearch creates "synthetic" realm names on the fly for services like API keys.
These synthetic realm names are prefixed with an underscore.
Currently, user configured realms can also be given a name with a leading underscore.
This creates confusion since realm names are meant to be unique for a node.

*Impact* +
Configuring a realm name with a leading underscore is deprecated. In a future release of Elasticsearch
it will result in an error on startup if any user configured realm has a name
with a leading underscore.
====
// end::notable-breaking-changes[]