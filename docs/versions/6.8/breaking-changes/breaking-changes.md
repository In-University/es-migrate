**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs/release-notes/elasticsearch/breaking-changes).

## Breaking changes

This section discusses the changes that you need to be aware of when migrating
your application from one version of Elasticsearch to another.

As a general rule:

* Migration between minor versions — e.g. `6.x` to `6.y` — can be
performed by [upgrading one node at a time](rolling-upgrades.html).

* Migration between consecutive major versions — e.g. `5.x` to `6.x` — requires a [full cluster restart](restart-upgrade.html).

* Migration between non-consecutive major versions — e.g. `2.x` to `6.x` — is not supported.

For more information, see [Upgrade Elasticsearch](setup-upgrade.html).

See also [Release Highlights](release-highlights.html) and [Release Notes](es-release-notes.html).