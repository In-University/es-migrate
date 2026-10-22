**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.14

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

Infra/Core

* Fix deadlock between Cache.put and Cache.invalidateAll [#99480](https://github.com/elastic/elasticsearch/pull/99480) (issue: [#99326](https://github.com/elastic/elasticsearch/issues/99326))

Infra/Scripting

* Fix Painless method lookup over unknown super interfaces [#97062](https://github.com/elastic/elasticsearch/pull/97062) (issue: [#97022](https://github.com/elastic/elasticsearch/issues/97022))

Ingest Node

* Validate enrich index before completing policy execution [#100106](https://github.com/elastic/elasticsearch/pull/100106)

Machine Learning

* Defend against negative datafeed start times [#100284](https://github.com/elastic/elasticsearch/pull/100284)

Search

* Close expired search contexts on SEARCH thread [#99660](https://github.com/elastic/elasticsearch/pull/99660)

* Fix PIT when resolving with deleted indices [#99281](https://github.com/elastic/elasticsearch/pull/99281)

### Enhancements

Infra/Node Lifecycle

* Check ILM status before reporting node migration STALLED [#98367](https://github.com/elastic/elasticsearch/pull/98367) (issue: [#89486](https://github.com/elastic/elasticsearch/issues/89486))

Ingest Node

* Show concrete error when enrich index not exist rather than NPE [#99604](https://github.com/elastic/elasticsearch/pull/99604)

### Upgrades

Packaging

* Upgrade bundled JDK to Java 21 [#99724](https://github.com/elastic/elasticsearch/pull/99724)