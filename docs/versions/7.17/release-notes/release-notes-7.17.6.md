**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.6

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

Cluster Coordination

* Improve rejection of ambiguous voting config name [#89239](https://github.com/elastic/elasticsearch/pull/89239)

Geo

* Fix potential circuit breaker leak on `InternalGeoGrid` [#88273](https://github.com/elastic/elasticsearch/pull/88273) (issue: [#88261](https://github.com/elastic/elasticsearch/issues/88261))

* Geo_line aggregation returns a geojson point when the resulting line has only one point [#89199](https://github.com/elastic/elasticsearch/pull/89199) (issue: [#85748](https://github.com/elastic/elasticsearch/issues/85748))

* Port fixed version of Lucene Tessellator into ES 7.17 [#88213](https://github.com/elastic/elasticsearch/pull/88213) (issue: [#88014](https://github.com/elastic/elasticsearch/issues/88014))

* Sort ranges in `geo_distance` aggregation [#89154](https://github.com/elastic/elasticsearch/pull/89154) (issue: [#89147](https://github.com/elastic/elasticsearch/issues/89147))

Infra/Node Lifecycle

* Fix message for stalled shutdown [#89254](https://github.com/elastic/elasticsearch/pull/89254)

Infra/Scripting

* Adjust date conversion for execution context in watcher compare condition [#88467](https://github.com/elastic/elasticsearch/pull/88467) (issue: [#88408](https://github.com/elastic/elasticsearch/issues/88408))

Ingest

* Don’t ignore pipeline for upserts in bulk api [#87719](https://github.com/elastic/elasticsearch/pull/87719) (issue: [#87131](https://github.com/elastic/elasticsearch/issues/87131))

Java High Level REST Client

* [7.17] Fix mount snapshot api ignoring unknown request parameter [#89061](https://github.com/elastic/elasticsearch/pull/89061) (issue: [#75982](https://github.com/elastic/elasticsearch/issues/75982))

Machine Learning

* Improve trained model stats API performance [#87978](https://github.com/elastic/elasticsearch/pull/87978)

* Fix potential cause of classification and regression job failures [#2385](https://github.com/elastic/ml-cpp/pull/2385)

Search

* Fix validation of `close_pit` request [#88702](https://github.com/elastic/elasticsearch/pull/88702)

* Override bulk visit methods of exitable point visitor [#82120](https://github.com/elastic/elasticsearch/pull/82120)

* Reduce memory usage in field-caps responses [#88042](https://github.com/elastic/elasticsearch/pull/88042)

Snapshot/Restore

* Avoid capturing `SnapshotsInProgress$Entry` in queue [#88707](https://github.com/elastic/elasticsearch/pull/88707)

* Move Get Snapshots Serialization to Management Pool [#83215](https://github.com/elastic/elasticsearch/pull/83215)

* Report better error for GCS credentials load failure [#89336](https://github.com/elastic/elasticsearch/pull/89336)

Stats

* Discard intermediate results upon cancellation for stats endpoints [#82685](https://github.com/elastic/elasticsearch/pull/82685) (issue: [#82337](https://github.com/elastic/elasticsearch/issues/82337))

Transform

* Execute `_refresh` separately from DBQ, with system permissions [#88005](https://github.com/elastic/elasticsearch/pull/88005) (issue: [#88001](https://github.com/elastic/elasticsearch/issues/88001))

### Deprecations

Infra/Core

* Set monitoring auth.password cluster settings deprecation level as critical [#88351](https://github.com/elastic/elasticsearch/pull/88351) (issue: [#86022](https://github.com/elastic/elasticsearch/issues/86022))

### Enhancements

Authorization

* Avoid loading authorized indices when requested indices are all concrete names [#81237](https://github.com/elastic/elasticsearch/pull/81237)

Machine Learning

* Improve accuracy of anomaly detection median estimation [#2367](https://github.com/elastic/ml-cpp/pull/2367) (issue: [#2364](https://github.com/elastic/ml-cpp/issues/2364))

Packaging

* Change UBI docker user to `elasticsearch` [#88262](https://github.com/elastic/elasticsearch/pull/88262) (issue: [#88218](https://github.com/elastic/elasticsearch/issues/88218))

Performance

* Warn about impact of large readahead on search [#88007](https://github.com/elastic/elasticsearch/pull/88007)

Security

* New setting to close idle connections in OIDC back-channel [#87773](https://github.com/elastic/elasticsearch/pull/87773)

### Upgrades

Packaging

* Upgrade to OpenJDK 18.0.2+9. The JDK update pertains to a potential security vulnerability. Please see our [security statement for more details](https://discuss.elastic.co/c/announcements/security-announcements/31).  [#88675](https://github.com/elastic/elasticsearch/pull/88675) (issue: [#88673](https://github.com/elastic/elasticsearch/issues/88673))