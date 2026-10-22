**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.10

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

Allocation

* Skip `DiskThresholdMonitor` when cluster state is not recovered [#93699](https://github.com/elastic/elasticsearch/pull/93699)

CCR

* Deduplicate Heavy CCR Repository CS Requests [#91398](https://github.com/elastic/elasticsearch/pull/91398)

ILM+SLM

* Allow ILM step transition to the phase terminal step [#91754](https://github.com/elastic/elasticsearch/pull/91754)

* Allow ILM to transition to implicit cached steps [#91779](https://github.com/elastic/elasticsearch/pull/91779) (issue: [#91749](https://github.com/elastic/elasticsearch/issues/91749))

* Avoiding `BulkProcessor` deadlock in ILMHistoryStore [#91238](https://github.com/elastic/elasticsearch/pull/91238) (issues: [#68468](https://github.com/elastic/elasticsearch/issues/68468), [#50440](https://github.com/elastic/elasticsearch/issues/50440))

* Retry clean and create snapshot if it already exists #83694 [#84829](https://github.com/elastic/elasticsearch/pull/84829) (issue: [#83694](https://github.com/elastic/elasticsearch/issues/83694))

Infra/Core

* Add checks for exception loops through suppressed exceptions only [#93944](https://github.com/elastic/elasticsearch/pull/93944) (issue: [#93943](https://github.com/elastic/elasticsearch/issues/93943))

* Check no unassigned shards even if the node already left [#94722](https://github.com/elastic/elasticsearch/pull/94722)

Infra/REST API

* Fixes CORS headers needed by Elastic clients [#85791](https://github.com/elastic/elasticsearch/pull/85791)

Ingest Node

* Fix async enrich execution prematurely releases enrich policy lock [#94702](https://github.com/elastic/elasticsearch/pull/94702) (issue: [#94690](https://github.com/elastic/elasticsearch/issues/94690))

Search

* Fix _id field fetch issue. [#94528](https://github.com/elastic/elasticsearch/pull/94528) (issue: [#94515](https://github.com/elastic/elasticsearch/issues/94515))

* Return 200 when closing empty PIT or scroll [#94708](https://github.com/elastic/elasticsearch/pull/94708)

Stats

* Fix _cluster/stats `.nodes.fs` deduplication [#94798](https://github.com/elastic/elasticsearch/pull/94798) (issue: [#24472](https://github.com/elastic/elasticsearch/issues/24472))

* Fix `FsInfo` device deduplication [#94744](https://github.com/elastic/elasticsearch/pull/94744)

Transform

* Catch deprecations as `Exception` rather than `IOException` [#94553](https://github.com/elastic/elasticsearch/pull/94553)

### Enhancements

Authorization

* Reuse `FieldPermissionsCache` in Role parsing [#94931](https://github.com/elastic/elasticsearch/pull/94931)

Ingest Node

* Refactor enrich maintenance coordination logic [#90931](https://github.com/elastic/elasticsearch/pull/90931)

### Upgrades

Packaging

* Upgrade bundled JDK to Java 20 [#94600](https://github.com/elastic/elasticsearch/pull/94600)

* Bump bundled JDK to Java 20.0.1 [#95371](https://github.com/elastic/elasticsearch/pull/95371)