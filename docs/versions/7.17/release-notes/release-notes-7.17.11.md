**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.11

Coming in 7.17.11.

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

Distributed

* Make cluster health API cancellable [#96551](https://github.com/elastic/elasticsearch/pull/96551)

Geo

* Port lucene tessellator fix github-12352 to Elasticsearch 7.17 [#96721](https://github.com/elastic/elasticsearch/pull/96721)

ILM+SLM

* [ILM] Fix the migrate to tiers service and migrate action tiers configuration [#95934](https://github.com/elastic/elasticsearch/pull/95934)

Search

* Increase concurrent request of opening point-in-time [#96782](https://github.com/elastic/elasticsearch/pull/96782)

Snapshot/Restore

* Fix Azure `InputStream#read` method [#96034](https://github.com/elastic/elasticsearch/pull/96034)

Watcher

* Avoiding running IO on scheduler thread in `ResourceWatcherService` [#96251](https://github.com/elastic/elasticsearch/pull/96251)

### Upgrades

Network

* Upgrade Netty to 4.1.89 [#95559](https://github.com/elastic/elasticsearch/pull/95559)