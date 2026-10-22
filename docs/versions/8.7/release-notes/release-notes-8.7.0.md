**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.7.0

Also see [Breaking changes in 8.7](migrating-8.7.html#breaking-changes-8.7).

### Known issues

* Shard rebalancing may temporarily unbalance cluster

From 8.6.0 onwards the default shard rebalancing algorithm will compute the
final desired balance and then make shard movements to reconcile the current
state of the cluster with the desired state. However the order in which the
shard movements take place may be skewed towards certain nodes, causing the
cluster to become temporarily unbalanced while the reconciliation is ongoing.
As always, once a node reaches a disk watermark it will not accept any
additional shards, but this skew may result in nodes reaching their disk
watermarks more often than expected in normal operation. Once the
reconciliation process completes, the cluster will be balanced again.

To avoid this problem, upgrade to 8.8.0 or later.

### Breaking changes

Ingest Node

* Making `JsonProcessor` stricter so that it does not silently drop data [#93179](https://github.com/elastic/elasticsearch/pull/93179) (issue: [#92898](https://github.com/elastic/elasticsearch/issues/92898))

Indices APIs

* The [Resolve index](indices-resolve-index-api.html) API implementation was adjusted to use the
same index resolution mechanism as other similar APIs, adding support for the
`ignore_unavailable` and `allow_no_indices` flags and the `_all` meta-index. If
there are no matching indices then earlier versions of this API would return an
empty result with the `200 OK` HTTP response code, but from 8.7.0 onwards by
default it returns an `IndexNotFoundException` with the `404 Not Found` HTTP
response code. To recover the old behaviour, add the query parameter
`?ignore_unavailable=true` ([#92820](https://github.com/elastic/elasticsearch/pull/92820)).

### Bug fixes

Aggregations

* Don’t create a new `DoubleHistogram` instance for empty buckets [#92547](https://github.com/elastic/elasticsearch/pull/92547)

* Fix: do not allow map key types other than String [#88686](https://github.com/elastic/elasticsearch/pull/88686) (issue: [#66057](https://github.com/elastic/elasticsearch/issues/66057))

Allocation

* Fallback to the actual shard size when forecast is not available [#93461](https://github.com/elastic/elasticsearch/pull/93461)

* Skip `DiskThresholdMonitor` when cluster state is not recovered [#93699](https://github.com/elastic/elasticsearch/pull/93699)

* Suppress response headers in `AllocationActionMultiListener` [#93777](https://github.com/elastic/elasticsearch/pull/93777) (issue: [#93773](https://github.com/elastic/elasticsearch/issues/93773))

Authentication

* Correctly remove domain from realm when rewriting `Authentication` for compatibility with node versions that don’t
support domains [#93276](https://github.com/elastic/elasticsearch/pull/93276)

Authorization

* Fix Security’s expression resolver to not remove unavailable but authorized names [#92625](https://github.com/elastic/elasticsearch/pull/92625)

CCR

* Deduplicate Heavy CCR Repository CS Requests [#91398](https://github.com/elastic/elasticsearch/pull/91398)

CRUD

* Avoid NPE in Stateless Get/mGet [#94164](https://github.com/elastic/elasticsearch/pull/94164)

* Do not refresh all indices in `TransportBulkAction` [#93417](https://github.com/elastic/elasticsearch/pull/93417)

Cluster Coordination

* Delay master task failure notifications until commit [#92693](https://github.com/elastic/elasticsearch/pull/92693) (issue: [#92677](https://github.com/elastic/elasticsearch/issues/92677))

Data streams

* Allow different filters per `DataStream` in a `DataStreamAlias` [#92692](https://github.com/elastic/elasticsearch/pull/92692) (issue: [#92050](https://github.com/elastic/elasticsearch/issues/92050))

Geo

* Build index qualified name in cross cluster vector tile search [#94574](https://github.com/elastic/elasticsearch/pull/94574) (issue: [#94557](https://github.com/elastic/elasticsearch/issues/94557))

* Check `GeohexGrid` bounds on geopoint using spherical coordinates [#92460](https://github.com/elastic/elasticsearch/pull/92460)

* Fix bug when clipping Geometry collections in vector tiles [#93562](https://github.com/elastic/elasticsearch/pull/93562)

Health

* Take into account `max_headroom` in disk watermark calculations [#93157](https://github.com/elastic/elasticsearch/pull/93157) (issue: [#93155](https://github.com/elastic/elasticsearch/issues/93155))

ILM+SLM

* Allow ILM step transition to the phase terminal step [#91754](https://github.com/elastic/elasticsearch/pull/91754)

* Avoiding `BulkProcessor` deadlock in ILMHistoryStore [#91238](https://github.com/elastic/elasticsearch/pull/91238) (issues: [#68468](https://github.com/elastic/elasticsearch/issues/68468), [#50440](https://github.com/elastic/elasticsearch/issues/50440))

* Fixed changing only the `forceMerge` flag in `SearchableSnapshotAction` wouldn’t update the policy [#93847](https://github.com/elastic/elasticsearch/pull/93847)

* Preventing ILM and SLM runtime state from being stored in a snapshot [#92252](https://github.com/elastic/elasticsearch/pull/92252)

Infra/CLI

* Restore printing bootstrap checks as errors [#93178](https://github.com/elastic/elasticsearch/pull/93178) (issue: [#93074](https://github.com/elastic/elasticsearch/issues/93074))

Infra/Core

* Add `jdk.internal.reflect` permission to es codebase [#92387](https://github.com/elastic/elasticsearch/pull/92387) (issue: [#92356](https://github.com/elastic/elasticsearch/issues/92356))

* Add checks for exception loops through suppressed exceptions only [#93944](https://github.com/elastic/elasticsearch/pull/93944) (issue: [#93943](https://github.com/elastic/elasticsearch/issues/93943))

* Ensure one-shot wrappers release their delegates [#92928](https://github.com/elastic/elasticsearch/pull/92928)

* Fix `InputStream#readAllBytes` on `InputStreamIndexInput` [#92680](https://github.com/elastic/elasticsearch/pull/92680)

* Fix indices resolver for datemath with colon [#92973](https://github.com/elastic/elasticsearch/pull/92973)

* Make `FilterStreamInput` less trappy [#92422](https://github.com/elastic/elasticsearch/pull/92422)

Infra/Plugins

* Ensure ordering of plugin initialization [#93882](https://github.com/elastic/elasticsearch/pull/93882) (issue: [#93851](https://github.com/elastic/elasticsearch/issues/93851))

* Fix unclosed directory stream in `ClassReaders` [#92890](https://github.com/elastic/elasticsearch/pull/92890) (issue: [#92866](https://github.com/elastic/elasticsearch/issues/92866))

* Update the version of asm used by plugin scanner [#92784](https://github.com/elastic/elasticsearch/pull/92784) (issue: [#92782](https://github.com/elastic/elasticsearch/issues/92782))

Infra/REST API

* [Rest Api Compatibility] Format response media type with parameters [#92695](https://github.com/elastic/elasticsearch/pull/92695)

Infra/Scripting

* Fix NPE when method was called on an array type [#91713](https://github.com/elastic/elasticsearch/pull/91713) (issue: [#87562](https://github.com/elastic/elasticsearch/issues/87562))

Infra/Settings

* Fix parse failures for ILM operator settings [#94477](https://github.com/elastic/elasticsearch/pull/94477) (issue: [#94465](https://github.com/elastic/elasticsearch/issues/94465))

Ingest Node

* Better names and types for ingest stats [#93533](https://github.com/elastic/elasticsearch/pull/93533) (issue: [#80763](https://github.com/elastic/elasticsearch/issues/80763))

* Correctly handle an exception case for ingest failure [#92455](https://github.com/elastic/elasticsearch/pull/92455)

* Disable ingest-attachment logging [#93878](https://github.com/elastic/elasticsearch/pull/93878)

* Download the geoip databases only when needed [#92335](https://github.com/elastic/elasticsearch/pull/92335) (issue: [#90673](https://github.com/elastic/elasticsearch/issues/90673))

* Forwarding simulate calls to ingest nodes [#92171](https://github.com/elastic/elasticsearch/pull/92171)

* Grok returns a list of matches for repeated pattern names #92092 [#92586](https://github.com/elastic/elasticsearch/pull/92586) (issue: [#92092](https://github.com/elastic/elasticsearch/issues/92092))

* Handle a default/request pipeline and a final pipeline with minimal additional overhead [#93329](https://github.com/elastic/elasticsearch/pull/93329) (issues: [#92843](https://github.com/elastic/elasticsearch/issues/92843), [#81244](https://github.com/elastic/elasticsearch/issues/81244), [#93118](https://github.com/elastic/elasticsearch/issues/93118))

* Ingest-attachment module tika dependency versions [#93755](https://github.com/elastic/elasticsearch/pull/93755)

* More accurate total ingest stats [#91730](https://github.com/elastic/elasticsearch/pull/91730) (issue: [#91358](https://github.com/elastic/elasticsearch/issues/91358))

* Speed up ingest geoip processors [#92372](https://github.com/elastic/elasticsearch/pull/92372)

* Speed up ingest set and append processors [#92395](https://github.com/elastic/elasticsearch/pull/92395)

Machine Learning

* Allocate trained models if zone awareness attributes not set [#94128](https://github.com/elastic/elasticsearch/pull/94128) (issue: [#94123](https://github.com/elastic/elasticsearch/issues/94123))

* Fix data counts race condition when starting a datafeed [#93324](https://github.com/elastic/elasticsearch/pull/93324) (issue: [#93298](https://github.com/elastic/elasticsearch/issues/93298))

* Fix tokenization bug when handling normalization in BERT and MPNet [#92329](https://github.com/elastic/elasticsearch/pull/92329)

* Free resources correctly when model loading is cancelled [#92204](https://github.com/elastic/elasticsearch/pull/92204)

* Stop the `frequent_items` aggregation reporting a subset when a superset exists [#92239](https://github.com/elastic/elasticsearch/pull/92239)

* Use long inference timeout at ingest [#93731](https://github.com/elastic/elasticsearch/pull/93731)

Mapping

* Fix dynamic mapping detection for invalid dates [#94115](https://github.com/elastic/elasticsearch/pull/94115) (issue: [#93888](https://github.com/elastic/elasticsearch/issues/93888))

* No length check for source-only keyword fields [#93299](https://github.com/elastic/elasticsearch/pull/93299) (issue: [#9304](https://github.com/elastic/elasticsearch/issues/9304))

Network

* Delay Connection#onRemoved while pending [#92546](https://github.com/elastic/elasticsearch/pull/92546)

* Fix fransport handshake starting before tls handshake completes [#90534](https://github.com/elastic/elasticsearch/pull/90534) (issue: [#77999](https://github.com/elastic/elasticsearch/issues/77999))

* Protect `NodeConnectionsService` from stale conns [#92558](https://github.com/elastic/elasticsearch/pull/92558) (issue: [#92029](https://github.com/elastic/elasticsearch/issues/92029))

Recovery

* Disable recovery monitor before recovery start [#93551](https://github.com/elastic/elasticsearch/pull/93551) (issue: [#93542](https://github.com/elastic/elasticsearch/issues/93542))

* Fix potential leak in `RemoteRecoveryHandler` [#91802](https://github.com/elastic/elasticsearch/pull/91802)

* Report recovered files as recovered from snapshot for fully mounted searchable snapshots [#92976](https://github.com/elastic/elasticsearch/pull/92976)

Rollup

* Downsampling unmapped text fields [#94387](https://github.com/elastic/elasticsearch/pull/94387) (issue: [#94346](https://github.com/elastic/elasticsearch/issues/94346))

* Propagate timestamp format and convert nanoseconds to milliseconds [#94141](https://github.com/elastic/elasticsearch/pull/94141) (issue: [#94085](https://github.com/elastic/elasticsearch/issues/94085))

* Stop processing `TransportDownsampleAction` on failure [#94624](https://github.com/elastic/elasticsearch/pull/94624)

* Support downsampling of histogram as labels [#93445](https://github.com/elastic/elasticsearch/pull/93445) (issue: [#93263](https://github.com/elastic/elasticsearch/issues/93263))

Search

* Add null check for sort fields over collapse fields [#94546](https://github.com/elastic/elasticsearch/pull/94546) (issue: [#94407](https://github.com/elastic/elasticsearch/issues/94407))

* Annotated highlighter does not match when search contains both annotation and annotated term [#92920](https://github.com/elastic/elasticsearch/pull/92920) (issue: [#91944](https://github.com/elastic/elasticsearch/issues/91944))

* Clear field caps index responses on cancelled [#93716](https://github.com/elastic/elasticsearch/pull/93716) (issue: [#93029](https://github.com/elastic/elasticsearch/issues/93029))

* Do not include frozen indices in PIT by default [#94377](https://github.com/elastic/elasticsearch/pull/94377)

* Fix NPE thrown by prefix query in strange scenarios [#94369](https://github.com/elastic/elasticsearch/pull/94369)

* Fix _id field fetch issue. [#94528](https://github.com/elastic/elasticsearch/pull/94528) (issue: [#94515](https://github.com/elastic/elasticsearch/issues/94515))

* Fix metadata `_size` when it comes to stored fields extraction [#94483](https://github.com/elastic/elasticsearch/pull/94483) (issue: [#94468](https://github.com/elastic/elasticsearch/issues/94468))

* Fix missing override for matches in `ProfileWeight` [#92360](https://github.com/elastic/elasticsearch/pull/92360)

* Nested path info shouldn’t be added during `copy_to` [#93340](https://github.com/elastic/elasticsearch/pull/93340) (issue: [#93117](https://github.com/elastic/elasticsearch/issues/93117))

* Use all profiling events on startup [#92087](https://github.com/elastic/elasticsearch/pull/92087)

* Use keyword analyzer for untokenized fields in `TermVectorsService` [#94518](https://github.com/elastic/elasticsearch/pull/94518)

* [Profiling] Adjust handling of last data slice [#94283](https://github.com/elastic/elasticsearch/pull/94283)

* [Profiling] Ensure responses are only sent once [#93692](https://github.com/elastic/elasticsearch/pull/93692) (issue: [#93691](https://github.com/elastic/elasticsearch/issues/93691))

* [Profiling] Handle response processing errors [#93860](https://github.com/elastic/elasticsearch/pull/93860)

Snapshot/Restore

* Fix unhandled exception when blobstore repository contains unexpected file [#93914](https://github.com/elastic/elasticsearch/pull/93914)

* Support for GCS proxies everywhere in the GCS API [#92192](https://github.com/elastic/elasticsearch/pull/92192) (issue: [#91952](https://github.com/elastic/elasticsearch/issues/91952))

Stats

* Avoid capturing cluster state in TBbNA [#92255](https://github.com/elastic/elasticsearch/pull/92255)

TSDB

* Fix synthetic `_source` for sparse `_doc_count` field [#91769](https://github.com/elastic/elasticsearch/pull/91769) (issue: [#91731](https://github.com/elastic/elasticsearch/issues/91731))

Task Management

* Fix context leak in list tasks API [#93431](https://github.com/elastic/elasticsearch/pull/93431) (issue: [#93428](https://github.com/elastic/elasticsearch/issues/93428))

Transform

* Integrate "sourceHasChanged" call into failure handling and retry logic [#92762](https://github.com/elastic/elasticsearch/pull/92762) (issue: [#92133](https://github.com/elastic/elasticsearch/issues/92133))

Vector Search

* Fix `maxScore` calculation for kNN search [#93875](https://github.com/elastic/elasticsearch/pull/93875)

* Fix explain for kNN search matches [#93876](https://github.com/elastic/elasticsearch/pull/93876)

### Enhancements

Aggregations

* Optimize composite agg with leading global ordinal value source [#92197](https://github.com/elastic/elasticsearch/pull/92197)

Allocation

* Add `forecasted_write_load` and `forecasted_shard_size_in_bytes` to the endpoint [#92303](https://github.com/elastic/elasticsearch/pull/92303)

* Expose tier balancing stats via internal endpoint [#92199](https://github.com/elastic/elasticsearch/pull/92199)

* Introduce ShardRouting.Role [#92668](https://github.com/elastic/elasticsearch/pull/92668)

* Prevalidate node removal API (pt. 2) [#91256](https://github.com/elastic/elasticsearch/pull/91256) (issue: [#87776](https://github.com/elastic/elasticsearch/issues/87776))

* Simulate moves using cluster_concurrent_rebalance=2 [#93977](https://github.com/elastic/elasticsearch/pull/93977)

* Unpromotables skip replication and peer recovery [#93210](https://github.com/elastic/elasticsearch/pull/93210)

Authentication

* Add new `token_type` setting to JWT realm [#91536](https://github.com/elastic/elasticsearch/pull/91536)

* JWT realm - Initial support for access tokens [#91781](https://github.com/elastic/elasticsearch/pull/91781)

* JWT realm - Simplify token principal calculation [#92315](https://github.com/elastic/elasticsearch/pull/92315)

* JWT realm - add support for required claims [#92314](https://github.com/elastic/elasticsearch/pull/92314)

* Support custom PBKDF2 password hashes [#92871](https://github.com/elastic/elasticsearch/pull/92871)

Authorization

* Allowed indices matcher supports nested limited roles [#93306](https://github.com/elastic/elasticsearch/pull/93306)

* Extra `kibana_system` privileges for Fleet transform upgrades [#91499](https://github.com/elastic/elasticsearch/pull/91499)

* Pre-authorize child search transport actions [#91886](https://github.com/elastic/elasticsearch/pull/91886)

Cluster Coordination

* Add links to troubleshooting docs [#92755](https://github.com/elastic/elasticsearch/pull/92755) (issue: [#92741](https://github.com/elastic/elasticsearch/issues/92741))

* Improve node-{join,left} logging for troubleshooting [#92742](https://github.com/elastic/elasticsearch/pull/92742)

* Repeat `cluster.initial_master_nodes` log warning [#92744](https://github.com/elastic/elasticsearch/pull/92744)

EQL

* EQL Samples: add support for multiple samples per key [#91783](https://github.com/elastic/elasticsearch/pull/91783)

Engine

* Add commits listener for `InternalEngine` and `CombinedDeletionPolicy` [#92017](https://github.com/elastic/elasticsearch/pull/92017)

* Add primary term supplier to Engine.IndexCommitListener [#92101](https://github.com/elastic/elasticsearch/pull/92101)

* Adjust range of allowed percentages of deletes in an index [#93188](https://github.com/elastic/elasticsearch/pull/93188)

* Diff the list of filenames that are added by each new commit [#92238](https://github.com/elastic/elasticsearch/pull/92238)

* Set a fixed compound file threshold of 1GB [#92659](https://github.com/elastic/elasticsearch/pull/92659)

Geo

* Add methods to H3#hexRing to prevent allocating long arrays [#92711](https://github.com/elastic/elasticsearch/pull/92711)

* Add methods to prevent allocating long arrays during child navigation on H3 api [#92099](https://github.com/elastic/elasticsearch/pull/92099)

* Add new H3 api method #h3ToNoChildrenIntersecting [#91673](https://github.com/elastic/elasticsearch/pull/91673)

* In H3, compute destination point from distance and azimuth using planar 3d math" [#93084](https://github.com/elastic/elasticsearch/pull/93084)

* Protect H3 library against integer overflow [#92829](https://github.com/elastic/elasticsearch/pull/92829)

* Reduce number of object allocations in H3#h3ToGeoBoundary [#91586](https://github.com/elastic/elasticsearch/pull/91586)

* Speed H3 library by using `FastMath` implementation for trigonometric functions [#91839](https://github.com/elastic/elasticsearch/pull/91839)

Health

* Expose Health Api telemetry via xpack [#91708](https://github.com/elastic/elasticsearch/pull/91708) (issue: [#90877](https://github.com/elastic/elasticsearch/issues/90877))

* Health api stats [#91559](https://github.com/elastic/elasticsearch/pull/91559)

Indices APIs

* Add `ignore_missing_component_templates` config option [#92436](https://github.com/elastic/elasticsearch/pull/92436) (issue: [#92426](https://github.com/elastic/elasticsearch/issues/92426))

Infra/CLI

* Scan stable plugins for named components upon install [#92528](https://github.com/elastic/elasticsearch/pull/92528)

Infra/Core

* Add log level for JVM logs [#92382](https://github.com/elastic/elasticsearch/pull/92382)

* Added new field `rollout_duration_seconds` to fleet-actions [#92640](https://github.com/elastic/elasticsearch/pull/92640)

* Bind the readiness service to the wildcard address [#91329](https://github.com/elastic/elasticsearch/pull/91329) (issue: [#90997](https://github.com/elastic/elasticsearch/issues/90997))

* Provide locally mounted secure settings implementation [#93392](https://github.com/elastic/elasticsearch/pull/93392)

Infra/Plugins

* Check stable plugin version at install and load time [#91780](https://github.com/elastic/elasticsearch/pull/91780)

* Example stable plugins with settings [#92334](https://github.com/elastic/elasticsearch/pull/92334)

* Load stable plugins as synthetic modules [#91869](https://github.com/elastic/elasticsearch/pull/91869)

* Settings api for stable plugins [#91467](https://github.com/elastic/elasticsearch/pull/91467)

Infra/Scripting

* Script: Metadata `validateMetadata` optimization [#93333](https://github.com/elastic/elasticsearch/pull/93333)

* Short-circuit painless def equality [#92102](https://github.com/elastic/elasticsearch/pull/92102)

* Use primitive types rather than boxing/unboxing for iterating over primitive arrays from defs [#92025](https://github.com/elastic/elasticsearch/pull/92025)

Ingest Node

* Cache the creation of parsers within DateProcessor [#92880](https://github.com/elastic/elasticsearch/pull/92880)

* Make `GeoIpProcessor` backing database instance pluggable [#93285](https://github.com/elastic/elasticsearch/pull/93285)

Machine Learning

* Add identification of multimodal distribution to anomaly explanations [#2440](https://github.com/elastic/ml-cpp/pull/2440)

* Add the ability to include and exclude values in Frequent items [#92414](https://github.com/elastic/elasticsearch/pull/92414)

* Better error when `aggregate_metric_double` used in scrolling datafeeds [#92232](https://github.com/elastic/elasticsearch/pull/92232) (issue: [#90592](https://github.com/elastic/elasticsearch/issues/90592))

* Implement extension pruning in frequent items to improve runtime [#92322](https://github.com/elastic/elasticsearch/pull/92322)

* Improve `frequent_items` performance using global ordinals [#93304](https://github.com/elastic/elasticsearch/pull/93304)

* Improve anomaly detection results indexing speed [#92417](https://github.com/elastic/elasticsearch/pull/92417)

* Improve frequent items runtime [#93255](https://github.com/elastic/elasticsearch/pull/93255)

* Increase the default timeout for the start trained model deployment API [#92328](https://github.com/elastic/elasticsearch/pull/92328)

* Option to delete user-added annotations for the reset/delete job APIs [#91698](https://github.com/elastic/elasticsearch/pull/91698) (issue: [#74310](https://github.com/elastic/elasticsearch/issues/74310))

* Persist data counts and datafeed timing stats asynchronously [#93000](https://github.com/elastic/elasticsearch/pull/93000)

* Remove the PyTorch inference work queue as now handled in Elasticsearch [#2456](https://github.com/elastic/ml-cpp/pull/2456)

* Text Embedding search [#93531](https://github.com/elastic/elasticsearch/pull/93531)

* Upgrade PyTorch to version 1.13.1 [#2430](https://github.com/elastic/ml-cpp/pull/2430)

Mapping

* Switch to Lucene’s new `IntField/LongField/FloatField/DoubleField` [#93165](https://github.com/elastic/elasticsearch/pull/93165)

Monitoring

* Add kibana.stats.elasticsearch_client stats to the monitoring index templates. [#91508](https://github.com/elastic/elasticsearch/pull/91508)

* Add monitoring mappings for es ingest metricset [#92950](https://github.com/elastic/elasticsearch/pull/92950)

Network

* Deserialize responses on the handling thread-pool [#91367](https://github.com/elastic/elasticsearch/pull/91367)

Performance

* Add vector distance scoring to micro benchmarks [#92340](https://github.com/elastic/elasticsearch/pull/92340)

Query Languages

* Introduce parameterized rule and executor [#92428](https://github.com/elastic/elasticsearch/pull/92428)

Recovery

* Make clean up files step configurable for peer-recovery of replicas [#92490](https://github.com/elastic/elasticsearch/pull/92490)

Search

* Access term dictionary more efficiently [#92269](https://github.com/elastic/elasticsearch/pull/92269)

* Add `term` query support to `rank_features` mapped field [#93247](https://github.com/elastic/elasticsearch/pull/93247)

* Add new `query_vector_builder` option to knn search clause [#93331](https://github.com/elastic/elasticsearch/pull/93331)

* Add profiling plugin [#91640](https://github.com/elastic/elasticsearch/pull/91640)

* Enable profiling plugin by default [#92787](https://github.com/elastic/elasticsearch/pull/92787)

* Get stackframes and executables more concurrently [#93559](https://github.com/elastic/elasticsearch/pull/93559)

* Improve the false positive rate of the bloom filter by setting 7 hash functions [#93283](https://github.com/elastic/elasticsearch/pull/93283)

* Increase the number of threads of GET threadpool [#92309](https://github.com/elastic/elasticsearch/pull/92309)

* Instrument Weight#count in ProfileWeight [#85656](https://github.com/elastic/elasticsearch/pull/85656) (issue: [#85203](https://github.com/elastic/elasticsearch/issues/85203))

* Reduce memory usage of match all bitset [#92777](https://github.com/elastic/elasticsearch/pull/92777)

* Runtime fields to optionally ignore script errors [#92380](https://github.com/elastic/elasticsearch/pull/92380)

* Speed up retrieval of data for flamegraphs [#93448](https://github.com/elastic/elasticsearch/pull/93448)

* Support retrieving inlined stack frames [#92863](https://github.com/elastic/elasticsearch/pull/92863)

* [Profiling] Reduce GC pressure [#93590](https://github.com/elastic/elasticsearch/pull/93590)

Security

* Configurable retention period for invalidated or expired API keys [#92219](https://github.com/elastic/elasticsearch/pull/92219)

* Record timestamp on API key invalidation [#91873](https://github.com/elastic/elasticsearch/pull/91873)

Snapshot/Restore

* Make `RecoveryPlannerService` optional [#92489](https://github.com/elastic/elasticsearch/pull/92489)

TSDB

* Enable bloom filter for `_id` field in tsdb indices [#92115](https://github.com/elastic/elasticsearch/pull/92115)

* Improve downsampling performance by removing map lookups [#92494](https://github.com/elastic/elasticsearch/pull/92494) (issue: [#90226](https://github.com/elastic/elasticsearch/issues/90226))

* Minor TSDB parsing speedup [#92276](https://github.com/elastic/elasticsearch/pull/92276)

* Skip duplicate checks on segments that don’t contain the document’s timestamp [#92456](https://github.com/elastic/elasticsearch/pull/92456)

* Support `fields` in synthetic source in last cases [#91595](https://github.com/elastic/elasticsearch/pull/91595)

Task Management

* `TransportGetTaskAction:` Wait for the task asynchronously [#93375](https://github.com/elastic/elasticsearch/pull/93375)

* `TransportListTaskAction:` wait for tasks to finish asynchronously [#90977](https://github.com/elastic/elasticsearch/pull/90977) (issue: [#89564](https://github.com/elastic/elasticsearch/issues/89564))

Transform

* Add from parameter to Transform Start API [#91116](https://github.com/elastic/elasticsearch/pull/91116) (issue: [#88646](https://github.com/elastic/elasticsearch/issues/88646))

* Support "offset" parameter in `DateHistogramGroupSource` [#93203](https://github.com/elastic/elasticsearch/pull/93203)

* Trigger state persistence based on time [#93221](https://github.com/elastic/elasticsearch/pull/93221)

Vector Search

* Allow `null` to be provided for `dense_vector` field values [#93388](https://github.com/elastic/elasticsearch/pull/93388)

* Allow more than one KNN search clause [#92118](https://github.com/elastic/elasticsearch/pull/92118) (issue: [#91187](https://github.com/elastic/elasticsearch/issues/91187))

Watcher

* Add ability for Watcher’s webhook actions to send additional header [#93426](https://github.com/elastic/elasticsearch/pull/93426)

### New features

Distributed

* Secure settings that can fall back to yml in Stateless [#91925](https://github.com/elastic/elasticsearch/pull/91925)

Geo

* Geohex aggregation on `geo_shape` field [#91956](https://github.com/elastic/elasticsearch/pull/91956) (issue: [#90163](https://github.com/elastic/elasticsearch/issues/90163))

* Support geo_grid ingest processor [#93370](https://github.com/elastic/elasticsearch/pull/93370) (issue: [#92473](https://github.com/elastic/elasticsearch/issues/92473))

Health

* The Health API is now generally available [#92879](https://github.com/elastic/elasticsearch/pull/92879)

* [HealthAPI] Add size parameter that controls the number of affected resources returned [#92399](https://github.com/elastic/elasticsearch/pull/92399) (issue: [#91930](https://github.com/elastic/elasticsearch/issues/91930))

* [HealthAPI] Add support for the FEATURE_STATE affected resource [#92296](https://github.com/elastic/elasticsearch/pull/92296) (issue: [#91353](https://github.com/elastic/elasticsearch/issues/91353))

Infra/Plugins

* [Fleet] Add files and files data index templates and ILM policies [#91413](https://github.com/elastic/elasticsearch/pull/91413)

Ingest Node

* Redact Ingest Processor [#92951](https://github.com/elastic/elasticsearch/pull/92951)

Machine Learning

* Make `frequent_item_sets` aggregation GA [#93421](https://github.com/elastic/elasticsearch/pull/93421)

* Make native inference generally available [#92213](https://github.com/elastic/elasticsearch/pull/92213)

TSDB

* Add a TSDB rate aggregation [#90447](https://github.com/elastic/elasticsearch/pull/90447)

* Downsampling GA [#92913](https://github.com/elastic/elasticsearch/pull/92913)

* Release time_series and rate (on counter fields) aggegations as tech preview [#93546](https://github.com/elastic/elasticsearch/pull/93546)

* Time series (TSDS) GA [#91519](https://github.com/elastic/elasticsearch/pull/91519)

Transform

* Transform _schedule_now API [#92948](https://github.com/elastic/elasticsearch/pull/92948) (issue: [#44722](https://github.com/elastic/elasticsearch/issues/44722))

### Upgrades

Infra/Core

* Align all usages of Jackson to be 2.14.2 [#93438](https://github.com/elastic/elasticsearch/pull/93438)

Ingest Node

* Upgrading tika to 2.6.0 [#92104](https://github.com/elastic/elasticsearch/pull/92104)

Network

* Upgrade to Netty 4.1.85 [#91846](https://github.com/elastic/elasticsearch/pull/91846)

* Upgrade to Netty 4.1.86 [#92587](https://github.com/elastic/elasticsearch/pull/92587)

Query Languages

* Upgrade antlr to 4.11.1 for ql, eql and sql [#93238](https://github.com/elastic/elasticsearch/pull/93238)

Search

* Upgrade to Lucene 9.5.0 [#93385](https://github.com/elastic/elasticsearch/pull/93385)

* Upgrade to lucene-9.5.0-snapshot-d19c3e2e0ed [#92957](https://github.com/elastic/elasticsearch/pull/92957)

Snapshot/Restore

* Align all usages of protobuf to be 3.21.9 [#92123](https://github.com/elastic/elasticsearch/pull/92123)

* Bump reactor netty version [#92457](https://github.com/elastic/elasticsearch/pull/92457)

* Consolidate google-oauth-client to latest version [#91722](https://github.com/elastic/elasticsearch/pull/91722)