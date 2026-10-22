**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.9

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

Authentication

* Improve performance for role mapping with DNs [#92074](https://github.com/elastic/elasticsearch/pull/92074)

Cluster Coordination

* Unsafe bootstrap memory optimization [#92493](https://github.com/elastic/elasticsearch/pull/92493)

Distributed

* Fork `TransportClusterStateAction` to MANAGEMENT [#90996](https://github.com/elastic/elasticsearch/pull/90996)

Geo

* Port lucene fix github-11986 to Elasticsearch 7.17 [#92320](https://github.com/elastic/elasticsearch/pull/92320)

ILM+SLM

* Get repository metadata from the cluster state doesn’t throw an exception if a repo is missing [#92914](https://github.com/elastic/elasticsearch/pull/92914)

Infra/Core

* Remove unnecessary `thirdPartyAudit` exclusions [#92352](https://github.com/elastic/elasticsearch/pull/92352) (issue: [#92346](https://github.com/elastic/elasticsearch/issues/92346))

Machine Learning

* Improve performance of closing files before spawning [#2424](https://github.com/elastic/ml-cpp/pull/2424).

Mapping

* Fix `_bulk` api `dynamic_templates` and explicit `op_type` [#92687](https://github.com/elastic/elasticsearch/pull/92687)

Network

* Reject connection attempts while closing [#92465](https://github.com/elastic/elasticsearch/pull/92465)

Search

* Avoid doing I/O when fetching min and max for keyword fields [#92026](https://github.com/elastic/elasticsearch/pull/92026)

Snapshot/Restore

* Fix quadratic complexity in `SnapshotStatus` serialization [#90795](https://github.com/elastic/elasticsearch/pull/90795)

* Simplify and optimize deduplication of `RepositoryData` for a non-caching repository instance [#91851](https://github.com/elastic/elasticsearch/pull/91851) (issue: [#89952](https://github.com/elastic/elasticsearch/issues/89952))

Store

* Fix numOpenOutputs and modCount in ByteSizeCachingDirectory [#92440](https://github.com/elastic/elasticsearch/pull/92440) (issue: [#92434](https://github.com/elastic/elasticsearch/issues/92434))

### Enhancements

Search

* Make field-caps tasks cancellable [#92051](https://github.com/elastic/elasticsearch/pull/92051)

### Upgrades

Snapshot/Restore

* Upgrade GCS SDK to 2.13.1 [#92327](https://github.com/elastic/elasticsearch/pull/92327)