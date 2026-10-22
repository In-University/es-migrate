**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.15

Also see [Breaking changes in 7.17](migrating-7.17.html#breaking-changes-7.17).

### Known issues

* High Memory Pressure due to a GC change in JDK 21

This version of Elasticsearch is bundled with JDK 21. In JDK 21
[Preventive GC has been removed](https://bugs.openjdk.org/browse/JDK-8297639).
This may lead to increased memory pressure and an increased number of CircuitBreakerExceptions when retrieving large
documents under some particular load. (issue: [#99592](https://github.com/elastic/elasticsearch/issues/99592))

If you needed to explicitly [enable Preventive GC for your workload in a previous Elasticsearch
version](release-notes-7.17.10.html#known-issues-7.17.10), we recommend you avoid to upgrade to this version, as the settings to enable Preventive GC have been removed
from JDK 21.

* The deprecated `index.mapper.dynamic` setting can break your cluster. It can only
be set using the **Update index settings API**. Symptoms include nodes failing to start
or shards failing to allocate. Do not use this setting in versions prior to 7.17.22.
The bug is fixed in 7.17.22.
(issue: [#109160](https://github.com/elastic/elasticsearch/issues/109160))

### Bug fixes

ILM+SLM

* `WaitForSnapshotStep` now verifies that the index belongs to the latest snapshot of that SLM policy [#100911](https://github.com/elastic/elasticsearch/pull/100911) (issue: [#57809](https://github.com/elastic/elasticsearch/issues/57809))

Network

* Ensure that all failures in `TcpTransport#openConnection` are treated consistently (all exceptions are now passed
to the listener). [#101907](https://github.com/elastic/elasticsearch/pull/101907) (issue: [#100510](https://github.com/elastic/elasticsearch/issues/100510))

* Protect `NodeConnectionsService` from stale connections [#92558](https://github.com/elastic/elasticsearch/pull/92558) (issue: [#92029](https://github.com/elastic/elasticsearch/issues/92029))

Snapshot/Restore

* Fix race condition in `SnapshotsService` [#101652](https://github.com/elastic/elasticsearch/pull/101652)

### Upgrades

Packaging

* Update bundled JDK to 21.0.1 [#101133](https://github.com/elastic/elasticsearch/pull/101133)