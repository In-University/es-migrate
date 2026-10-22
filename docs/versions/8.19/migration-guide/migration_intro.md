# Migration guide

This section discusses the changes that you need to be aware of to migrate
your application to {version}. For more information about what's new in this
release, see the [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

As Elasticsearch introduces new features and improves existing ones, the changes
sometimes make older settings, APIs, and parameters obsolete. We typically
deprecate obsolete functionality as part of a release. If possible, we support
the deprecated functionality for several subsequent releases before removing it.
This enables applications to continue working unchanged while you prepare to
migrate away from the deprecated functionality.

To get the most out of Elasticsearch and facilitate future upgrades, we strongly
encourage migrating away from using deprecated functionality as soon as
possible.

To give you insight into what deprecated features you're using, Elasticsearch:

- Returns a `Warn` HTTP header whenever you
submit a request that uses deprecated functionality.
- [Logs deprecation warnings](#deprecation-logging) when
deprecated functionality is used.
- [Provides a deprecation info API](#migration-api-deprecation)
that scans a cluster's configuration
and mappings for deprecated functionality.

For more information about {minor-version},
see the [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).
For information about how to upgrade your cluster, see [setup-upgrade](#setup-upgrade).