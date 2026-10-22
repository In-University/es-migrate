**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.16

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Enhancements

Infra/Core

* Update joda dependency to latest 2.10.10 [#72052](https://github.com/elastic/elasticsearch/pull/72052) (issue: [#72028](https://github.com/elastic/elasticsearch/issues/72028))

### Bug fixes

CCR

* Handle failure to get remote client in unfollow [#71928](https://github.com/elastic/elasticsearch/pull/71928) (issue: [#71885](https://github.com/elastic/elasticsearch/issues/71885))

Features/Stats

* Avoid return of negative value in `CounterMetric` [#71446](https://github.com/elastic/elasticsearch/pull/71446) (issues: [#52411](https://github.com/elastic/elasticsearch/issues/52411), [#70968](https://github.com/elastic/elasticsearch/issues/70968))

Network

* Validate IP filter settings [#72195](https://github.com/elastic/elasticsearch/pull/72195) (issue: [#72192](https://github.com/elastic/elasticsearch/issues/72192))

Search

* Fix scroll contexts counter in `SearchService` [#71354](https://github.com/elastic/elasticsearch/pull/71354) (issues: [#53449](https://github.com/elastic/elasticsearch/issues/53449), [#56202](https://github.com/elastic/elasticsearch/issues/56202))