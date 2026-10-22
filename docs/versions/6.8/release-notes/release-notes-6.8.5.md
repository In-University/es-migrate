**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.5

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Known issues

* Slow loggers can cause Log4j loggers to leak over time. When a new index is created, a new Log4j logger is associated with it. However, when an index is deleted, Log4j keeps an internal reference to its loggers that results in a memory leak [#57228](https://github.com/elastic/elasticsearch/pull/57228) (issue: [#56171](https://github.com/elastic/elasticsearch/issues/56171))

This issue is fixed in Elasticsearch 6.8.10 and 7.7.1.

### Enhancements

Engine

* Avoid unneeded refresh with concurrent realtime gets [#47895](https://github.com/elastic/elasticsearch/pull/47895)

Infra/Settings

* Do not reference values for filtered settings [#48066](https://github.com/elastic/elasticsearch/pull/48066)

Machine Learning

* The machine learning native processes are now arranged in a `.app` directory structure on
macOS to allow for notarization on macOS Catalina [#593](https://github.com/elastic/ml-cpp/pull/593)

### Bug fixes

Allocation

* Handle negative free disk space in deciders [#48392](https://github.com/elastic/elasticsearch/pull/48392) (issue: [#48380](https://github.com/elastic/elasticsearch/issues/48380))

Analysis

* Actually close IndexAnalyzers contents [#43914](https://github.com/elastic/elasticsearch/pull/43914)

CCR

* Handle lower retaining sequence number retention lease error [#46420](https://github.com/elastic/elasticsearch/pull/46420) (issues: [#46013](https://github.com/elastic/elasticsearch/issues/46013), [#46416](https://github.com/elastic/elasticsearch/issues/46416))

CRUD

* Close query cache on index service creation failure [#48230](https://github.com/elastic/elasticsearch/pull/48230) (issue: [#48186](https://github.com/elastic/elasticsearch/issues/48186))

Engine

* Fix refresh optimization for realtime get in mixed cluster [#48151](https://github.com/elastic/elasticsearch/pull/48151) (issue: [#48114](https://github.com/elastic/elasticsearch/issues/48114))

Features/Java High Level REST Client

* Fix ILM HLRC Javadoc→documentation links [#48083](https://github.com/elastic/elasticsearch/pull/48083)

* Prevent deadlock in BulkProcessor by using separate schedulers [#48697](https://github.com/elastic/elasticsearch/pull/48697) (issue: [#47599](https://github.com/elastic/elasticsearch/issues/47599))

Infra/Logging

* Slow log must use separate underlying logger for each index [#47234](https://github.com/elastic/elasticsearch/pull/47234) (issue: [#42432](https://github.com/elastic/elasticsearch/issues/42432))

Machine Learning

* Restore from checkpoint could damage seasonality modeling. For example, it could
cause seasonal components to be overwritten in error [#821](https://github.com/elastic/ml-cpp/pull/821)

SQL

* Fix issue with negative literels and parentheses [#48113](https://github.com/elastic/elasticsearch/pull/48113) (issue: [#48009](https://github.com/elastic/elasticsearch/issues/48009))

* Failing group by queries due to different ExpressionIds [#43072](https://github.com/elastic/elasticsearch/pull/43072) (issues: [#33361](https://github.com/elastic/elasticsearch/issues/33361), [#34543](https://github.com/elastic/elasticsearch/issues/34543), [#36074](https://github.com/elastic/elasticsearch/issues/36074), [#37044](https://github.com/elastic/elasticsearch/issues/37044), [#40001](https://github.com/elastic/elasticsearch/issues/40001), [#40240](https://github.com/elastic/elasticsearch/issues/40240), [#41159](https://github.com/elastic/elasticsearch/issues/41159), [#42041](https://github.com/elastic/elasticsearch/issues/42041), [#46316](https://github.com/elastic/elasticsearch/issues/46316))

Snapshot/Restore

* Cleanup concurrent RepositoryData loading [#48329](https://github.com/elastic/elasticsearch/pull/48329) (issue: [#48122](https://github.com/elastic/elasticsearch/issues/48122))