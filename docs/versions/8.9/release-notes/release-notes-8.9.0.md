**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.9.0

Also see [Breaking changes in 8.9](migrating-8.9.html#breaking-changes-8.9).

### Known issues

* Question Answering fails on long input text. If the context supplied to the
task is longer than the model’s max_sequence_length and truncate is set to none
then inference fails with the message `question answering result has
invalid dimension`. (issue: [#97917](https://github.com/elastic/elasticsearch/issues/97917))

* High Memory Pressure due to a GC JVM setting change

This version of Elasticsearch is bundled with JDK 20. In JDK 20
[Preventive GC is disabled by default](https://bugs.openjdk.org/browse/JDK-8293861).
This may lead to increased memory pressure and an increased number of CircuitBreakerExceptions when retrieving large
documents under some load patterns. (issue: [#99592](https://github.com/elastic/elasticsearch/issues/99592))

If this change affects your use of Elasticsearch, consider re-enabling the previous behaviour
by adding the JVM arguments `-XX:+UnlockDiagnosticVMOptions -XX:+G1UsePreventiveGC` (reference:
[JDK 20 release notes](https://www.oracle.com/java/technologies/javase/20-relnote-issues.html#JDK-8293861)). It is
important to note that this workaround is temporary and works only with JDK 20, which is bundled with Elasticsearch up
to version 8.10.2 inclusive. Successive versions are bundling JDK 21+, where this setting
[has been removed](https://bugs.openjdk.org/browse/JDK-8297639). Specifying those JVM arguments will prevent the
JVM (and therefore Elasticsearch Nodes) from starting.

### Breaking changes

Aggregations

* Switch TDigestState to use `HybridDigest` by default [#96904](https://github.com/elastic/elasticsearch/pull/96904)

### Bug fixes

Allocation

* Attempt to fix delay allocation [#95921](https://github.com/elastic/elasticsearch/pull/95921)

* Fix NPE in Desired Balance API [#97775](https://github.com/elastic/elasticsearch/pull/97775)

* Fix autoexpand during node replace [#96281](https://github.com/elastic/elasticsearch/pull/96281)

Authorization

* Resolving wildcard application names without prefix query [#96479](https://github.com/elastic/elasticsearch/pull/96479) (issue: [#96465](https://github.com/elastic/elasticsearch/issues/96465))

CRUD

* Fix `retry_on_conflict` parameter in update API to not retry indefinitely [#96262](https://github.com/elastic/elasticsearch/pull/96262)

* Handle failure in `TransportUpdateAction#handleUpdateFailureWithRetry` [#97290](https://github.com/elastic/elasticsearch/pull/97290) (issue: [#97286](https://github.com/elastic/elasticsearch/issues/97286))

Cluster Coordination

* Avoid `getStateForMasterService` where possible [#97304](https://github.com/elastic/elasticsearch/pull/97304)

* Become candidate on publication failure [#96490](https://github.com/elastic/elasticsearch/pull/96490) (issue: [#96273](https://github.com/elastic/elasticsearch/issues/96273))

* Fix cluster settings update task acknowledgment [#97111](https://github.com/elastic/elasticsearch/pull/97111)

Data streams

* Accept timestamp as object at root level [#97401](https://github.com/elastic/elasticsearch/pull/97401)

Geo

* Fix bug when creating empty `geo_lines` [#97509](https://github.com/elastic/elasticsearch/pull/97509) (issue: [#97311](https://github.com/elastic/elasticsearch/issues/97311))

* Fix time-series geo_line to include reduce phase in MergedGeoLines [#96953](https://github.com/elastic/elasticsearch/pull/96953) (issue: [#96983](https://github.com/elastic/elasticsearch/issues/96983))

* Support for Byte and Short as vector tiles features [#97619](https://github.com/elastic/elasticsearch/pull/97619) (issue: [#97612](https://github.com/elastic/elasticsearch/issues/97612))

ILM+SLM

* Limit the details field length we store for each SLM invocation [#97038](https://github.com/elastic/elasticsearch/pull/97038) (issue: [#96918](https://github.com/elastic/elasticsearch/issues/96918))

Infra/CLI

* Initialise ES logging in CLI [#97353](https://github.com/elastic/elasticsearch/pull/97353) (issue: [#97350](https://github.com/elastic/elasticsearch/issues/97350))

Infra/Core

* Capture max processors in static init [#97119](https://github.com/elastic/elasticsearch/pull/97119) (issue: [#97088](https://github.com/elastic/elasticsearch/issues/97088))

* Interpret microseconds cpu stats from cgroups2 properly as nanos [#96924](https://github.com/elastic/elasticsearch/pull/96924) (issue: [#96089](https://github.com/elastic/elasticsearch/issues/96089))

Infra/Logging

* Add slf4j-nop in order to prevent startup warnings [#95459](https://github.com/elastic/elasticsearch/pull/95459)

Infra/REST API

* Fix tchar pattern in `RestRequest` [#96406](https://github.com/elastic/elasticsearch/pull/96406)

Infra/Scripting

* Fix Painless method lookup over unknown super interfaces [#97062](https://github.com/elastic/elasticsearch/pull/97062) (issue: [#97022](https://github.com/elastic/elasticsearch/issues/97022))

Infra/Settings

* Enable validation for `versionSettings` [#95874](https://github.com/elastic/elasticsearch/pull/95874) (issue: [#95873](https://github.com/elastic/elasticsearch/issues/95873))

Ingest Node

* Fixing `DateProcessor` when the format is `epoch_millis` [#95996](https://github.com/elastic/elasticsearch/pull/95996)

* Fixing `GeoIpDownloaderStatsAction$NodeResponse` serialization by defensively copying inputs [#96777](https://github.com/elastic/elasticsearch/pull/96777) (issue: [#96438](https://github.com/elastic/elasticsearch/issues/96438))

* Trim field references in reroute processor [#96941](https://github.com/elastic/elasticsearch/pull/96941) (issue: [#96939](https://github.com/elastic/elasticsearch/issues/96939))

Machine Learning

* Catch exceptions thrown during inference and report as errors [#2542](https://github.com/elastic/ml-cpp/pull/2542)

* Fix `WordPiece` tokenization where stripping accents results in an empty string [#97354](https://github.com/elastic/elasticsearch/pull/97354)

* Improve model downloader robustness [#97274](https://github.com/elastic/elasticsearch/pull/97274)

* Prevent high memory usage by evaluating batch inference singularly [#2538](https://github.com/elastic/ml-cpp/pull/2538)

Mapping

* Avoid stack overflow while parsing mapping [#95705](https://github.com/elastic/elasticsearch/pull/95705) (issue: [#52098](https://github.com/elastic/elasticsearch/issues/52098))

* Fix mapping parsing logic to determine synthetic source is active [#97355](https://github.com/elastic/elasticsearch/pull/97355) (issue: [#97320](https://github.com/elastic/elasticsearch/issues/97320))

Ranking

* Fix `sub_searches` serialization bug [#97587](https://github.com/elastic/elasticsearch/pull/97587)

Recovery

* Promptly fail recovery from snapshot [#96421](https://github.com/elastic/elasticsearch/pull/96421) (issue: [#95525](https://github.com/elastic/elasticsearch/issues/95525))

Search

* Prevent instantiation of `top_metrics` when sub-aggregations are present [#96180](https://github.com/elastic/elasticsearch/pull/96180) (issue: [#95663](https://github.com/elastic/elasticsearch/issues/95663))

* Set new providers before building `FetchSubPhaseProcessors` [#97460](https://github.com/elastic/elasticsearch/pull/97460) (issue: [#96284](https://github.com/elastic/elasticsearch/issues/96284))

Snapshot/Restore

* Fix blob cache races/assertion errors [#96458](https://github.com/elastic/elasticsearch/pull/96458)

* Fix reused/recovered bytes for files that are only partially recovered from cache [#95987](https://github.com/elastic/elasticsearch/pull/95987) (issues: [#95970](https://github.com/elastic/elasticsearch/issues/95970), [#95994](https://github.com/elastic/elasticsearch/issues/95994))

* Fix reused/recovered bytes for files that are recovered from cache [#97278](https://github.com/elastic/elasticsearch/pull/97278) (issue: [#95994](https://github.com/elastic/elasticsearch/issues/95994))

* Refactor `RestoreClusterStateListener` to use `ClusterStateObserver` [#96662](https://github.com/elastic/elasticsearch/pull/96662) (issue: [#96425](https://github.com/elastic/elasticsearch/issues/96425))

TSDB

* Error message for misconfigured TSDB index [#96956](https://github.com/elastic/elasticsearch/pull/96956) (issue: [#96445](https://github.com/elastic/elasticsearch/issues/96445))

* Min score for time series [#96878](https://github.com/elastic/elasticsearch/pull/96878)

Task Management

* Improve cancellability in `TransportTasksAction` [#96279](https://github.com/elastic/elasticsearch/pull/96279)

Transform

* Improve reporting status of the transform that is about to finish [#95672](https://github.com/elastic/elasticsearch/pull/95672)

### Enhancements

Aggregations

* Add cluster setting to `SearchExecutionContext` to configure `TDigestExecutionHint` [#96943](https://github.com/elastic/elasticsearch/pull/96943)

* Add support for dynamic pruning to cardinality aggregations on low-cardinality keyword fields [#92060](https://github.com/elastic/elasticsearch/pull/92060)

* Make TDigestState configurable [#96794](https://github.com/elastic/elasticsearch/pull/96794)

* Skip `SortingDigest` when merging a large digest in `HybridDigest` [#97099](https://github.com/elastic/elasticsearch/pull/97099)

* Support value retrieval in `top_hits` [#95828](https://github.com/elastic/elasticsearch/pull/95828)

Allocation

* Take into account `expectedShardSize` when initializing shard in simulation [#95734](https://github.com/elastic/elasticsearch/pull/95734)

Analysis

* Create `.synonyms` system index [#95548](https://github.com/elastic/elasticsearch/pull/95548)

Application

* Add template parameters to Search Applications [#95674](https://github.com/elastic/elasticsearch/pull/95674)

* Chunk profiling stacktrace response [#96340](https://github.com/elastic/elasticsearch/pull/96340)

* [Profiling] Add status API [#96272](https://github.com/elastic/elasticsearch/pull/96272)

* [Profiling] Allow to upgrade managed ILM policy [#96550](https://github.com/elastic/elasticsearch/pull/96550)

* [Profiling] Introduce ILM for K/V indices [#96268](https://github.com/elastic/elasticsearch/pull/96268)

* [Profiling] Require POST to retrieve stacktraces [#96790](https://github.com/elastic/elasticsearch/pull/96790)

* [Profiling] Tweak default ILM policy [#96516](https://github.com/elastic/elasticsearch/pull/96516)

* [Search Applications] Support arrays in stored mustache templates [#96197](https://github.com/elastic/elasticsearch/pull/96197)

Authentication

* Header validator with Security [#95112](https://github.com/elastic/elasticsearch/pull/95112)

Authorization

* Add Search ALC filter index prefix to the enterprise search user [#96885](https://github.com/elastic/elasticsearch/pull/96885)

* Ensure checking application privileges work with nested-limited roles [#96970](https://github.com/elastic/elasticsearch/pull/96970)

Autoscaling

* Add shard explain info to `ReactiveReason` about unassigned shards [#88590](https://github.com/elastic/elasticsearch/pull/88590) (issue: [#85243](https://github.com/elastic/elasticsearch/issues/85243))

DLM

* Add auto force merge functionality to DLM [#95204](https://github.com/elastic/elasticsearch/pull/95204)

* Adding `data_lifecycle` to the _xpack/usage API [#96177](https://github.com/elastic/elasticsearch/pull/96177)

* Adding `manage_data_stream_lifecycle` index privilege and expanding `view_index_metadata` for access to data stream lifecycle APIs [#95512](https://github.com/elastic/elasticsearch/pull/95512)

* Allow for the data lifecycle and the retention to be explicitly nullified [#95979](https://github.com/elastic/elasticsearch/pull/95979)

Data streams

* Add support for `logs@custom` component template for `logs-**-** data streams [#95481](https://github.com/elastic/elasticsearch/pull/95481) (issue: [#95469](https://github.com/elastic/elasticsearch/issues/95469))

* Adding ECS dynamic mappings component and applying it to logs data streams by default [#96171](https://github.com/elastic/elasticsearch/pull/96171) (issue: [#95538](https://github.com/elastic/elasticsearch/issues/95538))

* Adjust ECS dynamic templates to support `subobjects: false` [#96712](https://github.com/elastic/elasticsearch/pull/96712)

* Automatically parse log events in logs data streams, if their `message` field contains JSON content [#96083](https://github.com/elastic/elasticsearch/pull/96083) (issue: [#95522](https://github.com/elastic/elasticsearch/issues/95522))

* Change default of `ignore_malformed` to `true` in `logs-*-*` data streams [#95329](https://github.com/elastic/elasticsearch/pull/95329) (issue: [#95224](https://github.com/elastic/elasticsearch/issues/95224))

* Set `@timestamp` for documents in logs data streams if missing and add support for custom pipeline [#95971](https://github.com/elastic/elasticsearch/pull/95971) (issues: [#95537](https://github.com/elastic/elasticsearch/issues/95537), [#95551](https://github.com/elastic/elasticsearch/issues/95551))

* Update data streams implicit timestamp `ignore_malformed` settings [#96051](https://github.com/elastic/elasticsearch/pull/96051)

Engine

* Cache modification time of translog writer file [#95107](https://github.com/elastic/elasticsearch/pull/95107)

* Trigger refresh when shard becomes search active [#96321](https://github.com/elastic/elasticsearch/pull/96321) (issue: [#95544](https://github.com/elastic/elasticsearch/issues/95544))

Geo

* Add brute force approach to `GeoHashGridTiler` [#96863](https://github.com/elastic/elasticsearch/pull/96863)

* Asset tracking - geo_line in time-series aggregations [#94954](https://github.com/elastic/elasticsearch/pull/94954)

ILM+SLM

* Chunk the GET _ilm/policy response [#97251](https://github.com/elastic/elasticsearch/pull/97251) (issue: [#96569](https://github.com/elastic/elasticsearch/issues/96569))

* Move get lifecycle API to Management thread pool and make cancellable [#97248](https://github.com/elastic/elasticsearch/pull/97248) (issue: [#96568](https://github.com/elastic/elasticsearch/issues/96568))

* Reduce WaitForNoFollowersStep requests indices shard stats [#94510](https://github.com/elastic/elasticsearch/pull/94510)

Indices APIs

* Bootstrap profiling indices at startup [#95666](https://github.com/elastic/elasticsearch/pull/95666)

Infra/Node Lifecycle

* SIGTERM node shutdown type [#95430](https://github.com/elastic/elasticsearch/pull/95430)

Ingest Node

* Add mappings for enrich fields [#96056](https://github.com/elastic/elasticsearch/pull/96056)

* Ingest: expose reroute inquiry/reset via Elastic-internal API bridge [#96958](https://github.com/elastic/elasticsearch/pull/96958)

Machine Learning

* Improved compliance with memory limitations [#2469](https://github.com/elastic/ml-cpp/pull/2469)

* Improve detection of calendar cyclic components with long bucket lengths [#2493](https://github.com/elastic/ml-cpp/pull/2493)

* Improve detection of time shifts, for example for daylight saving [#2479](https://github.com/elastic/ml-cpp/pull/2479)

Mapping

* Allow unsigned long field to use decay functions [#96394](https://github.com/elastic/elasticsearch/pull/96394) (issue: [#89603](https://github.com/elastic/elasticsearch/issues/89603))

Ranking

* Add multiple queries for ranking to the search endpoint [#96224](https://github.com/elastic/elasticsearch/pull/96224)

Recovery

* Implement `StartRecoveryRequest#getDescription` [#95731](https://github.com/elastic/elasticsearch/pull/95731)

Search

* Add search shards endpoint [#94534](https://github.com/elastic/elasticsearch/pull/94534)

* Don’t generate stacktrace in `EarlyTerminationException` and `TimeExceededException` [#95910](https://github.com/elastic/elasticsearch/pull/95910)

* Feature/speed up binary vector decoding [#96716](https://github.com/elastic/elasticsearch/pull/96716)

* Improve brute force vector search speed by using Lucene functions [#96617](https://github.com/elastic/elasticsearch/pull/96617)

* Include search idle info to shard stats [#95740](https://github.com/elastic/elasticsearch/pull/95740) (issue: [#95727](https://github.com/elastic/elasticsearch/issues/95727))

* Integrate CCS with new `search_shards` API [#95894](https://github.com/elastic/elasticsearch/pull/95894) (issue: [#93730](https://github.com/elastic/elasticsearch/issues/93730))

* Introduce a filtered collector manager [#96824](https://github.com/elastic/elasticsearch/pull/96824)

* Introduce minimum score collector manager [#96834](https://github.com/elastic/elasticsearch/pull/96834)

* Skip shards when querying constant keyword fields [#96161](https://github.com/elastic/elasticsearch/pull/96161) (issue: [#95541](https://github.com/elastic/elasticsearch/issues/95541))

* Support CCS minimize round trips in async search [#96012](https://github.com/elastic/elasticsearch/pull/96012)

* Support for patter_replace filter in keyword normalizer [#96588](https://github.com/elastic/elasticsearch/pull/96588)

* Support null_value for rank_feature field type [#95811](https://github.com/elastic/elasticsearch/pull/95811)

Security

* Add "_storage" internal user [#95694](https://github.com/elastic/elasticsearch/pull/95694)

Snapshot/Restore

* Reduce overhead in blob cache service get [#96399](https://github.com/elastic/elasticsearch/pull/96399)

Stats

* Add `ingest` information to the cluster info endpoint [#96328](https://github.com/elastic/elasticsearch/pull/96328) (issue: [#95392](https://github.com/elastic/elasticsearch/issues/95392))

* Add `script` information to the cluster info endpoint [#96613](https://github.com/elastic/elasticsearch/pull/96613) (issue: [#95394](https://github.com/elastic/elasticsearch/issues/95394))

* Add `thread_pool` information to the cluster info endpoint [#96407](https://github.com/elastic/elasticsearch/pull/96407) (issue: [#95393](https://github.com/elastic/elasticsearch/issues/95393))

TSDB

* Feature: include unit support for time series rate aggregation [#96605](https://github.com/elastic/elasticsearch/pull/96605) (issue: [#94630](https://github.com/elastic/elasticsearch/issues/94630))

Vector Search

* Leverage SIMD hardware instructions in Vector Search [#96453](https://github.com/elastic/elasticsearch/pull/96453) (issue: [#96370](https://github.com/elastic/elasticsearch/issues/96370))

### New features

Application

* Enable analytics geoip in behavioral analytics [#96624](https://github.com/elastic/elasticsearch/pull/96624)

Authorization

* Support restricting access of API keys to only certain workflows [#96744](https://github.com/elastic/elasticsearch/pull/96744)

Data streams

* Adding ability to auto-install ingest pipelines and refer to them from index templates [#95782](https://github.com/elastic/elasticsearch/pull/95782)

Geo

* Geometry simplifier [#94859](https://github.com/elastic/elasticsearch/pull/94859)

ILM+SLM

* Enhance ILM Health Indicator [#96092](https://github.com/elastic/elasticsearch/pull/96092)

Infra/Node Lifecycle

* Gracefully shutdown elasticsearch [#96363](https://github.com/elastic/elasticsearch/pull/96363)

Infra/Plugins

* [Fleet] Add `.fleet-secrets` system index [#95625](https://github.com/elastic/elasticsearch/pull/95625) (issue: [#95143](https://github.com/elastic/elasticsearch/issues/95143))

Machine Learning

* Add support for `xlm_roberta` tokenized models [#94089](https://github.com/elastic/elasticsearch/pull/94089)

* Removes the technical preview admonition from query_vector_builder docs [#96735](https://github.com/elastic/elasticsearch/pull/96735)

Snapshot/Restore

* Add repo throttle metrics to node stats api response [#96678](https://github.com/elastic/elasticsearch/pull/96678) (issue: [#89385](https://github.com/elastic/elasticsearch/issues/89385))

Stats

* New HTTP info endpoint [#96198](https://github.com/elastic/elasticsearch/pull/96198) (issue: [#95391](https://github.com/elastic/elasticsearch/issues/95391))

### Upgrades

Infra/Transport API

* Bump `TransportVersion` to the first non-release version number. Transport protocol is now versioned independently of release version. [#95286](https://github.com/elastic/elasticsearch/pull/95286)

Network

* Upgrade Netty to 4.1.92 [#95575](https://github.com/elastic/elasticsearch/pull/95575)

* Upgrade Netty to 4.1.94.Final [#97112](https://github.com/elastic/elasticsearch/pull/97112)

Search

* Upgrade Lucene to a 9.7.0 snapshot [#96433](https://github.com/elastic/elasticsearch/pull/96433)

* Upgrade to new lucene snapshot 9.7.0-snapshot-a8602d6ef88 [#96741](https://github.com/elastic/elasticsearch/pull/96741)