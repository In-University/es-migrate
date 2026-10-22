**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.11

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Bug fixes

CCR

* Ensure CCR partial reads never overuse buffer [#58620](https://github.com/elastic/elasticsearch/pull/58620)

Infra/Core

* Index name expression resolver bwc layer for date parsing [#58503](https://github.com/elastic/elasticsearch/pull/58503) (issues: [#58481](https://github.com/elastic/elasticsearch/issues/58481), [#58602](https://github.com/elastic/elasticsearch/issues/58602))

* Week based parsing for ingest date processor [#58597](https://github.com/elastic/elasticsearch/pull/58597) (issue: [#58479](https://github.com/elastic/elasticsearch/issues/58479))

Machine Learning

* Better interrupt handling during named pipe connection [#1311](https://github.com/elastic/ml-cpp/pull/1311)

* Trap potential cause of SIGFPE [#1351](https://github.com/elastic/ml-cpp/pull/1351) (issue: [#1348](https://github.com/elastic/ml-cpp/issues/1348))

Mapping

* Fix types deprecation warning for put mapping. [#58764](https://github.com/elastic/elasticsearch/pull/58764) (issues: [#38825](https://github.com/elastic/elasticsearch/issues/38825), [#58675](https://github.com/elastic/elasticsearch/issues/58675))

SQL

* Introduce JDBC option for meta pattern escaping [#40661](https://github.com/elastic/elasticsearch/pull/40661) (issue: [#40640](https://github.com/elastic/elasticsearch/issues/40640))

Search

* Prevent BigInteger serialization errors in term queries [#57987](https://github.com/elastic/elasticsearch/pull/57987) (issue: [#57917](https://github.com/elastic/elasticsearch/issues/57917))

Task Management

* Remove ban tasks with the current thread context [#55404](https://github.com/elastic/elasticsearch/pull/55404)

### Upgrades

Infra/Core

* Upgrade to JNA 5.5.0 [#58183](https://github.com/elastic/elasticsearch/pull/58183)