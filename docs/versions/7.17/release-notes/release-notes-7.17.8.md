**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.8

Also see [Breaking changes in 7.17](migrating-7.17.html#breaking-changes-7.17).

### Known issues

* Parsing a request when the last element in an array is filtered out
(for instance using `_source_includes`) fails. This
is due to [a bug in Jackson parser](https://github.com/FasterXML/jackson-core/issues/882).
Fixed in Elasticsearch 8.6.1 ([#91456](https://github.com/elastic/elasticsearch/pull/92480))

* The deprecated `index.mapper.dynamic` setting can break your cluster. It can only
be set using the **Update index settings API**. Symptoms include nodes failing to start
or shards failing to allocate. Do not use this setting in versions prior to 7.17.22.
The bug is fixed in 7.17.22.
(issue: [#109160](https://github.com/elastic/elasticsearch/issues/109160))

### Bug fixes

EQL

* Fix serialization of `resultPosition` in `EqlSearchRequest` [#91497](https://github.com/elastic/elasticsearch/pull/91497)

* Limit CCS to v 7.15 [#91834](https://github.com/elastic/elasticsearch/pull/91834) (issue: [#91762](https://github.com/elastic/elasticsearch/issues/91762))

Infra/Core

* Add `trace.id` to request trace logs [#91772](https://github.com/elastic/elasticsearch/pull/91772) (issue: [#88174](https://github.com/elastic/elasticsearch/issues/88174))

* `DoPrivileged` in `ElasticsearchEncaughtExceptionHandler` and check modify thread [#91704](https://github.com/elastic/elasticsearch/pull/91704) (issue: [#91650](https://github.com/elastic/elasticsearch/issues/91650))

Ingest Node

* Set the enrich maintenance cluster lifecycle listener only once [#90486](https://github.com/elastic/elasticsearch/pull/90486)

Machine Learning

* ML stats failures should not stop the usage API working [#91917](https://github.com/elastic/elasticsearch/pull/91917) (issue: [#91893](https://github.com/elastic/elasticsearch/issues/91893))

Search

* Fix integer overflow in `AsyncTaskIndexService` [#91044](https://github.com/elastic/elasticsearch/pull/91044)

Transform

* Make transform `_preview` request cancellable [#91313](https://github.com/elastic/elasticsearch/pull/91313) (issue: [#91286](https://github.com/elastic/elasticsearch/issues/91286))

### Enhancements

Infra/Core

* Check for unassigned shards on node shutdown [#91297](https://github.com/elastic/elasticsearch/pull/91297) (issue: [#88635](https://github.com/elastic/elasticsearch/issues/88635))

* Extend systemd startup timeout to 900s [#91338](https://github.com/elastic/elasticsearch/pull/91338)

Snapshot/Restore

* Update HDFS Repository to HDFS 3.3.3 [#88039](https://github.com/elastic/elasticsearch/pull/88039)

TLS

* Support SAN/dnsName for restricted trust [#91946](https://github.com/elastic/elasticsearch/pull/91946)

### Upgrades

Packaging

* Update bundled JDK to Java 19.0.1 [#91025](https://github.com/elastic/elasticsearch/pull/91025) (issue: [#91010](https://github.com/elastic/elasticsearch/issues/91010))