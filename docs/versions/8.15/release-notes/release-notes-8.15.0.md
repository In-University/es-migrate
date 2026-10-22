**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.15.0

Also see [Breaking changes in 8.15](migrating-8.15.html#breaking-changes-8.15).

### Known issues

* The `pytorch_inference` process used to run Machine Learning models can consume large amounts of memory.
In environments where the available memory is limited, the OS Out of Memory Killer will kill the `pytorch_inference`
process to reclaim memory. This can cause inference requests to fail.
Elasticsearch will automatically restart the `pytorch_inference` process
after it is killed up to four times in 24 hours. (issue: [#110530](https://github.com/elastic/elasticsearch/issues/110530))

* Pipeline aggregations under `time_series` and `categorize_text` aggregations are never
returned (issue: [#111679](https://github.com/elastic/elasticsearch/issues/111679))

* Elasticsearch will not start on Windows machines if
[`bootstrap.memory_lock` is set to `true`]([https://www.elastic.co/guide/en/elasticsearch/reference/current/setup-configuration-memory.html#bootstrap-memory_lock](/guide/en/elasticsearch/reference/current/setup-configuration-memory.html#bootstrap-memory_lock)).
Either downgrade to an earlier version, upgrade to 8.15.1, or else follow the
recommendation in the manual to entirely disable swap instead of using the
memory lock feature (issue: [#111847](https://github.com/elastic/elasticsearch/issues/111847))

* The `took` field of the response to the [Bulk](docs-bulk.html) API is incorrect and may be rather large. Clients which
[incorrectly](api-conventions.html#api-conventions-number-values) assume that this value will be within a particular range (e.g. that it fits into a 32-bit
signed integer) may encounter errors (issue: [#111854](https://github.com/elastic/elasticsearch/issues/111854))

* Elasticsearch will not start if custom role mappings are configured using the
`xpack.security.authc.realms.*.files.role_mapping` configuration option. As a workaround, custom role mappings
can be configured using the [REST API](/guide/en/elasticsearch/reference/current/security-api-put-role-mapping.html) (issue: [#112503](https://github.com/elastic/elasticsearch/issues/112503))

* ES|QL queries can lead to node crashes due to Out Of Memory errors when:

* Multiple indices match the query pattern

* These indices have many conflicting field mappings

* Many of those fields are included in the request
These issues deplete heap memory, increasing the likelihood of OOM errors. (issue: [#111964](https://github.com/elastic/elasticsearch/issues/111964), [#111358](https://github.com/elastic/elasticsearch/issues/111358)).
In Kibana, you might indirectly execute these queries when using Discover, or adding a Field Statistics panel to a dashboard.

To work around this issue, you have a number of options:

* Downgrade to an earlier version

* Upgrade to 8.15.2 upon release

* Follow the instructions to
[disable ES|QL queries in Kibana](esql-kibana.html#esql-kibana-enable)

* Change the default data view in Discover to a smaller set of indices and/or one with fewer mapping conflicts.

* Synthetic source bug. Synthetic source may fail generating the _source at runtime, causing failures in get APIs or
partial failures in the search APIs. The result is that for the affected documents the _source can’t be retrieved.
There is no workaround and the only option to is to upgrade to 8.15.2 when released.

If you use synthetic source then you may be affected by this bug if the following is true:
**If you have more fields then the `index.mapping.total_fields.limit` setting allows.** If you use dynamic mappings and the `index.mapping.total_fields.ignore_dynamic_beyond_limit` setting is enabled.

### Breaking changes

Cluster Coordination

* Interpret `?timeout=-1` as infinite ack timeout [#107675](https://github.com/elastic/elasticsearch/pull/107675)

Inference API

* Replace `model_id` with `inference_id` in GET inference API [#111366](https://github.com/elastic/elasticsearch/pull/111366)

Rollup

* Disallow new rollup jobs in clusters with no rollup usage [#108624](https://github.com/elastic/elasticsearch/pull/108624) (issue: [#108381](https://github.com/elastic/elasticsearch/issues/108381))

Search

* Change `skip_unavailable` remote cluster setting default value to true [#105792](https://github.com/elastic/elasticsearch/pull/105792)

### Bug fixes

Aggregations

* Don’t sample calls to `ReduceContext#consumeBucketsAndMaybeBreak` ins `InternalDateHistogram` and `InternalHistogram` during reduction [#110186](https://github.com/elastic/elasticsearch/pull/110186)

* Fix `ClassCastException` in Significant Terms [#108429](https://github.com/elastic/elasticsearch/pull/108429) (issue: [#108427](https://github.com/elastic/elasticsearch/issues/108427))

* Run terms concurrently when cardinality is only lower than shard size [#110369](https://github.com/elastic/elasticsearch/pull/110369) (issue: [#105505](https://github.com/elastic/elasticsearch/issues/105505))

Allocation

* Fix misc trappy allocation API timeouts [#109241](https://github.com/elastic/elasticsearch/pull/109241)

* Fix trappy timeout in allocation explain API [#109240](https://github.com/elastic/elasticsearch/pull/109240)

Analysis

* Correct positioning for unique token filter [#109395](https://github.com/elastic/elasticsearch/pull/109395)

Authentication

* Add comma before charset parameter in WWW-Authenticate response header [#110906](https://github.com/elastic/elasticsearch/pull/110906)

* Avoid NPE if `users_roles` file does not exist [#109606](https://github.com/elastic/elasticsearch/pull/109606)

* Improve security-crypto threadpool overflow handling [#111369](https://github.com/elastic/elasticsearch/pull/111369)

Authorization

* Fix trailing slash in `security.put_privileges` specification [#110177](https://github.com/elastic/elasticsearch/pull/110177)

* Fixes cluster state-based role mappings not recovered from disk [#109167](https://github.com/elastic/elasticsearch/pull/109167)

* Handle unmatching remote cluster wildcards properly for `IndicesRequest.SingleIndexNoWildcards` requests [#109185](https://github.com/elastic/elasticsearch/pull/109185)

Autoscaling

* Expose `?master_timeout` in autoscaling APIs [#108759](https://github.com/elastic/elasticsearch/pull/108759)

CRUD

* Update checkpoints after post-replication actions, even on failure [#109908](https://github.com/elastic/elasticsearch/pull/109908)

Cluster Coordination

* Deserialize publish requests on generic thread-pool [#108814](https://github.com/elastic/elasticsearch/pull/108814) (issue: [#106352](https://github.com/elastic/elasticsearch/issues/106352))

* Fail cluster state API if blocked [#109618](https://github.com/elastic/elasticsearch/pull/109618) (issue: [#107503](https://github.com/elastic/elasticsearch/issues/107503))

* Use `scheduleUnlessShuttingDown` in `LeaderChecker` [#108643](https://github.com/elastic/elasticsearch/pull/108643) (issue: [#108642](https://github.com/elastic/elasticsearch/issues/108642))

Data streams

* Apm-data: set concrete values for `metricset.interval` [#109043](https://github.com/elastic/elasticsearch/pull/109043)

* Ecs@mappings: reduce scope for `ecs_geo_point` [#108349](https://github.com/elastic/elasticsearch/pull/108349) (issue: [#108338](https://github.com/elastic/elasticsearch/issues/108338))

* Include component templates in retention validaiton [#109779](https://github.com/elastic/elasticsearch/pull/109779)

Distributed

* Associate restore snapshot task to parent mount task [#108705](https://github.com/elastic/elasticsearch/pull/108705) (issue: [#105830](https://github.com/elastic/elasticsearch/issues/105830))

* Don’t detect `PlainActionFuture` deadlock on concurrent complete [#110361](https://github.com/elastic/elasticsearch/pull/110361) (issues: [#110181](https://github.com/elastic/elasticsearch/issues/110181), [#110360](https://github.com/elastic/elasticsearch/issues/110360))

* Handle nullable `DocsStats` and `StoresStats` [#109196](https://github.com/elastic/elasticsearch/pull/109196)

Downsampling

* Support flattened fields and multi-fields as dimensions in downsampling [#110066](https://github.com/elastic/elasticsearch/pull/110066) (issue: [#99297](https://github.com/elastic/elasticsearch/issues/99297))

ES|QL

* ESQL: Change "substring" function to not return null on empty string [#109174](https://github.com/elastic/elasticsearch/pull/109174)

* ESQL: Fix Join references [#109989](https://github.com/elastic/elasticsearch/pull/109989)

* ESQL: Fix LOOKUP attribute shadowing [#109807](https://github.com/elastic/elasticsearch/pull/109807) (issue: [#109392](https://github.com/elastic/elasticsearch/issues/109392))

* ESQL: Fix Max doubles bug with negatives and add tests for Max and Min [#110586](https://github.com/elastic/elasticsearch/pull/110586)

* ESQL: Fix `IpPrefix` function not handling correctly `ByteRefs` [#109205](https://github.com/elastic/elasticsearch/pull/109205) (issue: [#109198](https://github.com/elastic/elasticsearch/issues/109198))

* ESQL: Fix equals `hashCode` for functions [#107947](https://github.com/elastic/elasticsearch/pull/107947) (issue: [#104393](https://github.com/elastic/elasticsearch/issues/104393))

* ESQL: Fix variable shadowing when pushing down past Project [#108360](https://github.com/elastic/elasticsearch/pull/108360) (issue: [#108008](https://github.com/elastic/elasticsearch/issues/108008))

* ESQL: Validate unique plan attribute names [#110488](https://github.com/elastic/elasticsearch/pull/110488) (issue: [#110541](https://github.com/elastic/elasticsearch/issues/110541))

* ESQL: change from quoting from backtick to quote [#108395](https://github.com/elastic/elasticsearch/pull/108395)

* ESQL: make named params objects truly per request [#110046](https://github.com/elastic/elasticsearch/pull/110046) (issue: [#110028](https://github.com/elastic/elasticsearch/issues/110028))

* ES|QL: Fix DISSECT that overwrites input [#110201](https://github.com/elastic/elasticsearch/pull/110201) (issue: [#110184](https://github.com/elastic/elasticsearch/issues/110184))

* ES|QL: limit query depth to 500 levels [#108089](https://github.com/elastic/elasticsearch/pull/108089) (issue: [#107752](https://github.com/elastic/elasticsearch/issues/107752))

* ES|QL: reduce max expression depth to 400 [#111186](https://github.com/elastic/elasticsearch/pull/111186) (issue: [#109846](https://github.com/elastic/elasticsearch/issues/109846))

* Fix ST_DISTANCE Lucene push-down for complex predicates [#110391](https://github.com/elastic/elasticsearch/pull/110391) (issue: [#110349](https://github.com/elastic/elasticsearch/issues/110349))

* Fix `ClassCastException` with MV_EXPAND on missing field [#110096](https://github.com/elastic/elasticsearch/pull/110096) (issue: [#109974](https://github.com/elastic/elasticsearch/issues/109974))

* Fix bug in union-types with type-casting in grouping key of STATS [#110476](https://github.com/elastic/elasticsearch/pull/110476) (issues: [#109922](https://github.com/elastic/elasticsearch/issues/109922), [#110477](https://github.com/elastic/elasticsearch/issues/110477))

* Fix for union-types for multiple columns with the same name [#110793](https://github.com/elastic/elasticsearch/pull/110793) (issues: [#110490](https://github.com/elastic/elasticsearch/issues/110490), [#109916](https://github.com/elastic/elasticsearch/issues/109916))

* [ESQL] Count_distinct(_source) should return a 400 [#110824](https://github.com/elastic/elasticsearch/pull/110824)

* [ESQL] Fix parsing of large magnitude negative numbers [#110665](https://github.com/elastic/elasticsearch/pull/110665) (issue: [#104323](https://github.com/elastic/elasticsearch/issues/104323))

* [ESQL] Migrate `SimplifyComparisonArithmetics` optimization [#109256](https://github.com/elastic/elasticsearch/pull/109256) (issues: [#108388](https://github.com/elastic/elasticsearch/issues/108388), [#108743](https://github.com/elastic/elasticsearch/issues/108743))

Engine

* Async close of `IndexShard` [#108145](https://github.com/elastic/elasticsearch/pull/108145)

Highlighting

* Fix issue with returning incomplete fragment for plain highlighter [#110707](https://github.com/elastic/elasticsearch/pull/110707)

ILM+SLM

* Allow `read_slm` to call GET /_slm/status [#108333](https://github.com/elastic/elasticsearch/pull/108333)

Indices APIs

* Create a new `NodeRequest` for every `NodesDataTiersUsageTransport` use [#108379](https://github.com/elastic/elasticsearch/pull/108379)

Infra/Core

* Add a cluster listener to fix missing node features after upgrading from a version prior to 8.13 [#110710](https://github.com/elastic/elasticsearch/pull/110710) (issue: [#109254](https://github.com/elastic/elasticsearch/issues/109254))

* Add bounds checking to parsing ISO8601 timezone offset values [#108672](https://github.com/elastic/elasticsearch/pull/108672)

* Fix native preallocate to actually run [#110851](https://github.com/elastic/elasticsearch/pull/110851)

* Ignore additional cpu.stat fields [#108019](https://github.com/elastic/elasticsearch/pull/108019) (issue: [#107983](https://github.com/elastic/elasticsearch/issues/107983))

* Specify parse index when error occurs on multiple datetime parses [#108607](https://github.com/elastic/elasticsearch/pull/108607)

Infra/Metrics

* Provide document size reporter with `MapperService` [#109794](https://github.com/elastic/elasticsearch/pull/109794)

Infra/Node Lifecycle

* Expose `?master_timeout` on get-shutdown API [#108886](https://github.com/elastic/elasticsearch/pull/108886)

* Fix serialization of put-shutdown request [#107862](https://github.com/elastic/elasticsearch/pull/107862) (issue: [#107857](https://github.com/elastic/elasticsearch/issues/107857))

* Support wait indefinitely for search tasks to complete on node shutdown [#107426](https://github.com/elastic/elasticsearch/pull/107426)

Infra/REST API

* Add some missing timeout params to REST API specs [#108761](https://github.com/elastic/elasticsearch/pull/108761)

* Consider `error_trace` supported by all endpoints [#109613](https://github.com/elastic/elasticsearch/pull/109613) (issue: [#109612](https://github.com/elastic/elasticsearch/issues/109612))

Ingest Node

* Fix Dissect with leading non-ascii characters [#111184](https://github.com/elastic/elasticsearch/pull/111184)

* Fix enrich policy runner exception handling on empty segments response [#111290](https://github.com/elastic/elasticsearch/pull/111290)

* GeoIP tasks should wait longer for master [#108410](https://github.com/elastic/elasticsearch/pull/108410)

* Removing the use of Stream::peek from `GeoIpDownloader::cleanDatabases` [#110666](https://github.com/elastic/elasticsearch/pull/110666)

* Simulate should succeed if `ignore_missing_pipeline` [#108106](https://github.com/elastic/elasticsearch/pull/108106) (issue: [#107314](https://github.com/elastic/elasticsearch/issues/107314))

Machine Learning

* Allow deletion of the ELSER inference service when reference in ingest [#108146](https://github.com/elastic/elasticsearch/pull/108146)

* Avoid `InferenceRunner` deadlock [#109551](https://github.com/elastic/elasticsearch/pull/109551)

* Correctly handle duplicate model ids for the `_cat` trained models api and usage statistics [#109126](https://github.com/elastic/elasticsearch/pull/109126)

* Do not use global ordinals strategy if the leaf reader context cannot be obtained [#108459](https://github.com/elastic/elasticsearch/pull/108459)

* Fix NPE in trained model assignment updater [#108942](https://github.com/elastic/elasticsearch/pull/108942)

* Fix serialising inference delete response [#109384](https://github.com/elastic/elasticsearch/pull/109384)

* Fix "stack use after scope" memory error [#2673](https://github.com/elastic/ml-cpp/pull/2673)

* Fix trailing slash in `ml.get_categories` specification [#110146](https://github.com/elastic/elasticsearch/pull/110146)

* Handle any exception thrown by inference [#2680](https://github.com/elastic/ml-cpp/pull/2680)

* Increase response size limit for batched requests [#110112](https://github.com/elastic/elasticsearch/pull/110112)

* Offload request to generic threadpool [#109104](https://github.com/elastic/elasticsearch/pull/109104) (issue: [#109100](https://github.com/elastic/elasticsearch/issues/109100))

* Propagate accurate deployment timeout [#109534](https://github.com/elastic/elasticsearch/pull/109534) (issue: [#109407](https://github.com/elastic/elasticsearch/issues/109407))

* Refactor TextEmbeddingResults to use primitives rather than objects [#108161](https://github.com/elastic/elasticsearch/pull/108161)

* Require question to be non-null in `QuestionAnsweringConfig` [#107972](https://github.com/elastic/elasticsearch/pull/107972)

* Start Trained Model Deployment API request query params now override body params [#109487](https://github.com/elastic/elasticsearch/pull/109487)

* Suppress deprecation warnings from ingest pipelines when deleting trained model [#108679](https://github.com/elastic/elasticsearch/pull/108679) (issue: [#105004](https://github.com/elastic/elasticsearch/issues/105004))

* Use default translog durability on AD results index [#108999](https://github.com/elastic/elasticsearch/pull/108999)

* Use the multi node routing action for internal inference services [#109358](https://github.com/elastic/elasticsearch/pull/109358)

* [Inference API] Extract optional long instead of integer in `RateLimitSettings#of` [#108602](https://github.com/elastic/elasticsearch/pull/108602)

* [Inference API] Fix serialization for inference delete endpoint response [#110431](https://github.com/elastic/elasticsearch/pull/110431)

* [Inference API] Replace `model_id` with `inference_id` in inference API except when stored [#111366](https://github.com/elastic/elasticsearch/pull/111366)

Mapping

* Fix off by one error when handling null values in range fields [#107977](https://github.com/elastic/elasticsearch/pull/107977) (issue: [#107282](https://github.com/elastic/elasticsearch/issues/107282))

* Limit number of synonym rules that can be created [#109981](https://github.com/elastic/elasticsearch/pull/109981) (issue: [#108785](https://github.com/elastic/elasticsearch/issues/108785))

* Propagate mapper builder context flags across nested mapper builder context creation [#109963](https://github.com/elastic/elasticsearch/pull/109963)

* `DenseVectorFieldMapper` fixed typo [#108065](https://github.com/elastic/elasticsearch/pull/108065)

Network

* Use proper executor for failing requests when connection closes [#109236](https://github.com/elastic/elasticsearch/pull/109236) (issue: [#109225](https://github.com/elastic/elasticsearch/issues/109225))

* `NoSuchRemoteClusterException` should not be thrown when a remote is configured [#107435](https://github.com/elastic/elasticsearch/pull/107435) (issue: [#107381](https://github.com/elastic/elasticsearch/issues/107381))

Packaging

* Adding override for lintian false positive on `libvec.so` [#108521](https://github.com/elastic/elasticsearch/pull/108521) (issue: [#108514](https://github.com/elastic/elasticsearch/issues/108514))

Ranking

* Fix score count validation in reranker response [#111424](https://github.com/elastic/elasticsearch/pull/111424) (issue: [#111202](https://github.com/elastic/elasticsearch/issues/111202))

Rollup

* Fix trailing slash in two rollup specifications [#110176](https://github.com/elastic/elasticsearch/pull/110176)

Search

* Adding score from `RankDoc` to `SearchHit` [#108870](https://github.com/elastic/elasticsearch/pull/108870)

* Better handling of multiple rescorers clauses with LTR [#109071](https://github.com/elastic/elasticsearch/pull/109071)

* Correct query profiling for conjunctions [#108122](https://github.com/elastic/elasticsearch/pull/108122) (issue: [#108116](https://github.com/elastic/elasticsearch/issues/108116))

* Fix `DecayFunctions'` `toString` [#107415](https://github.com/elastic/elasticsearch/pull/107415) (issue: [#100870](https://github.com/elastic/elasticsearch/issues/100870))

* Fix leak in collapsing search results [#110927](https://github.com/elastic/elasticsearch/pull/110927)

* Fork freeing search/scroll contexts to GENERIC pool [#109481](https://github.com/elastic/elasticsearch/pull/109481)

Security

* Add permission to secure access to certain config files [#107827](https://github.com/elastic/elasticsearch/pull/107827)

* Add permission to secure access to certain config files specified by settings [#108895](https://github.com/elastic/elasticsearch/pull/108895)

* Fix trappy timeouts in security settings APIs [#109233](https://github.com/elastic/elasticsearch/pull/109233)

Snapshot/Restore

* Stricter failure handling in multi-repo get-snapshots request handling [#107191](https://github.com/elastic/elasticsearch/pull/107191)

TSDB

* Sort time series indices by time range in `GetDataStreams` API [#107967](https://github.com/elastic/elasticsearch/pull/107967) (issue: [#102088](https://github.com/elastic/elasticsearch/issues/102088))

Transform

* Always pick the user `maxPageSize` value [#109876](https://github.com/elastic/elasticsearch/pull/109876) (issue: [#109844](https://github.com/elastic/elasticsearch/issues/109844))

* Exit gracefully when deleted [#107917](https://github.com/elastic/elasticsearch/pull/107917) (issue: [#107266](https://github.com/elastic/elasticsearch/issues/107266))

* Fix NPE during destination index creation [#108891](https://github.com/elastic/elasticsearch/pull/108891) (issue: [#108890](https://github.com/elastic/elasticsearch/issues/108890))

* Forward `indexServiceSafe` exception to listener [#108517](https://github.com/elastic/elasticsearch/pull/108517) (issue: [#108418](https://github.com/elastic/elasticsearch/issues/108418))

* Halt Indexer on Stop/Abort API [#107792](https://github.com/elastic/elasticsearch/pull/107792)

* Handle `IndexNotFoundException` [#108394](https://github.com/elastic/elasticsearch/pull/108394) (issue: [#107263](https://github.com/elastic/elasticsearch/issues/107263))

* Prevent concurrent jobs during cleanup [#109047](https://github.com/elastic/elasticsearch/pull/109047)

* Redirect `VersionConflict` to reset code [#108070](https://github.com/elastic/elasticsearch/pull/108070)

* Reset max page size to settings value [#109449](https://github.com/elastic/elasticsearch/pull/109449) (issue: [#109308](https://github.com/elastic/elasticsearch/issues/109308))

Vector Search

* Ensure vector similarity correctly limits `inner_hits` returned for nested kNN [#111363](https://github.com/elastic/elasticsearch/pull/111363) (issue: [#111093](https://github.com/elastic/elasticsearch/issues/111093))

* Ensure we return non-negative scores when scoring scalar dot-products [#108522](https://github.com/elastic/elasticsearch/pull/108522)

Watcher

* Avoiding running watch jobs in TickerScheduleTriggerEngine if it is paused [#110061](https://github.com/elastic/elasticsearch/pull/110061) (issue: [#105933](https://github.com/elastic/elasticsearch/issues/105933))

### Deprecations

ILM+SLM

* Deprecate using slm privileges to access ilm [#110540](https://github.com/elastic/elasticsearch/pull/110540)

Infra/Settings

* `ParseHeapRatioOrDeprecatedByteSizeValue` for `indices.breaker.total.limit` [#110236](https://github.com/elastic/elasticsearch/pull/110236)

Machine Learning

* Deprecate `text_expansion` and `weighted_tokens` queries [#109880](https://github.com/elastic/elasticsearch/pull/109880)

### Enhancements

Aggregations

* Aggs: Scripted metric allow list [#109444](https://github.com/elastic/elasticsearch/pull/109444)

* Enable inter-segment concurrency for low cardinality numeric terms aggs [#108306](https://github.com/elastic/elasticsearch/pull/108306)

* Increase size of big arrays only when there is an actual value in the aggregators [#107764](https://github.com/elastic/elasticsearch/pull/107764)

* Increase size of big arrays only when there is an actual value in the aggregators (Analytics module) [#107813](https://github.com/elastic/elasticsearch/pull/107813)

* Optimise `BinaryRangeAggregator` for single value fields [#108016](https://github.com/elastic/elasticsearch/pull/108016)

* Optimise cardinality aggregations for single value fields [#107892](https://github.com/elastic/elasticsearch/pull/107892)

* Optimise composite aggregations for single value fields [#107897](https://github.com/elastic/elasticsearch/pull/107897)

* Optimise few metric aggregations for single value fields [#107832](https://github.com/elastic/elasticsearch/pull/107832)

* Optimise histogram aggregations for single value fields [#107893](https://github.com/elastic/elasticsearch/pull/107893)

* Optimise multiterms aggregation for single value fields [#107937](https://github.com/elastic/elasticsearch/pull/107937)

* Optimise terms aggregations for single value fields [#107930](https://github.com/elastic/elasticsearch/pull/107930)

* Speed up collecting zero document string terms [#110922](https://github.com/elastic/elasticsearch/pull/110922)

Allocation

* Log shard movements [#105829](https://github.com/elastic/elasticsearch/pull/105829)

* Support effective watermark thresholds in node stats API [#107244](https://github.com/elastic/elasticsearch/pull/107244) (issue: [#106676](https://github.com/elastic/elasticsearch/issues/106676))

Application

* Add Create or update query rule API call [#109042](https://github.com/elastic/elasticsearch/pull/109042)

* Rename rule query and add support for multiple rulesets [#108831](https://github.com/elastic/elasticsearch/pull/108831)

* Support multiple associated groups for TopN [#108409](https://github.com/elastic/elasticsearch/pull/108409) (issue: [#108018](https://github.com/elastic/elasticsearch/issues/108018))

* [Connector API] Change `UpdateConnectorFiltering` API to have better defaults [#108612](https://github.com/elastic/elasticsearch/pull/108612)

Authentication

* Expose API Key cache metrics [#109078](https://github.com/elastic/elasticsearch/pull/109078)

Authorization

* Cluster state role mapper file settings service [#107886](https://github.com/elastic/elasticsearch/pull/107886)

* Cluster-state based Security role mapper [#107410](https://github.com/elastic/elasticsearch/pull/107410)

* Introduce role description field [#107088](https://github.com/elastic/elasticsearch/pull/107088)

* [Osquery] Extend `kibana_system` role with an access to new `osquery_manager` index [#108849](https://github.com/elastic/elasticsearch/pull/108849)

Data streams

* Add metrics@custom component template to metrics-**-** index template [#109540](https://github.com/elastic/elasticsearch/pull/109540) (issue: [#109475](https://github.com/elastic/elasticsearch/issues/109475))

* Apm-data: enable plugin by default [#108860](https://github.com/elastic/elasticsearch/pull/108860)

* Apm-data: ignore malformed fields, and too many dynamic fields [#108444](https://github.com/elastic/elasticsearch/pull/108444)

* Apm-data: improve default pipeline performance [#108396](https://github.com/elastic/elasticsearch/pull/108396) (issue: [#108290](https://github.com/elastic/elasticsearch/issues/108290))

* Apm-data: improve indexing resilience [#108227](https://github.com/elastic/elasticsearch/pull/108227)

* Apm-data: increase priority above Fleet templates [#108885](https://github.com/elastic/elasticsearch/pull/108885)

* Apm-data: increase version for templates [#108340](https://github.com/elastic/elasticsearch/pull/108340)

* Apm-data: set codec: best_compression for logs-apm.* data streams [#108862](https://github.com/elastic/elasticsearch/pull/108862)

* Remove `default_field: message` from metrics index templates [#110651](https://github.com/elastic/elasticsearch/pull/110651)

Distributed

* Add `wait_for_completion` parameter to delete snapshot request [#109462](https://github.com/elastic/elasticsearch/pull/109462) (issue: [#101300](https://github.com/elastic/elasticsearch/issues/101300))

* Improve mechanism for extracting the result of a `PlainActionFuture` [#110019](https://github.com/elastic/elasticsearch/pull/110019) (issue: [#108125](https://github.com/elastic/elasticsearch/issues/108125))

ES|QL

* Add `BlockHash` for 3 `BytesRefs` [#108165](https://github.com/elastic/elasticsearch/pull/108165)

* Allow `LuceneSourceOperator` to early terminate [#108820](https://github.com/elastic/elasticsearch/pull/108820)

* Check if `CsvTests` required capabilities exist [#108684](https://github.com/elastic/elasticsearch/pull/108684)

* ESQL: Add aggregates node level reduction [#107876](https://github.com/elastic/elasticsearch/pull/107876)

* ESQL: Add more time span units [#108300](https://github.com/elastic/elasticsearch/pull/108300)

* ESQL: Implement LOOKUP, an "inline" enrich [#107987](https://github.com/elastic/elasticsearch/pull/107987) (issue: [#107306](https://github.com/elastic/elasticsearch/issues/107306))

* ESQL: Renamed `TopList` to Top [#110347](https://github.com/elastic/elasticsearch/pull/110347)

* ESQL: Union Types Support [#107545](https://github.com/elastic/elasticsearch/pull/107545) (issue: [#100603](https://github.com/elastic/elasticsearch/issues/100603))

* ESQL: add REPEAT string function [#109220](https://github.com/elastic/elasticsearch/pull/109220)

* ES|QL Add primitive float support to the Compute Engine [#109746](https://github.com/elastic/elasticsearch/pull/109746) (issue: [#109178](https://github.com/elastic/elasticsearch/issues/109178))

* ES|QL Add primitive float variants of all aggregators to the compute engine [#109781](https://github.com/elastic/elasticsearch/pull/109781)

* ES|QL: vectorize eval [#109332](https://github.com/elastic/elasticsearch/pull/109332)

* Optimize ST_DISTANCE filtering with Lucene circle intersection query [#110102](https://github.com/elastic/elasticsearch/pull/110102) (issue: [#109972](https://github.com/elastic/elasticsearch/issues/109972))

* Optimize for single value in ordinals grouping [#108118](https://github.com/elastic/elasticsearch/pull/108118)

* Rewrite away type converting functions that do not convert types [#108713](https://github.com/elastic/elasticsearch/pull/108713) (issue: [#107716](https://github.com/elastic/elasticsearch/issues/107716))

* ST_DISTANCE Function [#108764](https://github.com/elastic/elasticsearch/pull/108764) (issue: [#108212](https://github.com/elastic/elasticsearch/issues/108212))

* Support metrics counter types in ESQL [#107877](https://github.com/elastic/elasticsearch/pull/107877)

* [ESQL] CBRT function [#108574](https://github.com/elastic/elasticsearch/pull/108574)

* [ES|QL] Convert string to datetime when the other size of an arithmetic operator is `date_period` or `time_duration` [#108455](https://github.com/elastic/elasticsearch/pull/108455)

* [ES|QL] Support Named and Positional Parameters in `EsqlQueryRequest` [#108421](https://github.com/elastic/elasticsearch/pull/108421) (issue: [#107029](https://github.com/elastic/elasticsearch/issues/107029))

* [ES|QL] `weighted_avg` [#109993](https://github.com/elastic/elasticsearch/pull/109993)

Engine

* Drop shards close timeout when stopping node. [#107978](https://github.com/elastic/elasticsearch/pull/107978) (issue: [#107938](https://github.com/elastic/elasticsearch/issues/107938))

* Update translog `writeLocation` for `flushListener` after commit [#109603](https://github.com/elastic/elasticsearch/pull/109603)

Geo

* Optimize `GeoBounds` and `GeoCentroid` aggregations for single value fields [#107663](https://github.com/elastic/elasticsearch/pull/107663)

Health

* Log details of non-green indicators in `HealthPeriodicLogger` [#108266](https://github.com/elastic/elasticsearch/pull/108266)

Highlighting

* Unified Highlighter to support matched_fields  [#107640](https://github.com/elastic/elasticsearch/pull/107640) (issue: [#5172](https://github.com/elastic/elasticsearch/issues/5172))

Infra/Core

* Add allocation explain output for THROTTLING shards [#109563](https://github.com/elastic/elasticsearch/pull/109563)

* Create custom parser for ISO-8601 datetimes [#106486](https://github.com/elastic/elasticsearch/pull/106486) (issue: [#102063](https://github.com/elastic/elasticsearch/issues/102063))

* Extend ISO8601 datetime parser to specify forbidden fields, allowing it to be used on more formats [#108606](https://github.com/elastic/elasticsearch/pull/108606)

* add Elastic-internal stable bridge api for use by Logstash [#108171](https://github.com/elastic/elasticsearch/pull/108171)

Infra/Metrics

* Add auto-sharding APM metrics [#107593](https://github.com/elastic/elasticsearch/pull/107593)

* Add request metric to `RestController` to track success/failure (by status code) [#109957](https://github.com/elastic/elasticsearch/pull/109957)

* Allow RA metrics to be reported upon parsing completed or accumulated [#108726](https://github.com/elastic/elasticsearch/pull/108726)

* Provide the `DocumentSizeReporter` with index mode [#108947](https://github.com/elastic/elasticsearch/pull/108947)

* Return noop instance `DocSizeObserver` for updates with scripts [#108856](https://github.com/elastic/elasticsearch/pull/108856)

Ingest Node

* Add `continent_code` support to the geoip processor [#108780](https://github.com/elastic/elasticsearch/pull/108780) (issue: [#85820](https://github.com/elastic/elasticsearch/issues/85820))

* Add support for the *Connection Type* database to the geoip processor [#108683](https://github.com/elastic/elasticsearch/pull/108683)

* Add support for the *Domain* database to the geoip processor [#108639](https://github.com/elastic/elasticsearch/pull/108639)

* Add support for the *ISP* database to the geoip processor [#108651](https://github.com/elastic/elasticsearch/pull/108651)

* Adding `hits_time_in_millis` and `misses_time_in_millis` to enrich cache stats [#107579](https://github.com/elastic/elasticsearch/pull/107579)

* Adding `user_type` support for the enterprise database for the geoip processor [#108687](https://github.com/elastic/elasticsearch/pull/108687)

* Adding human readable times to geoip stats [#107647](https://github.com/elastic/elasticsearch/pull/107647)

* Include doc size info in ingest stats [#107240](https://github.com/elastic/elasticsearch/pull/107240) (issue: [#106386](https://github.com/elastic/elasticsearch/issues/106386))

* Make ingest byte stat names more descriptive [#108786](https://github.com/elastic/elasticsearch/pull/108786)

* Return ingest byte stats even when 0-valued [#108796](https://github.com/elastic/elasticsearch/pull/108796)

* Test pipeline run after reroute [#108693](https://github.com/elastic/elasticsearch/pull/108693)

Logs

* Introduce a node setting controlling the activation of the `logs` index mode in logs@settings component template [#109025](https://github.com/elastic/elasticsearch/pull/109025) (issue: [#108762](https://github.com/elastic/elasticsearch/issues/108762))

* Support index sorting with nested fields [#110251](https://github.com/elastic/elasticsearch/pull/110251) (issue: [#107349](https://github.com/elastic/elasticsearch/issues/107349))

Machine Learning

* Add Anthropic messages integration to Inference API [#109893](https://github.com/elastic/elasticsearch/pull/109893)

* Add `sparse_vector` query [#108254](https://github.com/elastic/elasticsearch/pull/108254)

* Add model download progress to the download task status [#107676](https://github.com/elastic/elasticsearch/pull/107676)

* Add rate limiting support for the Inference API [#107706](https://github.com/elastic/elasticsearch/pull/107706)

* Add the rerank task to the Elasticsearch internal inference service [#108452](https://github.com/elastic/elasticsearch/pull/108452)

* Default the HF service to cosine similarity [#109967](https://github.com/elastic/elasticsearch/pull/109967)

* GA the update trained model action [#108868](https://github.com/elastic/elasticsearch/pull/108868)

* Handle the "JSON memory allocator bytes" field [#109653](https://github.com/elastic/elasticsearch/pull/109653)

* Inference Processor: skip inference when all fields are missing [#108131](https://github.com/elastic/elasticsearch/pull/108131)

* Log 'No statistics at.. ' message as a warning [#2684](https://github.com/elastic/ml-cpp/pull/2684)

* Optimise frequent item sets aggregation for single value fields [#108130](https://github.com/elastic/elasticsearch/pull/108130)

* Sentence Chunker [#110334](https://github.com/elastic/elasticsearch/pull/110334)

* [Inference API] Add Amazon Bedrock Support to Inference API [#110248](https://github.com/elastic/elasticsearch/pull/110248)

* [Inference API] Add Mistral Embeddings Support to Inference API [#109194](https://github.com/elastic/elasticsearch/pull/109194)

* [Inference API] Check for related pipelines on delete inference endpoint [#109123](https://github.com/elastic/elasticsearch/pull/109123)

Mapping

* Add ignored field values to synthetic source [#107567](https://github.com/elastic/elasticsearch/pull/107567)

* Apply FLS to the contents of `IgnoredSourceFieldMapper` [#109931](https://github.com/elastic/elasticsearch/pull/109931)

* Binary field enables doc values by default for index mode with synthe… [#107739](https://github.com/elastic/elasticsearch/pull/107739) (issue: [#107554](https://github.com/elastic/elasticsearch/issues/107554))

* Feature/annotated text store defaults [#107922](https://github.com/elastic/elasticsearch/pull/107922) (issue: [#107734](https://github.com/elastic/elasticsearch/issues/107734))

* Handle `ignore_above` in synthetic source for flattened fields [#110214](https://github.com/elastic/elasticsearch/pull/110214)

* Opt in keyword field into fallback synthetic source if needed [#110016](https://github.com/elastic/elasticsearch/pull/110016)

* Opt in number fields into fallback synthetic source when doc values a… [#110160](https://github.com/elastic/elasticsearch/pull/110160)

* Reflect latest changes in synthetic source documentation [#109501](https://github.com/elastic/elasticsearch/pull/109501)

* Store source for fields in objects with `dynamic` override [#108911](https://github.com/elastic/elasticsearch/pull/108911)

* Store source for nested objects [#108818](https://github.com/elastic/elasticsearch/pull/108818)

* Support synthetic source for `geo_point` when `ignore_malformed` is used [#109651](https://github.com/elastic/elasticsearch/pull/109651)

* Support synthetic source for `scaled_float` and `unsigned_long` when `ignore_malformed` is used [#109506](https://github.com/elastic/elasticsearch/pull/109506)

* Support synthetic source for date fields when `ignore_malformed` is used [#109410](https://github.com/elastic/elasticsearch/pull/109410)

* Support synthetic source together with `ignore_malformed` in histogram fields [#109882](https://github.com/elastic/elasticsearch/pull/109882)

* Track source for arrays of objects [#108417](https://github.com/elastic/elasticsearch/pull/108417) (issue: [#90708](https://github.com/elastic/elasticsearch/issues/90708))

* Track synthetic source for disabled objects [#108051](https://github.com/elastic/elasticsearch/pull/108051)

Network

* Detect long-running tasks on network threads [#109204](https://github.com/elastic/elasticsearch/pull/109204)

Ranking

* Enabling profiling for `RankBuilders` and adding tests for RRF [#109470](https://github.com/elastic/elasticsearch/pull/109470)

Relevance

* [Query Rules] Add API calls to get or delete individual query rules within a ruleset [#109554](https://github.com/elastic/elasticsearch/pull/109554)

* [Query Rules] Require Enterprise License for Query Rules [#109634](https://github.com/elastic/elasticsearch/pull/109634)

Search

* Add AVX-512 optimised vector distance functions for int7 on x64 [#109084](https://github.com/elastic/elasticsearch/pull/109084)

* Add `SparseVectorStats` [#108793](https://github.com/elastic/elasticsearch/pull/108793)

* Add `_name` support for top level `knn` clauses [#107645](https://github.com/elastic/elasticsearch/pull/107645) (issues: [#106254](https://github.com/elastic/elasticsearch/issues/106254), [#107448](https://github.com/elastic/elasticsearch/issues/107448))

* Add a SIMD (AVX2) optimised vector distance function for int7 on x64 [#108088](https://github.com/elastic/elasticsearch/pull/108088)

* Add min/max range of the `event.ingested` field to cluster state for searchable snapshots [#106252](https://github.com/elastic/elasticsearch/pull/106252)

* Add per-field KNN vector format to Index Segments API [#107216](https://github.com/elastic/elasticsearch/pull/107216)

* Add support for hiragana_uppercase & katakana_uppercase token filters in kuromoji analysis plugin [#106553](https://github.com/elastic/elasticsearch/pull/106553)

* Adding support for explain in rrf [#108682](https://github.com/elastic/elasticsearch/pull/108682)

* Allow rescorer with field collapsing [#107779](https://github.com/elastic/elasticsearch/pull/107779) (issue: [#27243](https://github.com/elastic/elasticsearch/issues/27243))

* Cut over stored fields to ZSTD for compression [#103374](https://github.com/elastic/elasticsearch/pull/103374)

* Limit the value in prefix query [#108537](https://github.com/elastic/elasticsearch/pull/108537) (issue: [#108486](https://github.com/elastic/elasticsearch/issues/108486))

* Make dense vector field type updatable [#106591](https://github.com/elastic/elasticsearch/pull/106591)

* Multivalue Sparse Vector Support [#109007](https://github.com/elastic/elasticsearch/pull/109007)

Security

* Add bulk delete roles API [#110383](https://github.com/elastic/elasticsearch/pull/110383)

* Remote cluster - API key security model - cluster privileges [#107493](https://github.com/elastic/elasticsearch/pull/107493)

Snapshot/Restore

* Denser in-memory representation of `ShardBlobsToDelete` [#109848](https://github.com/elastic/elasticsearch/pull/109848)

* Log repo UUID at generation/registration time [#109672](https://github.com/elastic/elasticsearch/pull/109672)

* Make repository analysis API available to non-operators [#110179](https://github.com/elastic/elasticsearch/pull/110179) (issue: [#100318](https://github.com/elastic/elasticsearch/issues/100318))

* Track `RequestedRangeNotSatisfiedException` separately in S3 Metrics [#109657](https://github.com/elastic/elasticsearch/pull/109657)

Stats

* DocsStats: Add human readable bytesize [#109720](https://github.com/elastic/elasticsearch/pull/109720)

TSDB

* Optimise `time_series` aggregation for single value fields [#107990](https://github.com/elastic/elasticsearch/pull/107990)

* Support `ignore_above` on keyword dimensions [#110337](https://github.com/elastic/elasticsearch/pull/110337)

Vector Search

* Adding hamming distance function to painless for `dense_vector` fields [#109359](https://github.com/elastic/elasticsearch/pull/109359)

* Support k parameter for knn query [#110233](https://github.com/elastic/elasticsearch/pull/110233) (issue: [#108473](https://github.com/elastic/elasticsearch/issues/108473))

### New features

Aggregations

* Opt `scripted_metric` out of parallelization [#109597](https://github.com/elastic/elasticsearch/pull/109597)

Application

* [Connector API] Add claim sync job endpoint [#109480](https://github.com/elastic/elasticsearch/pull/109480)

ES|QL

* ESQL: Add `ip_prefix` function [#109070](https://github.com/elastic/elasticsearch/pull/109070) (issue: [#99064](https://github.com/elastic/elasticsearch/issues/99064))

* ESQL: Introduce a casting operator, `::` [#107409](https://github.com/elastic/elasticsearch/pull/107409)

* ESQL: `top_list` aggregation [#109386](https://github.com/elastic/elasticsearch/pull/109386) (issue: [#109213](https://github.com/elastic/elasticsearch/issues/109213))

* ESQL: add Arrow dataframes output format [#109873](https://github.com/elastic/elasticsearch/pull/109873)

* Reapply "ESQL: Expose "_ignored" metadata field" [#108871](https://github.com/elastic/elasticsearch/pull/108871)

Infra/REST API

* Add a capabilities API to check node and cluster capabilities [#106820](https://github.com/elastic/elasticsearch/pull/106820)

Ingest Node

* Directly download commercial ip geolocation databases from providers [#110844](https://github.com/elastic/elasticsearch/pull/110844)

* Mark the Redact processor as Generally Available [#110395](https://github.com/elastic/elasticsearch/pull/110395)

Logs

* Introduce logs index mode as Tech Preview [#108896](https://github.com/elastic/elasticsearch/pull/108896) (issue: [#108896](https://github.com/elastic/elasticsearch/issues/108896))

Machine Learning

* Add support for Azure AI Studio embeddings and completions to the inference service. [#108472](https://github.com/elastic/elasticsearch/pull/108472)

Mapping

* Add `semantic_text` field type and `semantic` query [#110338](https://github.com/elastic/elasticsearch/pull/110338)

* Add generic fallback implementation for synthetic source [#108222](https://github.com/elastic/elasticsearch/pull/108222)

* Add synthetic source support for `geo_shape` via fallback implementation [#108881](https://github.com/elastic/elasticsearch/pull/108881)

* Add synthetic source support for binary fields [#107549](https://github.com/elastic/elasticsearch/pull/107549)

* Enable fallback synthetic source by default [#109370](https://github.com/elastic/elasticsearch/pull/109370) (issue: [#106460](https://github.com/elastic/elasticsearch/issues/106460))

* Enable fallback synthetic source for `point` and `shape` [#109312](https://github.com/elastic/elasticsearch/pull/109312)

* Enable fallback synthetic source for `token_count` [#109044](https://github.com/elastic/elasticsearch/pull/109044)

* Implement synthetic source support for annotated text field [#107735](https://github.com/elastic/elasticsearch/pull/107735)

* Implement synthetic source support for range fields [#107081](https://github.com/elastic/elasticsearch/pull/107081)

* Support arrays in fallback synthetic source implementation [#108878](https://github.com/elastic/elasticsearch/pull/108878)

* Support synthetic source for `aggregate_metric_double` when ignore_malf… [#108746](https://github.com/elastic/elasticsearch/pull/108746)

Ranking

* Add text similarity reranker retriever [#109813](https://github.com/elastic/elasticsearch/pull/109813)

Relevance

* Mark Query Rules as GA [#110004](https://github.com/elastic/elasticsearch/pull/110004)

Search

* Add new int4 quantization to dense_vector [#109317](https://github.com/elastic/elasticsearch/pull/109317)

* Adding RankFeature search phase implementation [#108538](https://github.com/elastic/elasticsearch/pull/108538)

* Adding aggregations support for the `_ignored` field [#101373](https://github.com/elastic/elasticsearch/pull/101373) (issue: [#59946](https://github.com/elastic/elasticsearch/issues/59946))

* Update Lucene version to 9.11 [#109219](https://github.com/elastic/elasticsearch/pull/109219)

Security

* Query Roles API [#108733](https://github.com/elastic/elasticsearch/pull/108733)

Transform

* Introduce _transform/_node_stats API [#107279](https://github.com/elastic/elasticsearch/pull/107279)

Vector Search

* Adds new `bit` `element_type` for `dense_vectors` [#110059](https://github.com/elastic/elasticsearch/pull/110059)

### Upgrades

Infra/Plugins

* Update ASM to 9.7 for plugin scanner [#108822](https://github.com/elastic/elasticsearch/pull/108822) (issue: [#108776](https://github.com/elastic/elasticsearch/issues/108776))

Ingest Node

* Bump Tika dependency to 2.9.2 [#108144](https://github.com/elastic/elasticsearch/pull/108144)

Network

* Upgrade to Netty 4.1.109 [#108155](https://github.com/elastic/elasticsearch/pull/108155)

Search

* Upgrade to Lucene-9.11.1 [#110234](https://github.com/elastic/elasticsearch/pull/110234)

Security

* Upgrade bouncy castle (non-fips) to 1.78.1 [#108223](https://github.com/elastic/elasticsearch/pull/108223)

Snapshot/Restore

* Bump jackson version in modules:repository-azure [#109717](https://github.com/elastic/elasticsearch/pull/109717)