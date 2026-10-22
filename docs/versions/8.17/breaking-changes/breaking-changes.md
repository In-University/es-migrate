**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs/release-notes/elasticsearch/breaking-changes).

## Migration guide

This section discusses the changes that you need to be aware of to migrate
your application to 8.17.10. For more information about what’s new in this
release, see the [*What’s new in 8.17*](release-highlights.html) and [Release notes](es-release-notes.html).

As Elasticsearch introduces new features and improves existing ones, the changes
sometimes make older settings, APIs, and parameters obsolete. We typically
deprecate obsolete functionality as part of a release. If possible, we support
the deprecated functionality for several subsequent releases before removing it.
This enables applications to continue working unchanged while you prepare to
migrate away from the deprecated functionality.

To get the most out of Elasticsearch and facilitate future upgrades, we strongly
encourage migrating away from using deprecated functionality as soon as
possible.

To give you insight into what deprecated features you’re using, Elasticsearch:

* Returns a `Warn` HTTP header whenever you
submit a request that uses deprecated functionality.

* [Logs deprecation warnings](logging.html#deprecation-logging) when
deprecated functionality is used.

* [Provides a deprecation info API](migration-api-deprecation.html)
that scans a cluster’s configuration
and mappings for deprecated functionality.

For more information about 8.17,
see the [*What’s new in 8.17*](release-highlights.html) and [Release notes](es-release-notes.html).
For information about how to upgrade your cluster, see [Upgrade Elasticsearch](setup-upgrade.html).

* [Migrating to 8.17](migrating-8.17.html)

* [Migrating to 8.16](migrating-8.16.html)

* [Migrating to 8.15](migrating-8.15.html)

* [Migrating to 8.14](migrating-8.14.html)

* [Migrating to 8.13](migrating-8.13.html)

* [Migrating to 8.12](migrating-8.12.html)

* [Migrating to 8.11](migrating-8.11.html)

* [Migrating to 8.10](migrating-8.10.html)

* [Migrating to 8.9](migrating-8.9.html)

* [Migrating to 8.8](migrating-8.8.html)

* [Migrating to 8.7](migrating-8.7.html)

* [Migrating to 8.6](migrating-8.6.html)

* [Migrating to 8.5](migrating-8.5.html)

* [Migrating to 8.4](migrating-8.4.html)

* [Migrating to 8.3](migrating-8.3.html)

* [Migrating to 8.2](migrating-8.2.html)

* [Migrating to 8.1](migrating-8.1.html)

* [Migrating to 8.0](migrating-8.0.html)