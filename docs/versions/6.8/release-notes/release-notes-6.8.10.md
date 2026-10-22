**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.10

### Bug fixes

Infra/Logging

* SlowLoggers using single logger [#56708](https://github.com/elastic/elasticsearch/pull/56708) (issue: [#56171](https://github.com/elastic/elasticsearch/issues/56171))

Machine Learning

* Fix delete_expired_data/nightly maintenance when many model snapshots need deleting [#57041](https://github.com/elastic/elasticsearch/pull/57041) (issue: [#47103](https://github.com/elastic/elasticsearch/issues/47103))

Search

* Ensure search contexts are removed on index delete [#56335](https://github.com/elastic/elasticsearch/pull/56335)

* Fix validate query listener invocation bug [#56157](https://github.com/elastic/elasticsearch/pull/56157)

### Upgrades

Infra/Packaging

* Upgrade bundled jdk to 14.0.1 [#57233](https://github.com/elastic/elasticsearch/pull/57233)

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).