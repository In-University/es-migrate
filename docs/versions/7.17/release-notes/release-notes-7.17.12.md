**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.12

Also see [Breaking changes in 7.17](migrating-7.17.html#breaking-changes-7.17).

### Known issues

* High Memory Pressure due to a GC JVM setting change

This version of Elasticsearch is bundled with JDK 20. In JDK 20
[Preventive GC is disabled by default](https://bugs.openjdk.org/browse/JDK-8293861).
This may lead to increased memory pressure and an increased number of CircuitBreakerExceptions when retrieving large
documents under some load patterns. (issue: [#99592](https://github.com/elastic/elasticsearch/issues/99592))

If this change affects your use of Elasticsearch, consider re-enabling the previous behaviour
by adding the JVM arguments `-XX:+UnlockDiagnosticVMOptions -XX:+G1UsePreventiveGC` (reference:
[JDK 20 release notes](https://www.oracle.com/java/technologies/javase/20-relnote-issues.html#JDK-8293861)). It is
important to note that this workaround is temporary and works only with JDK 20, which is bundled with Elasticsearch up
to version 7.17.13 inclusive. Successive versions are bundling JDK 21+, where this setting
[has been removed](https://bugs.openjdk.org/browse/JDK-8297639). Specifying those JVM arguments will prevent the
JVM (and therefore Elasticsearch Nodes) from starting.

* The deprecated `index.mapper.dynamic` setting can break your cluster. It can only
be set using the **Update index settings API**. Symptoms include nodes failing to start
or shards failing to allocate. Do not use this setting in versions prior to 7.17.22.
The bug is fixed in 7.17.22.
(issue: [#109160](https://github.com/elastic/elasticsearch/issues/109160))

### Bug fixes

Aggregations

* Less jank in after-key parsing for unmapped fields [#97282](https://github.com/elastic/elasticsearch/pull/97282) (issue: [#85928](https://github.com/elastic/elasticsearch/issues/85928))

CRUD

* Handle failure in `TransportUpdateAction#handleUpdateFailureWithRetry` [#97290](https://github.com/elastic/elasticsearch/pull/97290) (issue: [#97286](https://github.com/elastic/elasticsearch/issues/97286))

Geo

* Support for Byte and Short as vector tiles features [#97619](https://github.com/elastic/elasticsearch/pull/97619) (issue: [#97612](https://github.com/elastic/elasticsearch/issues/97612))

Infra/Core

* Capture max processors in static init [#97119](https://github.com/elastic/elasticsearch/pull/97119) (issue: [#97088](https://github.com/elastic/elasticsearch/issues/97088))

* Preserve context in `ResultDeduplicator` [#84038](https://github.com/elastic/elasticsearch/pull/84038) (issue: [#84036](https://github.com/elastic/elasticsearch/issues/84036))

Snapshot/Restore

* Fix unhandled exception when blobstore repository contains unexpected file [#93914](https://github.com/elastic/elasticsearch/pull/93914)

### Enhancements

Transform

* Adding null check to fix potential NPE [#96785](https://github.com/elastic/elasticsearch/pull/96785) (issue: [#96781](https://github.com/elastic/elasticsearch/issues/96781))

### Upgrades

Network

* Upgrade Netty to 4.1.94.Final [#97114](https://github.com/elastic/elasticsearch/pull/97114)