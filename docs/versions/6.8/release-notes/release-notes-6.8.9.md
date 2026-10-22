**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.9

### Known issues

* Slow loggers can cause Log4j loggers to leak over time. When a new index is created, a new Log4j logger is associated with it. However, when an index is deleted, Log4j keeps an internal reference to its loggers that results in a memory leak [#57228](https://github.com/elastic/elasticsearch/pull/57228) (issue: [#56171](https://github.com/elastic/elasticsearch/issues/56171))

This issue is fixed in Elasticsearch 6.8.10 and 7.7.1.

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

* Java based - formats with *8* prefix - week based parsing and calculations are using JDK default calendar data provider which is Sunday,1.
Sunday is considered first day of a week and it requires only 1 day in a week to for the first week of the year.
It can be worked around by using locale which is based on ISO8601 rule (Monday,4) - for instance en-GB
This issue is fixed in Elasticsearch 7.7 [https://github.com/elastic/elasticsearch/pull/48209](https://github.com/elastic/elasticsearch/pull/48209)

### Enhancements

Authorization

* Remove synthetic role names of API keys as they confuse users [#56005](https://github.com/elastic/elasticsearch/pull/56005)

Infra/Core

* Enable helpful null pointer exceptions [#54853](https://github.com/elastic/elasticsearch/pull/54853)

Snapshot/Restore

* Update the HDFS version used by HDFS Repo [#53693](https://github.com/elastic/elasticsearch/pull/53693)

### Bug fixes

CCR

* Retry follow task when remote connection queue full [#55314](https://github.com/elastic/elasticsearch/pull/55314)

* Clear recent errors when auto-follow successfully [#54997](https://github.com/elastic/elasticsearch/pull/54997)

* Handle no such remote cluster exception in ccr [#53415](https://github.com/elastic/elasticsearch/pull/53415) (issue: [#53225](https://github.com/elastic/elasticsearch/issues/53225))

CRUD

* Reduce deprecation warnings from bulk OCC [#53911](https://github.com/elastic/elasticsearch/pull/53911)

Engine

* Ensure no circular reference in translog tragic exception [#55959](https://github.com/elastic/elasticsearch/pull/55959) (issue: [#55893](https://github.com/elastic/elasticsearch/issues/55893))

Features/CAT APIs

* Cat tasks output should respect time display settings [#54536](https://github.com/elastic/elasticsearch/pull/54536)

Infra/Core

* Avoid StackOverflowError if write circular reference exception [#54147](https://github.com/elastic/elasticsearch/pull/54147) (issue: [#53589](https://github.com/elastic/elasticsearch/issues/53589))

* Disallow negative TimeValues [#53913](https://github.com/elastic/elasticsearch/pull/53913) (issue: [#54041](https://github.com/elastic/elasticsearch/issues/54041))

Network

* Fix use of password protected PKCS#8 keys for SSL [#55457](https://github.com/elastic/elasticsearch/pull/55457) (issue: [#8](https://github.com/elastic/elasticsearch/issues/8))

* Add support for more named curves [#55179](https://github.com/elastic/elasticsearch/pull/55179) (issue: [#55031](https://github.com/elastic/elasticsearch/issues/55031))

Reindex

* Reindex negative TimeValue fix [#54057](https://github.com/elastic/elasticsearch/pull/54057) (issue: [#53913](https://github.com/elastic/elasticsearch/issues/53913))

### Upgrades

Engine

* Upgrade to Lucene 7.7.3 [#55897](https://github.com/elastic/elasticsearch/pull/55897)