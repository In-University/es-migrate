**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.8

### Known issues

* Slow loggers can cause Log4j loggers to leak over time. When a new index is created, a new Log4j logger is associated with it. However, when an index is deleted, Log4j keeps an internal reference to its loggers that results in a memory leak [#57228](https://github.com/elastic/elasticsearch/pull/57228) (issue: [#56171](https://github.com/elastic/elasticsearch/issues/56171))

This issue is fixed in Elasticsearch 6.8.10 and 7.7.1.

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Bug fixes

Authorization

* Explicitly require that delegate API keys have no privileges [#53647](https://github.com/elastic/elasticsearch/pull/53647)

Distributed

* Avoid loading retention leases while writing them [#42620](https://github.com/elastic/elasticsearch/pull/42620) (issue: [#41430](https://github.com/elastic/elasticsearch/issues/41430))

Infra/Core

* Avoid self-suppression on grouped action listener [#53262](https://github.com/elastic/elasticsearch/pull/53262) (issue: [#53174](https://github.com/elastic/elasticsearch/issues/53174))

Network

* Invoke response handler on failure to send [#53631](https://github.com/elastic/elasticsearch/pull/53631)

SQL

* Fix column size for IP data type [#53056](https://github.com/elastic/elasticsearch/pull/53056) (issue: [#52762](https://github.com/elastic/elasticsearch/issues/52762))

Search

* Fix concurrent requests race over scroll context limit [#53449](https://github.com/elastic/elasticsearch/pull/53449)

* Fix potential NPE in FuzzyTermsEnum [#53231](https://github.com/elastic/elasticsearch/pull/53231) (issue: [#52894](https://github.com/elastic/elasticsearch/issues/52894))

### Upgrades

Features/Ingest

* Ingest Attachment: Upgrade tika to v1.22 [#53418](https://github.com/elastic/elasticsearch/pull/53418)

Infra/Core

* Upgrade the bundled JDK to JDK 14 [#53748](https://github.com/elastic/elasticsearch/pull/53748) (issue: [#53575](https://github.com/elastic/elasticsearch/issues/53575))

* Update jackson-databind to 2.8.11.6 [#53522](https://github.com/elastic/elasticsearch/pull/53522) (issue: [#45225](https://github.com/elastic/elasticsearch/issues/45225))