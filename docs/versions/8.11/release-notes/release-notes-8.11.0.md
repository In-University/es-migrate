**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.11.0

Also see [Breaking changes in 8.11](migrating-8.11.html#breaking-changes-8.11).

### Breaking changes

Infra/Core

* Remove `transport_versions` from cluster state API [#99223](https://github.com/elastic/elasticsearch/pull/99223)

### Known issues

* High Memory Pressure due to a GC change in JDK 21

This version of Elasticsearch is bundled with JDK 21. In JDK 21
[Preventive GC has been removed](https://bugs.openjdk.org/browse/JDK-8297639).
This may lead to increased memory pressure and an increased number of CircuitBreakerExceptions when retrieving large
documents under some particular load. (issue: [#99592](https://github.com/elastic/elasticsearch/issues/99592))

If you needed to explicitly [enable Preventive GC for your workload in a previous Elasticsearch
version](release-notes-8.10.0.html#known-issues-8.10.0), we recommend you avoid to upgrade to this version, as the settings to enable Preventive GC have been removed
from JDK 21.

### Bug fixes

Aggregations

* Adjust `DateHistogram's` bucket accounting to be iteratively [#101012](https://github.com/elastic/elasticsearch/pull/101012)

* Allow parsing on non-string routing fields [#97729](https://github.com/elastic/elasticsearch/pull/97729)

* Support runtime fields in synthetic source [#99796](https://github.com/elastic/elasticsearch/pull/99796) (issue: [#98287](https://github.com/elastic/elasticsearch/issues/98287))

Allocation

* Consider node shutdown in `DataTierAllocationDecider` [#98824](https://github.com/elastic/elasticsearch/pull/98824) (issue: [#97207](https://github.com/elastic/elasticsearch/issues/97207))

Application

* Align look-back with client-side cache [#101264](https://github.com/elastic/elasticsearch/pull/101264)

* Increase K/V look-back time interval [#101205](https://github.com/elastic/elasticsearch/pull/101205)

* Provide stable resampling [#101255](https://github.com/elastic/elasticsearch/pull/101255)

* [Profiling] Tighten resource creation check [#99873](https://github.com/elastic/elasticsearch/pull/99873)

Authorization

* Allow `enrich_user` to read/view enrich indices [#100707](https://github.com/elastic/elasticsearch/pull/100707)

* Grant editor and viewer access to profiling [#100594](https://github.com/elastic/elasticsearch/pull/100594)

CCR

* CCR: Use local cluster state request [#100323](https://github.com/elastic/elasticsearch/pull/100323)

CRUD

* Change `GetFromTranslog` to indices action [#99300](https://github.com/elastic/elasticsearch/pull/99300)

* Wait for cluster to recover before resolving index template [#99797](https://github.com/elastic/elasticsearch/pull/99797)

Cluster Coordination

* Reset `GatewayService` flags before reroute [#98653](https://github.com/elastic/elasticsearch/pull/98653) (issue: [#98606](https://github.com/elastic/elasticsearch/issues/98606))

Data streams

* DSL waits for the tsdb time boundaries to lapse [#100470](https://github.com/elastic/elasticsearch/pull/100470) (issue: [#99696](https://github.com/elastic/elasticsearch/issues/99696))

* Propagate cancellation in `DataTiersUsageTransportAction` [#100253](https://github.com/elastic/elasticsearch/pull/100253)

* [DSL] skip deleting indices that have in-progress downsampling operations [#101495](https://github.com/elastic/elasticsearch/pull/101495)

Downsampling

* Make downsample target index replicas configurable [#99712](https://github.com/elastic/elasticsearch/pull/99712)

ES|QL

* "params" correctly parses the values including an optional "type" [#99310](https://github.com/elastic/elasticsearch/pull/99310) (issue: [#99294](https://github.com/elastic/elasticsearch/issues/99294))

* Account for an exception being thrown when building a `BytesRefArrayBlock` [#99726](https://github.com/elastic/elasticsearch/pull/99726) (issue: [#99472](https://github.com/elastic/elasticsearch/issues/99472))

* Add arithmetic operators [#98628](https://github.com/elastic/elasticsearch/pull/98628)

* Add identity check in Block equality [#100377](https://github.com/elastic/elasticsearch/pull/100377) (issue: [#100374](https://github.com/elastic/elasticsearch/issues/100374))

* Adds Enrich implicit `match_fields` to `field_caps` call [#101456](https://github.com/elastic/elasticsearch/pull/101456) (issue: [#101328](https://github.com/elastic/elasticsearch/issues/101328))

* Better management of not stored TEXT fiels with synthetic source [#99695](https://github.com/elastic/elasticsearch/pull/99695)

* Continue resolving attributes for Eval [#99601](https://github.com/elastic/elasticsearch/pull/99601) (issue: [#99576](https://github.com/elastic/elasticsearch/issues/99576))

* Create a Vector when needed for IN [#99382](https://github.com/elastic/elasticsearch/pull/99382) (issue: [#99347](https://github.com/elastic/elasticsearch/issues/99347))

* ESQL: Fix unreleased block in topn [#101648](https://github.com/elastic/elasticsearch/pull/101648) (issue: [#101588](https://github.com/elastic/elasticsearch/issues/101588))

* ESQL: check type before casting [#101492](https://github.com/elastic/elasticsearch/pull/101492) (issue: [#101489](https://github.com/elastic/elasticsearch/issues/101489))

* Fix NPE when aggregating literals [#99827](https://github.com/elastic/elasticsearch/pull/99827)

* Fix escaping of backslash in LIKE operator [#101120](https://github.com/elastic/elasticsearch/pull/101120) (issue: [#101106](https://github.com/elastic/elasticsearch/issues/101106))

* Fix eval of functions on foldable literals [#101438](https://github.com/elastic/elasticsearch/pull/101438) (issue: [#101425](https://github.com/elastic/elasticsearch/issues/101425))

* Fix non-null value being returned for unsupported data types in `ValueSources` [#100656](https://github.com/elastic/elasticsearch/pull/100656) (issue: [#100048](https://github.com/elastic/elasticsearch/issues/100048))

* Graceful handling of non-bool condition in the filter [#100645](https://github.com/elastic/elasticsearch/pull/100645) (issues: [#100049](https://github.com/elastic/elasticsearch/issues/100049), [#100409](https://github.com/elastic/elasticsearch/issues/100409))

* Handle queries with non-existing enrich policies and no field [#100647](https://github.com/elastic/elasticsearch/pull/100647) (issue: [#100593](https://github.com/elastic/elasticsearch/issues/100593))

* Implement serialization of `InvalidMappedField` [#98972](https://github.com/elastic/elasticsearch/pull/98972) (issue: [#98851](https://github.com/elastic/elasticsearch/issues/98851))

* Improve verifier error for incorrect agg declaration [#100650](https://github.com/elastic/elasticsearch/pull/100650) (issue: [#100641](https://github.com/elastic/elasticsearch/issues/100641))

* Limit how many bytes `concat()` can process [#100360](https://github.com/elastic/elasticsearch/pull/100360)

* Make DISSECT parameter `append_separator` case insensitive [#101358](https://github.com/elastic/elasticsearch/pull/101358) (issue: [#101138](https://github.com/elastic/elasticsearch/issues/101138))

* Page shouldn’t close a block twice [#100370](https://github.com/elastic/elasticsearch/pull/100370) (issues: [#100356](https://github.com/elastic/elasticsearch/issues/100356), [#100365](https://github.com/elastic/elasticsearch/issues/100365))

* Preserve intermediate aggregation output in local relation [#100866](https://github.com/elastic/elasticsearch/pull/100866) (issue: [#100807](https://github.com/elastic/elasticsearch/issues/100807))

* Properly handle multi-values in fold() and date math [#100766](https://github.com/elastic/elasticsearch/pull/100766) (issue: [#100497](https://github.com/elastic/elasticsearch/issues/100497))

* Remove aliasing inside Eval [#100238](https://github.com/elastic/elasticsearch/pull/100238) (issue: [#100174](https://github.com/elastic/elasticsearch/issues/100174))

* Resilience to non-indexed fields [#99588](https://github.com/elastic/elasticsearch/pull/99588) (issue: [#99506](https://github.com/elastic/elasticsearch/issues/99506))

* Skip synthetic attributes when planning the physical fragment [#99188](https://github.com/elastic/elasticsearch/pull/99188) (issue: [#99170](https://github.com/elastic/elasticsearch/issues/99170))

* Support date and time intervals as input params [#101001](https://github.com/elastic/elasticsearch/pull/101001) (issue: [#99570](https://github.com/elastic/elasticsearch/issues/99570))

* Support queries that don’t return underlying fields [#98759](https://github.com/elastic/elasticsearch/pull/98759) (issue: [#98404](https://github.com/elastic/elasticsearch/issues/98404))

* Use exact attributes for data source extraction [#99874](https://github.com/elastic/elasticsearch/pull/99874) (issue: [#99183](https://github.com/elastic/elasticsearch/issues/99183))

* `mv_expand` pushes down limit and project and keep the limit after it untouched [#100782](https://github.com/elastic/elasticsearch/pull/100782) (issues: [#99971](https://github.com/elastic/elasticsearch/issues/99971), [#100774](https://github.com/elastic/elasticsearch/issues/100774))

* support metric tsdb fields while querying index patterns [#100351](https://github.com/elastic/elasticsearch/pull/100351) (issue: [#100144](https://github.com/elastic/elasticsearch/issues/100144))

Geo

* Use `NamedWritable` to enable `GeoBoundingBox` serialisation [#99163](https://github.com/elastic/elasticsearch/pull/99163) (issue: [#99089](https://github.com/elastic/elasticsearch/issues/99089))

Health

* Fix NPE in `StableMasterHealthIndicatorService` [#98635](https://github.com/elastic/elasticsearch/pull/98635)

* Health report infrastructure doesn’t trip the circuit breakers [#101629](https://github.com/elastic/elasticsearch/pull/101629)

* Propagate cancellation in `GetHealthAction` [#100273](https://github.com/elastic/elasticsearch/pull/100273)

Highlighting

* Correctly handle `ScriptScoreQuery` in plain highlighter [#99804](https://github.com/elastic/elasticsearch/pull/99804) (issue: [#99700](https://github.com/elastic/elasticsearch/issues/99700))

* Disable `weight_matches` when kNN query is present [#101713](https://github.com/elastic/elasticsearch/pull/101713)

ILM+SLM

* Compute SLM retention from `RepositoryData` [#100092](https://github.com/elastic/elasticsearch/pull/100092) (issue: [#99953](https://github.com/elastic/elasticsearch/issues/99953))

* `WaitForSnapshotStep` verifies if the index belongs to the latest snapshot of that SLM policy [#100911](https://github.com/elastic/elasticsearch/pull/100911)

Infra/Core

* Add `java.net.NetPermission` to APM module’s permissions [#99474](https://github.com/elastic/elasticsearch/pull/99474)

* Don’t update system index mappings in mixed clusters [#101778](https://github.com/elastic/elasticsearch/pull/101778) (issues: [#101331](https://github.com/elastic/elasticsearch/issues/101331), [#99778](https://github.com/elastic/elasticsearch/issues/99778))

* Revert "Kibana system index does not allow user templates to affect it" [#98888](https://github.com/elastic/elasticsearch/pull/98888)

* Specify correct current `IndexVersion` after 8.10 release [#98574](https://github.com/elastic/elasticsearch/pull/98574) (issue: [#98555](https://github.com/elastic/elasticsearch/issues/98555))

* Tracing: Use `doPriv` when working with spans, use `SpanId` [#100232](https://github.com/elastic/elasticsearch/pull/100232)

Infra/Scripting

* Improve painless error wrapping [#100872](https://github.com/elastic/elasticsearch/pull/100872)

Ingest Node

* Improving tika handling [#101486](https://github.com/elastic/elasticsearch/pull/101486)

* Update enrich execution to only set index false on fields that support it [#98038](https://github.com/elastic/elasticsearch/pull/98038) (issue: [#98019](https://github.com/elastic/elasticsearch/issues/98019))

Machine Learning

* Avoid risk of OOM in datafeeds when memory is constrained [#98915](https://github.com/elastic/elasticsearch/pull/98915) (issue: [#89769](https://github.com/elastic/elasticsearch/issues/89769))

* Fix for inference requests being sent to every node with a model allocation. If there are more nodes than items in the original request then empty requests were sent. [#100388](https://github.com/elastic/elasticsearch/pull/100388) (issue: [#100180](https://github.com/elastic/elasticsearch/issues/100180))

* Preserve order of inference results when calling the _infer API with multiple inputs on a model deployment with more than one allocation the output results order was not guaranteed to match the input order. The fix ensures the output order matches the input order. [#100143](https://github.com/elastic/elasticsearch/pull/100143)

* Remove noisy *Could not find trained model* message [#100760](https://github.com/elastic/elasticsearch/pull/100760)

* Safely drain deployment request queues before allowing node to shutdown [#98406](https://github.com/elastic/elasticsearch/pull/98406)

* Use the correct writable name for model assignment metadata in mixed version clusters. Prevents a node failure due to IllegalArgumentException Unknown NamedWriteable [trained_model_assignment] [#100886](https://github.com/elastic/elasticsearch/pull/100886)

* Wait to gracefully stop deployments until alternative allocation exists [#99107](https://github.com/elastic/elasticsearch/pull/99107)

Mapping

* Automatically disable `ignore_malformed` on datastream `@timestamp` fields [#99346](https://github.com/elastic/elasticsearch/pull/99346)

* Correct behaviour of `ContentPath::remove()` [#98332](https://github.com/elastic/elasticsearch/pull/98332) (issue: [#98327](https://github.com/elastic/elasticsearch/issues/98327))

* Fix merges of mappings with `subobjects: false` for composable index templates [#97317](https://github.com/elastic/elasticsearch/pull/97317) (issue: [#96768](https://github.com/elastic/elasticsearch/issues/96768))

* Percolator to support parsing script score query with params [#101051](https://github.com/elastic/elasticsearch/pull/101051) (issue: [#97377](https://github.com/elastic/elasticsearch/issues/97377))

Network

* Do not report failure after connections are made [#99117](https://github.com/elastic/elasticsearch/pull/99117)

Percolator

* Fix percolator query for stored queries that expand on wildcard field names [#98878](https://github.com/elastic/elasticsearch/pull/98878)

Query Languages

* Preserve subfields for unsupported types [#100875](https://github.com/elastic/elasticsearch/pull/100875) (issue: [#100869](https://github.com/elastic/elasticsearch/issues/100869))

Recovery

* Fix interruption of `markAllocationIdAsInSync` [#100610](https://github.com/elastic/elasticsearch/pull/100610) (issues: [#96578](https://github.com/elastic/elasticsearch/issues/96578), [#100589](https://github.com/elastic/elasticsearch/issues/100589))

Search

* Consistent scores for multi-term `SourceConfirmedTestQuery` [#100846](https://github.com/elastic/elasticsearch/pull/100846) (issue: [#98712](https://github.com/elastic/elasticsearch/issues/98712))

* Fix UnsignedLong field range query gt "0" can get the result equal to 0 [#98843](https://github.com/elastic/elasticsearch/pull/98843)

* Fix `advanceExact` for doc values from sources [#99685](https://github.com/elastic/elasticsearch/pull/99685)

* Fork response-sending in `OpenPointInTimeAction` [#99222](https://github.com/elastic/elasticsearch/pull/99222)

* [CI] `SearchResponseTests#testSerialization` failing resolved [#100020](https://github.com/elastic/elasticsearch/pull/100020) (issue: [#100005](https://github.com/elastic/elasticsearch/issues/100005))

* fix fuzzy query rewrite parameter not work [#97642](https://github.com/elastic/elasticsearch/pull/97642)

Security

* Fix NullPointerException in RotableSecret [#100779](https://github.com/elastic/elasticsearch/pull/100779) (issue: [#99759](https://github.com/elastic/elasticsearch/issues/99759))

Snapshot/Restore

* Fix race condition in `SnapshotsService` [#101652](https://github.com/elastic/elasticsearch/pull/101652)

* Fix snapshot double finalization [#101497](https://github.com/elastic/elasticsearch/pull/101497)

* Fix thread context in `getRepositoryData` [#99627](https://github.com/elastic/elasticsearch/pull/99627)

* Frozen index input clone copy cache file [#98930](https://github.com/elastic/elasticsearch/pull/98930)

* Make S3 anti-contention delay configurable [#101245](https://github.com/elastic/elasticsearch/pull/101245)

* More robust timeout for repo analysis [#101184](https://github.com/elastic/elasticsearch/pull/101184) (issue: [#101182](https://github.com/elastic/elasticsearch/issues/101182))

* Register `repository_s3` settings [#101344](https://github.com/elastic/elasticsearch/pull/101344)

* Reinstate `RepositoryData` BwC [#100447](https://github.com/elastic/elasticsearch/pull/100447)

TSDB

* Don’t ignore empty index template that have no template definition [#98840](https://github.com/elastic/elasticsearch/pull/98840) (issue: [#98834](https://github.com/elastic/elasticsearch/issues/98834))

* Fix painless execute api and tsdb issue [#101212](https://github.com/elastic/elasticsearch/pull/101212) (issue: [#101072](https://github.com/elastic/elasticsearch/issues/101072))

* Make tsdb settings public in Serverless [#99567](https://github.com/elastic/elasticsearch/pull/99567) (issue: [#99563](https://github.com/elastic/elasticsearch/issues/99563))

Transform

* Fix possible NPE when getting transform stats for failed transforms [#98061](https://github.com/elastic/elasticsearch/pull/98061) (issue: [#98052](https://github.com/elastic/elasticsearch/issues/98052))

* Ignore `IndexNotFound` error when refreshing destination index [#101627](https://github.com/elastic/elasticsearch/pull/101627)

* Make Transform Feature Reset really wait for all the tasks [#100624](https://github.com/elastic/elasticsearch/pull/100624)

* Make tasks that calculate checkpoints cancellable [#100808](https://github.com/elastic/elasticsearch/pull/100808)

Watcher

* Treating watcher webhook response header names as case-insensitive [#99717](https://github.com/elastic/elasticsearch/pull/99717)

### Deprecations

Rollup

* Rollup functionality is now deprecated [#101265](https://github.com/elastic/elasticsearch/pull/101265)

### Enhancements

Aggregations

* Disable `FilterByFilterAggregator` through `ClusterSettings` [#99417](https://github.com/elastic/elasticsearch/pull/99417) (issue: [#99335](https://github.com/elastic/elasticsearch/issues/99335))

* Represent histogram value count as long [#99912](https://github.com/elastic/elasticsearch/pull/99912) (issue: [#99820](https://github.com/elastic/elasticsearch/issues/99820))

* Skip `DisiPriorityQueue` on single filter agg [#99215](https://github.com/elastic/elasticsearch/pull/99215) (issue: [#99202](https://github.com/elastic/elasticsearch/issues/99202))

* Use a competitive iterator in `FiltersAggregator` [#98360](https://github.com/elastic/elasticsearch/pull/98360) (issue: [#97544](https://github.com/elastic/elasticsearch/issues/97544))

Allocation

* Report a node’s "roles" setting in the /_cluster/allocation/explain response [#98550](https://github.com/elastic/elasticsearch/pull/98550) (issue: [#97859](https://github.com/elastic/elasticsearch/issues/97859))

Application

* Add flamegraph API [#99091](https://github.com/elastic/elasticsearch/pull/99091)

* [Profiling] Allow to customize the ILM policy [#99909](https://github.com/elastic/elasticsearch/pull/99909)

* [Profiling] Allow to wait until resources created [#99655](https://github.com/elastic/elasticsearch/pull/99655)

Audit

* Reduce verbosity of the bulk indexing audit log [#98470](https://github.com/elastic/elasticsearch/pull/98470)

Authentication

* Allow native users/roles to be disabled via setting [#98654](https://github.com/elastic/elasticsearch/pull/98654)

CAT APIs

* Add *dataset* size to cat indices and cat shards [#98622](https://github.com/elastic/elasticsearch/pull/98622) (issue: [#95092](https://github.com/elastic/elasticsearch/issues/95092))

Data streams

* Allow explain data stream lifecycle to accept a data stream [#98811](https://github.com/elastic/elasticsearch/pull/98811)

ES|QL

* Add `CEIL` function [#98847](https://github.com/elastic/elasticsearch/pull/98847)

* Add ability to perform date math [#98870](https://github.com/elastic/elasticsearch/pull/98870) (issue: [#98402](https://github.com/elastic/elasticsearch/issues/98402))

* Add support for TEXT fields in comparison operators and SORT [#98528](https://github.com/elastic/elasticsearch/pull/98528) (issue: [#98642](https://github.com/elastic/elasticsearch/issues/98642))

* Compact topn [#99316](https://github.com/elastic/elasticsearch/pull/99316)

* Date math for negatives [#99711](https://github.com/elastic/elasticsearch/pull/99711)

* Enable arithmetics for durations and periods [#99432](https://github.com/elastic/elasticsearch/pull/99432) (issue: [#99293](https://github.com/elastic/elasticsearch/issues/99293))

* Enhance SHOW FUNCTIONS command [#99736](https://github.com/elastic/elasticsearch/pull/99736) (issue: [#99507](https://github.com/elastic/elasticsearch/issues/99507))

* Improve log messages [#99470](https://github.com/elastic/elasticsearch/pull/99470)

* Log execution time consistently [#99286](https://github.com/elastic/elasticsearch/pull/99286)

* Log query and execution time [#99058](https://github.com/elastic/elasticsearch/pull/99058)

* Log start and end of queries [#99746](https://github.com/elastic/elasticsearch/pull/99746)

* Lower the implicit limit, if none is user-provided [#99816](https://github.com/elastic/elasticsearch/pull/99816) (issue: [#99458](https://github.com/elastic/elasticsearch/issues/99458))

* Make settings dynamic [#101516](https://github.com/elastic/elasticsearch/pull/101516)

* Mark counter fields as unsupported [#99054](https://github.com/elastic/elasticsearch/pull/99054)

* Remove the swapped-args check for date_xxx() [#101362](https://github.com/elastic/elasticsearch/pull/101362) (issue: [#99562](https://github.com/elastic/elasticsearch/issues/99562))

* Serialize the source in expressions [#99956](https://github.com/elastic/elasticsearch/pull/99956)

* Simple check if all blocks get released [#100199](https://github.com/elastic/elasticsearch/pull/100199)

* Support unsigned long in sqrt and log10 [#98711](https://github.com/elastic/elasticsearch/pull/98711)

* Use DEBUG log level to report execution steps [#99303](https://github.com/elastic/elasticsearch/pull/99303)

Engine

* Use `IndexWriter.flushNextBuffer()` to reclaim memory from indexing buffers [#94607](https://github.com/elastic/elasticsearch/pull/94607)

Health

* Avoiding the use of nodes that are no longer in the cluster when computing master stability [#98809](https://github.com/elastic/elasticsearch/pull/98809) (issue: [#98636](https://github.com/elastic/elasticsearch/issues/98636))

* When a primary is inactive but this is considered expected, the same applies for the replica of this shard. [#99995](https://github.com/elastic/elasticsearch/pull/99995) (issue: [#99951](https://github.com/elastic/elasticsearch/issues/99951))

Infra/Core

* APM Metering API [#99832](https://github.com/elastic/elasticsearch/pull/99832)

* Update the elastic-apm-agent version [#100064](https://github.com/elastic/elasticsearch/pull/100064)

* Use mappings version to retrieve system index mappings at creation time [#99555](https://github.com/elastic/elasticsearch/pull/99555)

Infra/Node Lifecycle

* Add links to docs from failing bootstrap checks [#99644](https://github.com/elastic/elasticsearch/pull/99644) (issue: [#99614](https://github.com/elastic/elasticsearch/issues/99614))

* Chunk `SingleNodeShutdownStatus` and `ShutdownShardMigrationStatus` (and related action) response [#99798](https://github.com/elastic/elasticsearch/pull/99798) (issue: [#99678](https://github.com/elastic/elasticsearch/issues/99678))

Infra/REST API

* Add `IndexVersion` to node info [#99515](https://github.com/elastic/elasticsearch/pull/99515)

* Add component info versions to node info in a pluggable way [#99631](https://github.com/elastic/elasticsearch/pull/99631)

* Return a 410 (Gone) status code for unavailable API endpoints [#97397](https://github.com/elastic/elasticsearch/pull/97397)

Machine Learning

* Add new _inference API [#99224](https://github.com/elastic/elasticsearch/pull/99224)

* Adding an option for trained models to be platform specific [#99584](https://github.com/elastic/elasticsearch/pull/99584)

* Log warnings for jobs unassigned for a long time [#100154](https://github.com/elastic/elasticsearch/pull/100154)

* Simplify the Inference Ingest Processor configuration [#100205](https://github.com/elastic/elasticsearch/pull/100205)

Mapping

* Automatically flatten objects when subobjects:false [#97972](https://github.com/elastic/elasticsearch/pull/97972) (issue: [#88934](https://github.com/elastic/elasticsearch/issues/88934))

* Explicit parsing object capabilities of `FieldMappers` [#98684](https://github.com/elastic/elasticsearch/pull/98684) (issue: [#98537](https://github.com/elastic/elasticsearch/issues/98537))

* Reintroduce `sparse_vector` mapping [#98996](https://github.com/elastic/elasticsearch/pull/98996)

Network

* Chunk the cluster allocation explain response [#99641](https://github.com/elastic/elasticsearch/pull/99641) (issue: [#97803](https://github.com/elastic/elasticsearch/issues/97803))

Recovery

* Wait for cluster state in recovery [#99193](https://github.com/elastic/elasticsearch/pull/99193)

Search

* Add additional counters to `_clusters` response for all Cluster search states [#99566](https://github.com/elastic/elasticsearch/pull/99566) (issue: [#98927](https://github.com/elastic/elasticsearch/issues/98927))

* Adding support for exist queries to `sparse_vector` fields [#99775](https://github.com/elastic/elasticsearch/pull/99775) (issue: [#99319](https://github.com/elastic/elasticsearch/issues/99319))

* Make `_index` optional for pinned query docs [#97450](https://github.com/elastic/elasticsearch/pull/97450)

* Reduce copying when creating scroll/PIT ids [#99219](https://github.com/elastic/elasticsearch/pull/99219)

* Refactor `SearchResponseClusters` to use CHM [#100129](https://github.com/elastic/elasticsearch/pull/100129) (issue: [#99101](https://github.com/elastic/elasticsearch/issues/99101))

* Support cluster/details for CCS minimize_roundtrips=false [#98457](https://github.com/elastic/elasticsearch/pull/98457)

Security

* Support rotatating the JWT shared secret [#99278](https://github.com/elastic/elasticsearch/pull/99278)

Snapshot/Restore

* Remove shard data files when they fail to write for snapshot [#99694](https://github.com/elastic/elasticsearch/pull/99694)

Stats

* Prune unnecessary information from TransportNodesInfoAction.NodeInfoRequest [#99938](https://github.com/elastic/elasticsearch/pull/99938) (issue: [#99744](https://github.com/elastic/elasticsearch/issues/99744))

TSDB

* Add `index.look_back_time` setting for tsdb data streams [#98518](https://github.com/elastic/elasticsearch/pull/98518) (issue: [#98463](https://github.com/elastic/elasticsearch/issues/98463))

* Improve time-series error and documentation [#100018](https://github.com/elastic/elasticsearch/pull/100018)

* Trim stored fields for `_id` field in tsdb [#97409](https://github.com/elastic/elasticsearch/pull/97409)

Transform

* Add accessors required to recreate `TransformStats` object from the fields [#98844](https://github.com/elastic/elasticsearch/pull/98844)

Vector Search

* Add new max_inner_product vector similarity function [#99527](https://github.com/elastic/elasticsearch/pull/99527)

* Adds `nested` support for indexed `dense_vector` fields [#99763](https://github.com/elastic/elasticsearch/pull/99763)

* Dense vector field types are indexed by default [#98268](https://github.com/elastic/elasticsearch/pull/98268)

* Increase the max vector dims to 4096 [#99682](https://github.com/elastic/elasticsearch/pull/99682)

### New features

Analysis

* Add support for Persian language stemmer [#99106](https://github.com/elastic/elasticsearch/pull/99106) (issue: [#98911](https://github.com/elastic/elasticsearch/issues/98911))

Application

* Automatically map float arrays of lengths 128 - 2048 as dense_vector [#98512](https://github.com/elastic/elasticsearch/pull/98512) (issue: [#97532](https://github.com/elastic/elasticsearch/issues/97532))

Data streams

* GA the data stream lifecycle [#100187](https://github.com/elastic/elasticsearch/pull/100187)

* GET `_data_stream` displays both ILM and DSL information [#99947](https://github.com/elastic/elasticsearch/pull/99947)

ES|QL

* Integrate Elasticsearch Query Language, ES|QL [#98309](https://github.com/elastic/elasticsearch/pull/98309)

* LEAST and GREATEST functions [#98630](https://github.com/elastic/elasticsearch/pull/98630)

* LEFT function [#98942](https://github.com/elastic/elasticsearch/pull/98942)

* LTRIM, RTRIM and fix unicode whitespace [#98590](https://github.com/elastic/elasticsearch/pull/98590)

* RIGHT function [#98974](https://github.com/elastic/elasticsearch/pull/98974)

* TopN sorting with min and max for multi-value fields [#98337](https://github.com/elastic/elasticsearch/pull/98337)

### Upgrades

Packaging

* Update bundled JDK to 21.0.1 [#101133](https://github.com/elastic/elasticsearch/pull/101133)

Search

* Upgrade main to Lucene 9.8.0 [#100138](https://github.com/elastic/elasticsearch/pull/100138)