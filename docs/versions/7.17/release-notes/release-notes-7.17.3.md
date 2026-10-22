**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.3

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

Authorization

* Grant `kibana_system` role read access to APM data streams [#85744](https://github.com/elastic/elasticsearch/pull/85744)

Geo

* Fix fields wildcard support to vector tile search API [#85595](https://github.com/elastic/elasticsearch/pull/85595) (issue: [#85592](https://github.com/elastic/elasticsearch/issues/85592))

Highlighting

* Fix wildcard highlighting on `match_only_text` [#85500](https://github.com/elastic/elasticsearch/pull/85500) (issue: [#85493](https://github.com/elastic/elasticsearch/issues/85493))

Infra/Core

* Prevent `ThreadContext` header leak when sending response [#68649](https://github.com/elastic/elasticsearch/pull/68649) (issue: [#68278](https://github.com/elastic/elasticsearch/issues/68278))

Machine Learning

* Allow retrieving `boolean` fields from `_source` in data frame analytics jobs [#85672](https://github.com/elastic/elasticsearch/pull/85672)

* Avoid multiple queued quantiles documents in renormalizer [#85555](https://github.com/elastic/elasticsearch/pull/85555) (issue: [#85539](https://github.com/elastic/elasticsearch/issues/85539))

Search

* Fix skip caching factor with `indices.queries.cache.all_segments` [#85510](https://github.com/elastic/elasticsearch/pull/85510)

### Upgrades

Ingest

* Bump commons-compress to 1.21 [#85581](https://github.com/elastic/elasticsearch/pull/85581)

Packaging

* Upgrade to JDK 18.0.0+36 [#85376](https://github.com/elastic/elasticsearch/pull/85376) (issue: [#85357](https://github.com/elastic/elasticsearch/issues/85357))