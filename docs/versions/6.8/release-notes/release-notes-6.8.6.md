**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.6

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Known issues

* Slow loggers can cause Log4j loggers to leak over time. When a new index is created, a new Log4j logger is associated with it. However, when an index is deleted, Log4j keeps an internal reference to its loggers that results in a memory leak [#57228](https://github.com/elastic/elasticsearch/pull/57228) (issue: [#56171](https://github.com/elastic/elasticsearch/issues/56171))

This issue is fixed in Elasticsearch 6.8.10 and 7.7.1.

### Enhancements

Features/Watcher

* Log attachment generation failures [#50080](https://github.com/elastic/elasticsearch/pull/50080)

Infra/Packaging

* Restrict support for CMS to pre-JDK 14 [#49123](https://github.com/elastic/elasticsearch/pull/49123) (issue: [#46973](https://github.com/elastic/elasticsearch/issues/46973))

### Bug fixes

Aggregations

* Avoid precision loss in DocValueFormat.RAW#parseLong [#49063](https://github.com/elastic/elasticsearch/pull/49063) (issue: [#38692](https://github.com/elastic/elasticsearch/issues/38692))

Audit

* Audit log filter and marker [#45456](https://github.com/elastic/elasticsearch/pull/45456) (issue: [#47251](https://github.com/elastic/elasticsearch/issues/47251))

Authentication

* Fix iterate-from-1 bug in smart realm order [#49473](https://github.com/elastic/elasticsearch/pull/49473)

CCR

* CCR should auto-retry rejected execution exceptions [#49213](https://github.com/elastic/elasticsearch/pull/49213)

Features/Java High Level REST Client

* Support es7 node http publish_address format [#49279](https://github.com/elastic/elasticsearch/pull/49279) (issue: [#48950](https://github.com/elastic/elasticsearch/issues/48950))

Machine Learning

* Fixes for stop datafeed edge cases [#49191](https://github.com/elastic/elasticsearch/pull/49191) (issues: [#43670](https://github.com/elastic/elasticsearch/issues/43670), [#48931](https://github.com/elastic/elasticsearch/issues/48931))

Recovery

* Ignore Lucene index in peer recovery if translog corrupted [#49114](https://github.com/elastic/elasticsearch/pull/49114)

Reindex

* Fix delete- and update-by-query on indices without sequence numbers [#50077](https://github.com/elastic/elasticsearch/pull/50077)