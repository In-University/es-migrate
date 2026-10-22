**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.16

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

### Security updates

* The 7.17.16 patch release contains a fix for a potential security vulnerability. [Please see our security advisory for more details](https://discuss.elastic.co/c/announcements/security-announcements/31).

### Bug fixes

Infra/Circuit Breakers

* Add more logging to the real memory circuit breaker and lower minimum interval [#102396](https://github.com/elastic/elasticsearch/pull/102396)

Infra/Scripting

* Improve painless error wrapping [#100872](https://github.com/elastic/elasticsearch/pull/100872)

Transform

* Ensure transform updates only modify the expected transform task [#102934](https://github.com/elastic/elasticsearch/pull/102934) (issue: [#102933](https://github.com/elastic/elasticsearch/issues/102933))

### Upgrades

Snapshot/Restore

* Upgrade reactor netty http to v1.0.39 and reactor core to v3.4.34 [#102629](https://github.com/elastic/elasticsearch/pull/102629)