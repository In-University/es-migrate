**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 7.12

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.12.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

* [Engine changes](migrating-7.12.html#breaking_712_engine_changes)

* [Search changes](migrating-7.12.html#breaking_712_search_changes)

* [SSL/TLS changes](migrating-7.12.html#breaking_712_ssl_changes)

* [Settings deprecations](migrating-7.12.html#breaking_712_settings_deprecations)

### Breaking changes

The following changes in Elasticsearch 7.12 might affect your applications
and prevent them from operating normally.
Before upgrading to 7.12, review these changes and take the described steps
to mitigate the impact.

Breaking changes introduced in minor versions are
normally limited to security and bug fixes.
Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Engine changes

Force-merges on frozen and searchable snapshot indices will fail if merging is required.

**Details**

In earlier versions a force-merge on a frozen index or a searchable snapshot
index would incorrectly yield a successful response without performing the
requested merge. This bug is fixed in version 7.12: from this version onwards a
force-merge on these immutable indices will fail if the requested merge is not
a no-op.

#### Search changes

The search APIs `fields` parameter returns fields inside `nested` fields grouped together.

**Details**

In earlier versions, fields retrieved via `fields` in the search API were
returned as a flat list. From 7.12 on, fields inside an object that is mapped
using the `nested` field type are grouped together to maintain the independence of
each object inside the original nested array.

#### SSL/TLS changes

TLSv1.1 and TLSv1.0 are disabled in the bundled JDK

**Details**

As of Elasticsearch 7.12.1, when using the bundled JDK,
TLSv1.1 and TLSv1.0 are disabled by default.
This may affect SSL connections to the Rest API for some older clients.
It also has the potential to affect outgoing connections such as Watcher webhooks,
LDAP authentication or access to snapshot repositories.

Most Elasticsearch deployments will not be affected by this change, as these older
TLS versions have known vulnerabilities and are no longer heavily used.

For instructions on how to enable these older TLS versions in your Elasticsearch cluster,
see [Enabling additional
SSL/TLS versions on your JDK](/guide/en/elasticsearch/reference/7.17/jdk-tls-versions.html#jdk-enable-tls-protocol).

### Deprecations

The following functionality has been deprecated in Elasticsearch 7.12
and will be removed in 8.0
While this won’t have an immediate impact on your applications,
we strongly encourage you take the described steps to update your code
after upgrading to 7.12.

Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Settings deprecations

Setting `xpack.searchable.snapshot.shared_cache.size` on non-frozen nodes is deprecated.

**Details**

Setting `xpack.searchable.snapshot.shared_cache.size` to a positive value on a
node without the `data_frozen` role is now deprecated.

The `xpack.searchable.snapshot.shared_cache.size` node setting reserves space
for a shared cache used by partially mounted searchable snapshot indices. Elasticsearch only
allocates partially mounted indices to nodes with the `data_frozen` role.

**Impact**

To avoid deprecation warnings, discontinue use of the setting on non-frozen
nodes.