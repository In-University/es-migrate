**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs/release-notes/elasticsearch/breaking-changes).

## Migration guide

This section describes the breaking changes and deprecations introduced in this release
and previous minor versions.

As Elasticsearch introduces new features and improves existing ones,
the changes sometimes make older settings, APIs, and parameters obsolete.
The obsolete functionality is typically deprecated in a minor release and
removed in the subsequent major release.
This enables applications to continue working unchanged across most minor version upgrades.
Breaking changes introduced in minor releases are generally limited to critical security fixes
and bug fixes that correct unintended behavior.

To get the most out of Elasticsearch and facilitate future upgrades, we strongly encourage migrating
away from using deprecated functionality as soon as possible.

To give you insight into what deprecated features you’re using, Elasticsearch:

* Returns a `Warn` HTTP header whenever you submit a request that uses deprecated functionality.

* [Logs deprecation warnings](logging.html#deprecation-logging) when deprecated functionality is used.

* [Provides a deprecation info API](migration-api-deprecation.html) that scans a cluster’s configuration
and mappings for deprecated functionality.

For more information about 7.17,
see the [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).
For information about how to upgrade your cluster, see [Upgrade Elasticsearch](setup-upgrade.html).

* [Migrating to 7.17](migrating-7.17.html#breaking-changes-7.17)

* [Migrating to 7.16](migrating-7.16.html#breaking-changes-7.16)

* [Migrating to 7.15](migrating-7.15.html#breaking-changes-7.15)

* [Migrating to 7.14](migrating-7.14.html#breaking-changes-7.14)

* [Migrating to 7.13](migrating-7.13.html#breaking-changes-7.13)

* [Migrating to 7.12](migrating-7.12.html#breaking-changes-7.12)

* [Migrating to 7.11](migrating-7.11.html#breaking-changes-7.11)

* [Migrating to 7.10](migrating-7.10.html#breaking-changes-7.10)

* [Migrating to 7.9](breaking-changes-7.9.html)

* [Migrating to 7.8](breaking-changes-7.8.html)

* [Migrating to 7.7](breaking-changes-7.7.html)

* [Migrating to 7.6](breaking-changes-7.6.html)

* [Migrating to 7.5](breaking-changes-7.5.html)

* [Migrating to 7.4](breaking-changes-7.4.html)

* [Migrating to 7.3](breaking-changes-7.3.html)

* [Migrating to 7.2](breaking-changes-7.2.html)

* [Migrating to 7.1](breaking-changes-7.1.html)

* [Migrating to 7.0](breaking-changes-7.0.html)