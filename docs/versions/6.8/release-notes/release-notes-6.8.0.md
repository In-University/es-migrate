**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.0

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Enhancements

Security

* Moved some security features to basic. See [6.8.0 Release highlights](release-highlights-6.8.0.html)

Authentication

* Log warning when unlicensed realms are skipped [#41778](https://github.com/elastic/elasticsearch/pull/41778)

Infra/Settings

* Drop distinction in entries for keystore [#41701](https://github.com/elastic/elasticsearch/pull/41701)

### Bug fixes

Features/Watcher

* Fix Watcher deadlock that can cause in-abilty to index documents. [#41418](https://github.com/elastic/elasticsearch/pull/41418) (issue: [#41390](https://github.com/elastic/elasticsearch/issues/41390))

Network

* Enforce transport TLS on Basic with Security [#42150](https://github.com/elastic/elasticsearch/pull/42150)

Reindex

* Allow reindexing into write alias [#41677](https://github.com/elastic/elasticsearch/pull/41677) (issue: [#41667](https://github.com/elastic/elasticsearch/issues/41667))

SQL

* SQL: Fix issue regarding INTERVAL * number [#42014](https://github.com/elastic/elasticsearch/pull/42014) (issue: [#41239](https://github.com/elastic/elasticsearch/issues/41239))

* SQL: Remove CircuitBreaker from parser [#41835](https://github.com/elastic/elasticsearch/pull/41835) (issue: [#41471](https://github.com/elastic/elasticsearch/issues/41471))

Security

* Remove dynamic objects from security index [#40499](https://github.com/elastic/elasticsearch/pull/40499) (issue: [#35460](https://github.com/elastic/elasticsearch/issues/35460))

* Add granular API key privileges [#41488](https://github.com/elastic/elasticsearch/pull/41488) (issue: [#40031](https://github.com/elastic/elasticsearch/issues/40031))