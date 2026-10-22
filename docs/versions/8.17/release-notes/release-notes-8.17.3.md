**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.17.3

Also see [Breaking changes in 8.17](migrating-8.17.html#breaking-changes-8.17).

### Bug fixes

Aggregations

* Disable concurrency when `top_hits` sorts on anything but `_score` [#123610](https://github.com/elastic/elasticsearch/pull/123610)

Allocation

* Deduplicate allocation stats calls [#123246](https://github.com/elastic/elasticsearch/pull/123246)

Authentication

* Improve jwt logging on failed auth [#122247](https://github.com/elastic/elasticsearch/pull/122247)

CRUD

* Reduce license checks in `LicensedWriteLoadForecaster` [#123346](https://github.com/elastic/elasticsearch/pull/123346) (issue: [#123247](https://github.com/elastic/elasticsearch/issues/123247))

Data streams

* Add `_metric_names_hash` field to OTel metric mappings [#120952](https://github.com/elastic/elasticsearch/pull/120952)

EQL

* Fix JOIN command validation (not supported) [#122011](https://github.com/elastic/elasticsearch/pull/122011)

ES|QL

* Fix ENRICH validation for use of wildcards [#121911](https://github.com/elastic/elasticsearch/pull/121911)

* Fix listener leak in exchange service [#122417](https://github.com/elastic/elasticsearch/pull/122417) (issue: [#122271](https://github.com/elastic/elasticsearch/issues/122271))

* Speed up VALUES for many buckets [#123073](https://github.com/elastic/elasticsearch/pull/123073)

Infra/Node Lifecycle

* Block running ES 8.17 with JDK 24+ [#122517](https://github.com/elastic/elasticsearch/pull/122517)

Ingest

* Fix `ArrayIndexOutOfBoundsException` in `ShardBulkInferenceActionFilter` [#122538](https://github.com/elastic/elasticsearch/pull/122538)

Ingest Node

* Canonicalize processor names and types in `IngestStats` [#122610](https://github.com/elastic/elasticsearch/pull/122610)

* Deduplicate `IngestStats` and `IngestStats.Stats` identity records when deserializing [#122496](https://github.com/elastic/elasticsearch/pull/122496)

* Fix redact processor arraycopy bug [#122640](https://github.com/elastic/elasticsearch/pull/122640)

* Register `IngestGeoIpMetadata` as a NamedXContent [#123079](https://github.com/elastic/elasticsearch/pull/123079)

* Use ordered maps for `PipelineConfiguration` xcontent deserialization [#123403](https://github.com/elastic/elasticsearch/pull/123403)

Logs

* Fix issues that prevents using search only snapshots for indices that use index sorting. This is includes Logsdb and time series indices. [#122199](https://github.com/elastic/elasticsearch/pull/122199)

* Use min node version to guard injecting settings in logs provider [#123005](https://github.com/elastic/elasticsearch/pull/123005) (issue: [#122950](https://github.com/elastic/elasticsearch/issues/122950))

Mapping

* Fix synthetic source bug that would mishandle nested `dense_vector` fields [#122425](https://github.com/elastic/elasticsearch/pull/122425)

* fix stale data in synthetic source for string stored field [#123105](https://github.com/elastic/elasticsearch/pull/123105) (issue: [#123110](https://github.com/elastic/elasticsearch/issues/123110))

Stats

* Fixing serialization of `ScriptStats` `cache_evictions_history` [#123384](https://github.com/elastic/elasticsearch/pull/123384)

### Upgrades

Authentication

* Bump json-smart and oauth2-oidc-sdk [#122737](https://github.com/elastic/elasticsearch/pull/122737)

### Known issues

ES|QL

* Some valid queries using an `ENRICH` command can fail when a match field is used that is absent from some indices or shards, either with a 500 status code due to `NullPointerException` or `ClassCastException` or with a 400 status code and `IllegalArgumentException`. This is fixed in [#126187](https://github.com/elastic/elasticsearch/pull/126187).