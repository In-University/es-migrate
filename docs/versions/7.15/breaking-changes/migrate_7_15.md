## Migrating to 7.15

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.15.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

* [breaking_715_indices_deprecations](#breaking_715_indices_deprecations)
* [breaking_715_security_deprecations](#breaking_715_security_deprecations)
* [breaking_715_settings_deprecations](#breaking_715_settings_deprecations)

//NOTE: The notable-breaking-changes tagged regions are re-used in the
//Installation and Upgrade Guide

### Breaking changes

The following changes in Elasticsearch 7.15 might affect your applications
and prevent them from operating normally.
Before upgrading to 7.15, review these changes and take the described steps
to mitigate the impact.

NOTE: Breaking changes introduced in minor versions are
normally limited to security and bug fixes.
Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

### Deprecations

The following functionality has been deprecated in Elasticsearch 7.15 and will be removed
in 8.0. While this won't have an immediate impact on your applications, we
strongly encourage you take the described steps to update your code after
upgrading to 7.15.

NOTE: Significant changes in behavior are deprecated in a minor release and the
old behavior is supported until the next major release. To find out if you are
using any deprecated functionality, enable [deprecation
logging](#deprecation-logging).

// tag::notable-breaking-changes[]
#### Indices deprecations

.Indices created in Elasticsearch 6.x and earlier versions are deprecated.
[%collapsible]
====
*Details* +
In 8.x, Elasticsearch will only read indices created in version 7.0 or above. An 8.x node
will not start in the presence of indices created in 6.x or earlier versions of
Elasticsearch.

*Impact* +
Before upgrading to an 8.x version, reindex any index created in 6.x or earlier
versions with Elasticsearch 7.x. If you no longer need the index, delete it instead.
You can use the get index API to check the Elasticsearch version in which an index
was created.

[source,console]
```
GET *,-.*?human=true&filter_path=**.settings.index.version.created_string
```
====

.The `simpleifs` index store type is deprecated.
[%collapsible]
====
*Details* +
The `simplefs` value for the {ref}/index-modules-store.html[`index.store.type`]
index setting is now deprecated. Use the `niofs` value for superior or
equivalent performance instead.

*Impact* +
To avoid deprecation warnings, discontinue use of the `simpleifs` store type in
new indices or index templates. Reindex any index using `simplefs` into one with
another store type.
====

#### Security deprecations

.The `accept_default_password` setting is deprecated.
[%collapsible]
====
*Details* +
In 6.0, we deprecated the `accept_default_password` cluster setting. We removed
support for default passwords in 6.0 but did not remove the setting for
backwards compatibility. In 8.0, we will remove the setting.

*Impact* +
To avoid deprecation warnings, discontinue use of the setting.
====

.Native role cache settings are deprecated.
[%collapsible]
====
*Details* +
In 5.2, we deprecated the following cluster settings:

* `xpack.security.authz.store.roles.index.cache.max_size`
* `xpack.security.authz.store.roles.index.cache.ttl`

These native role cache settings have been unused since 5.2, but we did not
remove the settings for backwards compatibility. In 8.0, we will remove the
settings.

*Impact* +
To avoid deprecation warnings, discontinue use of the settings.
====

#### Settings deprecations

.Fractional byte size values are deprecated.
[%collapsible]
====
*Details* +
In 6.2, we deprecated support for fractional byte size values, such as `23.5pb`,
in:

* Cluster settings
* Index settings
* Cluster state metadata, such as an {ilm-init} policy, that support byte size
values

*Impact* +
To avoid deprecation warnings, discontinue use of fractional byte size values in
your configurations. Update any existing configurations to use whole values.
====
// end::notable-breaking-changes[]