**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.7

### Known issues

* Slow loggers can cause Log4j loggers to leak over time. When a new index is created, a new Log4j logger is associated with it. However, when an index is deleted, Log4j keeps an internal reference to its loggers that results in a memory leak [#57228](https://github.com/elastic/elasticsearch/pull/57228) (issue: [#56171](https://github.com/elastic/elasticsearch/issues/56171))

This issue is fixed in Elasticsearch 6.8.10 and 7.7.1.

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Bug fixes

Authentication

* Preserve ApiKey credentials for async verification [#51244](https://github.com/elastic/elasticsearch/pull/51244)

CCR

* Fix shard follow task cleaner under security [#52347](https://github.com/elastic/elasticsearch/pull/52347) (issues: [#44702](https://github.com/elastic/elasticsearch/issues/44702), [#51971](https://github.com/elastic/elasticsearch/issues/51971))

Engine

* Account soft-deletes in FrozenEngine [#51192](https://github.com/elastic/elasticsearch/pull/51192) (issue: [#50775](https://github.com/elastic/elasticsearch/issues/50775))

Features/Java Low Level REST Client

* Improve warning value extraction performance in Response [#50208](https://github.com/elastic/elasticsearch/pull/50208) (issue: [#24114](https://github.com/elastic/elasticsearch/issues/24114))

Infra/Core

* Ignore virtual ethernet devices that disappear [#51581](https://github.com/elastic/elasticsearch/pull/51581) (issue: [#49914](https://github.com/elastic/elasticsearch/issues/49914))

Machine Learning

* Include out-of-order as well as in-order terms in categorization reverse
searches [#950](https://github.com/elastic/ml-cpp/pull/950) (issue: [#949](https://github.com/elastic/ml-cpp/issues/949))

SQL

* Fix ORDER BY on aggregates and GROUPed BY fields [#51894](https://github.com/elastic/elasticsearch/pull/51894) (issue: [#50355](https://github.com/elastic/elasticsearch/issues/50355))

* Fix ORDER BY YEAR() function [#51562](https://github.com/elastic/elasticsearch/pull/51562) (issue: [#51224](https://github.com/elastic/elasticsearch/issues/51224))

* Fix issue with CAST and NULL checking. [#50371](https://github.com/elastic/elasticsearch/pull/50371) (issue: [#50191](https://github.com/elastic/elasticsearch/issues/50191))

Search

* Fix NPE bug inner_hits [#50709](https://github.com/elastic/elasticsearch/pull/50709) (issue: [#50539](https://github.com/elastic/elasticsearch/issues/50539))

### Enhancements

SQL

* Verify Full-Text Search functions not allowed in SELECT [#51568](https://github.com/elastic/elasticsearch/pull/51568) (issue: [#47446](https://github.com/elastic/elasticsearch/issues/47446))

### Upgrades

Infra/Packaging

* Upgrade the bundled JDK to JDK 13.0.2 [#51511](https://github.com/elastic/elasticsearch/pull/51511)