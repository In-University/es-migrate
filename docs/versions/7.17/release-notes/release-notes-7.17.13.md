**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.13

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

### Security updates

* Elasticsearch generally filters out sensitive information and credentials before
logging to the audit log. It was found that this filtering was not applied when
requests to Elasticsearch use certain deprecated `_xpack/security` URIs for APIs. The
impact of this flaw is that sensitive information, such as passwords and tokens,
might be printed in cleartext in Elasticsearch audit logs. Note that audit logging is
disabled by default and needs to be explicitly enabled. Even when audit logging
is enabled, request bodies that could contain sensitive information are not
printed to the audit log unless explicitly configured.

The issue is resolved in Elasticsearch 7.17.13.

For more information, see our related
[security
announcement](https://discuss.elastic.co/t/elasticsearch-8-9-2-and-7-17-13-security-update/342479).

### Enhancements

Infra/Core

* Enhance regex performance with duplicate wildcards [#98176](https://github.com/elastic/elasticsearch/pull/98176)

Search

* Refactor nested field handling in `FieldFetcher` [#97683](https://github.com/elastic/elasticsearch/pull/97683)