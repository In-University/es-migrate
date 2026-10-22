**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.17.6

Also see [Breaking changes in 8.17](migrating-8.17.html#breaking-changes-8.17).

### Bug fixes

CCS

* Cancel expired async search task when a remote returns its results [#126583](https://github.com/elastic/elasticsearch/pull/126583)

Data streams

* [otel-data] Bump plugin version to release _metric_names_hash changes [#126850](https://github.com/elastic/elasticsearch/pull/126850)

ES|QL

* Fix count optimization with pushable union types [#127225](https://github.com/elastic/elasticsearch/pull/127225) (issue: [#127200](https://github.com/elastic/elasticsearch/issues/127200))

Infra/Core

* Rework uniquify to not use iterators [#126889](https://github.com/elastic/elasticsearch/pull/126889) (issue: [#126883](https://github.com/elastic/elasticsearch/issues/126883))

* Workaround max name limit imposed by Jackson 2.17 [#126806](https://github.com/elastic/elasticsearch/pull/126806)

Machine Learning

* Adding missing `onFailure` call for Inference API start model request [#126930](https://github.com/elastic/elasticsearch/pull/126930)

* Fix text structure NPE when fields in list have null value [#125922](https://github.com/elastic/elasticsearch/pull/125922)

* Leverage threadpool schedule for inference api to avoid long running thread [#126858](https://github.com/elastic/elasticsearch/pull/126858) (issue: [#126853](https://github.com/elastic/elasticsearch/issues/126853))

Ranking

* Fix LTR rescorer with model alias [#126273](https://github.com/elastic/elasticsearch/pull/126273)

Task Management

* Fix race condition in `RestCancellableNodeClient` [#126686](https://github.com/elastic/elasticsearch/pull/126686) (issue: [#88201](https://github.com/elastic/elasticsearch/issues/88201))

Vector Search

* Fix `vec_caps` to test for OS support too (on x64) [#126911](https://github.com/elastic/elasticsearch/pull/126911) (issue: [#126809](https://github.com/elastic/elasticsearch/issues/126809))

### Enhancements

Security

* Add Issuer to failed SAML Signature validation logs when available [#126310](https://github.com/elastic/elasticsearch/pull/126310) (issue: [#111022](https://github.com/elastic/elasticsearch/issues/111022))