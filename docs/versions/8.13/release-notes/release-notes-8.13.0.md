**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.13.0

Also see [Breaking changes in 8.13](migrating-8.13.html#breaking-changes-8.13).

### Known issues

* Searches involving nodes upgraded to 8.13.0 and a coordinator node that is running on version
8.12 or earlier can produce duplicate buckets when running `date_histogram` or `histogram`
aggregations. This can happen during a rolling upgrade to 8.13 or while running cross-cluster
searches. (issue: [#108181](https://github.com/elastic/elasticsearch/issues/108181)).

* Due to a bug in the bundled JDK 22 nodes might crash abruptly under high memory pressure.
We recommend [downgrading to JDK 21.0.2](install-elasticsearch.html#jvm-version) asap to mitigate the issue.

* Nodes upgraded to 8.13.0 fail to load downsampling persistent tasks. This prevents them from joining the cluster, blocking its upgrade (issue: [#106880](https://github.com/elastic/elasticsearch/issues/106880))

This affects clusters running version 8.10 or later, with an active downsampling
[configuration](/guide/en/elasticsearch/reference/current/downsampling-ilm.html)
or a configuration that was activated at some point since upgrading to version 8.10 or later.

* When upgrading clusters from version 8.11.4 or earlier, if your cluster contains non-master-eligible nodes,
information about the new functionality of these upgraded nodes may not be registered properly with the master node.
This can lead to some new functionality added since 8.12.0 not being accessible on the upgraded cluster.
If your cluster is running on ECK 2.12.1 and above, this may cause problems with finalizing the upgrade.
To resolve this issue, perform a rolling restart on the non-master-eligible nodes once all Elasticsearch nodes
are upgraded. This issue is fixed in 8.15.0.

* The `pytorch_inference` process used to run Machine Learning models can consume large amounts of memory.
In environments where the available memory is limited, the OS Out of Memory Killer will kill the `pytorch_inference`
process to reclaim memory. This can cause inference requests to fail.
Elasticsearch will automatically restart the `pytorch_inference` process
after it is killed up to four times in 24 hours. (issue: [#110530](https://github.com/elastic/elasticsearch/issues/110530))

### Breaking changes

ES|QL

* ESQL: Grammar - FROM METADATA no longer requires [] [#105221](https://github.com/elastic/elasticsearch/pull/105221)

* ES|QL: remove PROJECT keyword from the grammar [#105064](https://github.com/elastic/elasticsearch/pull/105064)

* [ESQL] Remove is_nan, is_finite, and `is_infinite` [#104091](https://github.com/elastic/elasticsearch/pull/104091)

TSDB

* Change `index.look_ahead_time` index setting’s default value from 2 hours to 30 minutes. [#103898](https://github.com/elastic/elasticsearch/pull/103898)

* Lower the `look_ahead_time` index setting’s max value from 7 days to 2 hours. [#103434](https://github.com/elastic/elasticsearch/pull/103434)

### Bug fixes

Aggregations

* Disable parallel collection for terms aggregation with `min_doc_count` equals to 0 [#106156](https://github.com/elastic/elasticsearch/pull/106156)

* `GlobalOrdCardinalityAggregator` should use `HyperLogLogPlusPlus` instead of `HyperLogLogPlusPlusSparse` [#105546](https://github.com/elastic/elasticsearch/pull/105546)

Allocation

* Fix disk computation when initializing new shards [#102879](https://github.com/elastic/elasticsearch/pull/102879)

* Fix disk computation when initializing unassigned shards in desired balance computation [#102207](https://github.com/elastic/elasticsearch/pull/102207)

Application

* Fix Search Applications bug where deleting an alias before deleting an application intermittently caused errors [#106329](https://github.com/elastic/elasticsearch/pull/106329)

* Use search to determine if cluster contains data [#103920](https://github.com/elastic/elasticsearch/pull/103920)

* [Connector API] Bugfix: support list type in filtering advenced snippet value [#105633](https://github.com/elastic/elasticsearch/pull/105633)

* [Connector API] Fix default ordering in `SyncJob` list endpoint [#105945](https://github.com/elastic/elasticsearch/pull/105945)

* [Connector API] Fix serialisation of script params in connector index service [#106060](https://github.com/elastic/elasticsearch/pull/106060)

Authentication

* Execute SAML authentication on the generic threadpool [#105232](https://github.com/elastic/elasticsearch/pull/105232) (issue: [#104962](https://github.com/elastic/elasticsearch/issues/104962))

Authorization

* Adjust interception of requests for specific shard IDs [#101656](https://github.com/elastic/elasticsearch/pull/101656)

Client

* Validate settings in `ReloadSecureSettings` API [#103176](https://github.com/elastic/elasticsearch/pull/103176)

Data streams

* Apm-data: fix `@custom` component templates [#104182](https://github.com/elastic/elasticsearch/pull/104182)

* Avoid false-positive matches on intermediate objects in `ecs@mappings` [#105440](https://github.com/elastic/elasticsearch/pull/105440) (issue: [#102794](https://github.com/elastic/elasticsearch/issues/102794))

* Execute lazy rollover with an internal dedicated user #104732 [#104905](https://github.com/elastic/elasticsearch/pull/104905) (issue: [#104732](https://github.com/elastic/elasticsearch/issues/104732))

* Fix write index resolution when an alias is pointing to a TSDS [#104440](https://github.com/elastic/elasticsearch/pull/104440) (issue: [#104189](https://github.com/elastic/elasticsearch/issues/104189))

* x-pack/plugin/core: add `match_mapping_type` to `ecs@mappings` dynamic templates [#103035](https://github.com/elastic/elasticsearch/pull/103035)

Distributed

* Fix logger Strings.format calls [#104573](https://github.com/elastic/elasticsearch/pull/104573)

* Request indexing memory pressure in APM node metrics publisher [#103520](https://github.com/elastic/elasticsearch/pull/103520)

ES|QL

* ESQL: Add single value checks on LIKE/RLIKE pushdown [#103807](https://github.com/elastic/elasticsearch/pull/103807) (issue: [#103806](https://github.com/elastic/elasticsearch/issues/103806))

* ESQL: Correct out-of-range filter pushdowns [#99961](https://github.com/elastic/elasticsearch/pull/99961) (issue: [#99960](https://github.com/elastic/elasticsearch/issues/99960))

* ESQL: Fix Analyzer to not interpret escaped * as a pattern [#105325](https://github.com/elastic/elasticsearch/pull/105325) (issue: [#104955](https://github.com/elastic/elasticsearch/issues/104955))

* ESQL: Fix a bug loading unindexed text fields [#104553](https://github.com/elastic/elasticsearch/pull/104553)

* ESQL: Fix bug in grammar that allowed spaces inside id pattern [#105476](https://github.com/elastic/elasticsearch/pull/105476) (issue: [#105441](https://github.com/elastic/elasticsearch/issues/105441))

* ESQL: Fix replacement of nested expressions in aggs with multiple parameters [#104718](https://github.com/elastic/elasticsearch/pull/104718) (issue: [#104706](https://github.com/elastic/elasticsearch/issues/104706))

* ESQL: Fix wrong attribute shadowing in pushdown rules [#105650](https://github.com/elastic/elasticsearch/pull/105650) (issue: [#105434](https://github.com/elastic/elasticsearch/issues/105434))

* ESQL: Improve pushdown of certain filters [#103538](https://github.com/elastic/elasticsearch/pull/103538) (issue: [#103536](https://github.com/elastic/elasticsearch/issues/103536))

* ESQL: allow `null` in date math [#103610](https://github.com/elastic/elasticsearch/pull/103610) (issue: [#103085](https://github.com/elastic/elasticsearch/issues/103085))

* ESQL: make `cidr_match` foldable [#105403](https://github.com/elastic/elasticsearch/pull/105403) (issue: [#105376](https://github.com/elastic/elasticsearch/issues/105376))

* ES|QL: Disable optimizations that rely on Expression.nullable() [#105691](https://github.com/elastic/elasticsearch/pull/105691)

* ES|QL: Improve type validation in aggs for UNSIGNED_LONG better support for VERSION [#104911](https://github.com/elastic/elasticsearch/pull/104911) (issue: [#102961](https://github.com/elastic/elasticsearch/issues/102961))

* ES|QL: better management of exact subfields for TEXT fields [#103510](https://github.com/elastic/elasticsearch/pull/103510) (issue: [#99899](https://github.com/elastic/elasticsearch/issues/99899))

* Fix error on sorting unsortable `geo_point` and `cartesian_point` [#106351](https://github.com/elastic/elasticsearch/pull/106351) (issue: [#106007](https://github.com/elastic/elasticsearch/issues/106007))

* For empty mappings use a `LocalRelation` [#105081](https://github.com/elastic/elasticsearch/pull/105081) (issue: [#104809](https://github.com/elastic/elasticsearch/issues/104809))

* Resume driver when failing to fetch pages [#106392](https://github.com/elastic/elasticsearch/pull/106392) (issue: [#106262](https://github.com/elastic/elasticsearch/issues/106262))

* Review KEEP logic to prevent duplicate column names [#103316](https://github.com/elastic/elasticsearch/pull/103316)

* `ProjectOperator` should not retain references to released blocks [#105848](https://github.com/elastic/elasticsearch/pull/105848)

Engine

* Consider currently refreshing data in the memory usage of refresh [#104122](https://github.com/elastic/elasticsearch/pull/104122)

* Release `TranslogSnapshot` buffer after iteration [#106398](https://github.com/elastic/elasticsearch/pull/106398) (issue: [#106390](https://github.com/elastic/elasticsearch/issues/106390))

Health

* Make Health API more resilient to multi-version clusters [#105789](https://github.com/elastic/elasticsearch/pull/105789) (issue: [#90183](https://github.com/elastic/elasticsearch/issues/90183))

* Stop the periodic health logger when es is stopping [#105272](https://github.com/elastic/elasticsearch/pull/105272)

ILM+SLM

* Remove `hashCode` and `equals` from `OperationModeUpdateTask` [#104265](https://github.com/elastic/elasticsearch/pull/104265) (issue: [#100871](https://github.com/elastic/elasticsearch/issues/100871))

* [ILM] Delete step deletes data stream with only one index [#105772](https://github.com/elastic/elasticsearch/pull/105772)

Indices APIs

* Fix `require_alias` implicit true value on presence [#104099](https://github.com/elastic/elasticsearch/pull/104099) (issue: [#103945](https://github.com/elastic/elasticsearch/issues/103945))

Infra/CLI

* Fix server cli to always pass through exit code [#104943](https://github.com/elastic/elasticsearch/pull/104943)

Infra/Core

* Do not enable APM agent *instrument*, it’s not required for manual tracing [#105055](https://github.com/elastic/elasticsearch/pull/105055)

* Fix bogus assertion tripped by force-executed tasks [#104581](https://github.com/elastic/elasticsearch/pull/104581) (issue: [#104580](https://github.com/elastic/elasticsearch/issues/104580))

* Metrics: Allow `AsyncCounters` to switch providers [#103025](https://github.com/elastic/elasticsearch/pull/103025)

* Metrics: Handle null observations in observers [#103091](https://github.com/elastic/elasticsearch/pull/103091)

Infra/Node Lifecycle

* Close rather than stop `HttpServerTransport` on shutdown [#102759](https://github.com/elastic/elasticsearch/pull/102759) (issue: [#102501](https://github.com/elastic/elasticsearch/issues/102501))

Ingest Node

* Add stable `ThreadPool` constructor to `LogstashInternalBridge` [#105163](https://github.com/elastic/elasticsearch/pull/105163)

* Adding `executedPipelines` to the `IngestDocument` copy constructor [#105427](https://github.com/elastic/elasticsearch/pull/105427)

* Revert "x-pack/plugin/apm-data: download geoip DB on pipeline creation" [#104505](https://github.com/elastic/elasticsearch/pull/104505)

* X-pack/plugin/apm-data: fix `@custom` pipeline support [#104113](https://github.com/elastic/elasticsearch/pull/104113)

Machine Learning

* Allow GET inference models by user a with read only permission [#105346](https://github.com/elastic/elasticsearch/pull/105346)

* Avoid computing `currentInferenceProcessors` on every cluster state [#106057](https://github.com/elastic/elasticsearch/pull/106057)

* Catch all the potential exceptions in the ingest processor code [#105391](https://github.com/elastic/elasticsearch/pull/105391)

* Changed system auditor to use levels [#105429](https://github.com/elastic/elasticsearch/pull/105429)

* During ML maintenance, reset jobs in the reset state without a corresponding task [#106062](https://github.com/elastic/elasticsearch/pull/106062)

* Fix `categorize_text` aggregation nested under empty buckets [#105987](https://github.com/elastic/elasticsearch/pull/105987) (issue: [#105836](https://github.com/elastic/elasticsearch/issues/105836))

* Fix resetting a job if the original reset task no longer exists. [#106020](https://github.com/elastic/elasticsearch/pull/106020)

* Retry updates to model snapshot ID on job config [#104077](https://github.com/elastic/elasticsearch/pull/104077)

* The OpenAI model parameter should be in service settings not task settings. Move the configuration field to service settings [#105458](https://github.com/elastic/elasticsearch/pull/105458)

* Undeploy elser when inference model deleted [#104230](https://github.com/elastic/elasticsearch/pull/104230)

Mapping

* Fix parsing of flattened fields within subobjects: false [#105373](https://github.com/elastic/elasticsearch/pull/105373)

Network

* Fix use-after-free at event-loop shutdown [#105486](https://github.com/elastic/elasticsearch/pull/105486)

Search

* Correct profiled rewrite time for knn with a pre-filter [#104150](https://github.com/elastic/elasticsearch/pull/104150)

* Force execution of `SearchService.Reaper` [#106544](https://github.com/elastic/elasticsearch/pull/106544) (issue: [#106543](https://github.com/elastic/elasticsearch/issues/106543))

* Move `TransportTermsEnumAction` coordination off transport threads [#104408](https://github.com/elastic/elasticsearch/pull/104408)

* Remove `SearchException` usages without a proper status code [#105150](https://github.com/elastic/elasticsearch/pull/105150)

* Require the name field for `inner_hits` for collapse [#104666](https://github.com/elastic/elasticsearch/pull/104666)

* add validation on _id field when upsert new doc [#103399](https://github.com/elastic/elasticsearch/pull/103399) (issue: [#102981](https://github.com/elastic/elasticsearch/issues/102981))

Security

* Revert "Validate settings in `ReloadSecureSettings` API" [#103310](https://github.com/elastic/elasticsearch/pull/103310)

Snapshot/Restore

* Do not record s3 http request time when it is not available [#105103](https://github.com/elastic/elasticsearch/pull/105103)

* `URLRepository` should not block shutdown [#105588](https://github.com/elastic/elasticsearch/pull/105588)

TLS

* Respect --pass option in certutil csr mode [#106105](https://github.com/elastic/elasticsearch/pull/106105)

Transform

* Fix `_reset` API when called with `force=true` on a failed transform [#106574](https://github.com/elastic/elasticsearch/pull/106574) (issue: [#106573](https://github.com/elastic/elasticsearch/issues/106573))

* Fix a bug where destination index aliases are not set up for an unattended transform [#105499](https://github.com/elastic/elasticsearch/pull/105499)

* Remove duplicate checkpoint audits [#105164](https://github.com/elastic/elasticsearch/pull/105164) (issue: [#105106](https://github.com/elastic/elasticsearch/issues/105106))

* Return results in order [#105089](https://github.com/elastic/elasticsearch/pull/105089) (issue: [#104847](https://github.com/elastic/elasticsearch/issues/104847))

* Use deduced mappings for determining proper fields' format even if `deduce_mappings==false` [#103682](https://github.com/elastic/elasticsearch/pull/103682) (issue: [#103115](https://github.com/elastic/elasticsearch/issues/103115))

Vector Search

* Fix bug when nested knn pre-filter might match nested docs [#105994](https://github.com/elastic/elasticsearch/pull/105994)

Watcher

* Handling exceptions on watcher reload [#105442](https://github.com/elastic/elasticsearch/pull/105442) (issue: [#69842](https://github.com/elastic/elasticsearch/issues/69842))

### Deprecations

Distributed

* `DesiredNode:` deprecate `node_version` field and make it optional (unused) in current parser [#104209](https://github.com/elastic/elasticsearch/pull/104209)

Infra/Core

* Deprecate `client.type` [#104574](https://github.com/elastic/elasticsearch/pull/104574)

### Enhancements

Aggregations

* Add index mapping parameter for `counted_keyword` [#103646](https://github.com/elastic/elasticsearch/pull/103646)

* Introduce an `AggregatorReducer` to reduce the footprint of aggregations in the coordinating node [#105207](https://github.com/elastic/elasticsearch/pull/105207)

* Release resources in `BestBucketsDeferringCollector` earlier [#104893](https://github.com/elastic/elasticsearch/pull/104893)

* Support sampling in `counted_terms` aggregation [#103846](https://github.com/elastic/elasticsearch/pull/103846)

Allocation

* Account for reserved disk size [#103903](https://github.com/elastic/elasticsearch/pull/103903)

* Derive expected replica size from primary [#102078](https://github.com/elastic/elasticsearch/pull/102078)

Application

* Add serverless scopes for Connector APIs [#104063](https://github.com/elastic/elasticsearch/pull/104063)

* [Connector API] Change required privileges to indices:data/read(write) [#105289](https://github.com/elastic/elasticsearch/pull/105289)

* [Connector API] Implement update `index_name` action [#104648](https://github.com/elastic/elasticsearch/pull/104648)

* [Connector API] Support filtering by name, index name in list action [#105131](https://github.com/elastic/elasticsearch/pull/105131)

* [Connector API] Support filtering connectors by service type and a query [#105178](https://github.com/elastic/elasticsearch/pull/105178)

* [Connector API] Support updating configuration values only [#105249](https://github.com/elastic/elasticsearch/pull/105249)

* [Connectors API] Add new field `api_key_secret_id` to Connector [#104982](https://github.com/elastic/elasticsearch/pull/104982)

* [Connectors API] Implement connector status update action [#104750](https://github.com/elastic/elasticsearch/pull/104750)

* [Connectors API] Implement update native action endpoint [#104654](https://github.com/elastic/elasticsearch/pull/104654)

* [Connectors API] Implement update service type action [#104643](https://github.com/elastic/elasticsearch/pull/104643)

* [Connectors API] Relax strict response parsing for get/list operations [#104909](https://github.com/elastic/elasticsearch/pull/104909)

* [Profiling] Extract properties faster from source [#104356](https://github.com/elastic/elasticsearch/pull/104356)

* [Profiling] Mark all templates as managed [#103783](https://github.com/elastic/elasticsearch/pull/103783)

* [Profiling] Speed up processing of stacktraces [#104674](https://github.com/elastic/elasticsearch/pull/104674)

* [Profiling] Support downsampling of generic events [#104730](https://github.com/elastic/elasticsearch/pull/104730)

* [Profiling] Use shard request cache consistently [#103643](https://github.com/elastic/elasticsearch/pull/103643)

Authentication

* Expose API key authentication metrics [#103178](https://github.com/elastic/elasticsearch/pull/103178)

* Expose realms authentication metrics [#104200](https://github.com/elastic/elasticsearch/pull/104200)

* Expose service account authentication metrics [#104043](https://github.com/elastic/elasticsearch/pull/104043)

* Expose token authentication metrics [#104142](https://github.com/elastic/elasticsearch/pull/104142)

* Hot-reloadable LDAP bind password [#104320](https://github.com/elastic/elasticsearch/pull/104320)

* Support of `match` for the Query API Key API [#104594](https://github.com/elastic/elasticsearch/pull/104594)

Authorization

* [Security Solution] Allow write permission for `kibana_system` role on endpoint response index [#103555](https://github.com/elastic/elasticsearch/pull/103555)

CRUD

* Avoid wrapping searchers multiple times in mget [#104227](https://github.com/elastic/elasticsearch/pull/104227) (issue: [#85069](https://github.com/elastic/elasticsearch/issues/85069))

Client

* Add rest spec for Query User API [#104529](https://github.com/elastic/elasticsearch/pull/104529)

Cluster Coordination

* Add troubleshooting docs link to `PeerFinder` logs [#104787](https://github.com/elastic/elasticsearch/pull/104787)

* Report current master in `PeerFinder` [#104396](https://github.com/elastic/elasticsearch/pull/104396)

Data streams

* Introduce lazy rollover for mapping updates in data streams [#103309](https://github.com/elastic/elasticsearch/pull/103309) (issue: [#89346](https://github.com/elastic/elasticsearch/issues/89346))

* Use new `ignore_dynamic_beyond_limit` in logs and metric data streams [#105180](https://github.com/elastic/elasticsearch/pull/105180)

* X-pack/plugin/apm-data: add dynamic setting for enabling template registry [#104386](https://github.com/elastic/elasticsearch/pull/104386) (issue: [#104385](https://github.com/elastic/elasticsearch/issues/104385))

* X-pack/plugin/core: rename `double_metrics` template [#103033](https://github.com/elastic/elasticsearch/pull/103033)

* x-pack/plugin/apm-data: Add a new field transaction.profiler_stack_trace_ids to [traces-apm@mappings.yaml](mailto:traces-apm@mappings.yaml) [#105223](https://github.com/elastic/elasticsearch/pull/105223)

* x-pack/plugin/apm-data: Map some APM fields as flattened and fix error.grouping_name script [#103032](https://github.com/elastic/elasticsearch/pull/103032)

* x-pack/plugin/core: make automatic rollovers lazy [#105273](https://github.com/elastic/elasticsearch/pull/105273) (issue: [#104083](https://github.com/elastic/elasticsearch/issues/104083))

Discovery-Plugins

* Set read timeout for fetching IMDSv2 token [#104407](https://github.com/elastic/elasticsearch/pull/104407) (issue: [#104244](https://github.com/elastic/elasticsearch/issues/104244))

Downsampling

* Support patch transport version from 8.12 [#104406](https://github.com/elastic/elasticsearch/pull/104406)

ES|QL

* Add ES|QL async delete API [#103628](https://github.com/elastic/elasticsearch/pull/103628)

* Avoid humongous blocks [#103340](https://github.com/elastic/elasticsearch/pull/103340)

* ESQL: Add TO_UPPER and TO_LOWER functions [#104309](https://github.com/elastic/elasticsearch/pull/104309)

* ESQL: Add option to drop null fields [#102428](https://github.com/elastic/elasticsearch/pull/102428)

* ESQL: Add plan consistency verification after each optimizer [#105371](https://github.com/elastic/elasticsearch/pull/105371)

* ESQL: Check field exists before load from `_source` [#103632](https://github.com/elastic/elasticsearch/pull/103632)

* ESQL: Delay finding field load infrastructure [#103821](https://github.com/elastic/elasticsearch/pull/103821)

* ESQL: Expand shallow copy with vecs [#103681](https://github.com/elastic/elasticsearch/pull/103681) (issue: [#100528](https://github.com/elastic/elasticsearch/issues/100528))

* ESQL: Extend STATS command to support aggregate expressions [#104958](https://github.com/elastic/elasticsearch/pull/104958)

* ESQL: Infer not null for aggregated fields [#103673](https://github.com/elastic/elasticsearch/pull/103673) (issue: [#102787](https://github.com/elastic/elasticsearch/issues/102787))

* ESQL: Nested expressions inside stats command [#104387](https://github.com/elastic/elasticsearch/pull/104387) (issue: [#99828](https://github.com/elastic/elasticsearch/issues/99828))

* ESQL: Pre-allocate rows in TopNOperator [#104796](https://github.com/elastic/elasticsearch/pull/104796)

* ESQL: Referencing expressions that contain backticks requires [escaping those backticks](esql-syntax.html#esql-identifiers). [#100740](https://github.com/elastic/elasticsearch/pull/100740) (issue: [#100312](https://github.com/elastic/elasticsearch/issues/100312))

* ESQL: Simpify IS NULL/IS NOT NULL evaluation [#103099](https://github.com/elastic/elasticsearch/pull/103099) (issue: [#103097](https://github.com/elastic/elasticsearch/issues/103097))

* ESQL: Speed up reading many nulls [#105088](https://github.com/elastic/elasticsearch/pull/105088)

* ESQL: Support loading shapes from source into WKB blocks [#104269](https://github.com/elastic/elasticsearch/pull/104269)

* ESQL: Track the rest of `DocVector` [#103727](https://github.com/elastic/elasticsearch/pull/103727)

* ESQL: `MV_FIRST` and `MV_LAST` [#103928](https://github.com/elastic/elasticsearch/pull/103928)

* ESQL: add `date_diff` function [#104118](https://github.com/elastic/elasticsearch/pull/104118) (issue: [#101942](https://github.com/elastic/elasticsearch/issues/101942))

* ESQL: push down "[text_field] is not null" [#105593](https://github.com/elastic/elasticsearch/pull/105593)

* ES|QL Async Query API [#103398](https://github.com/elastic/elasticsearch/pull/103398)

* Prepare enrich plan to support multi clusters [#104355](https://github.com/elastic/elasticsearch/pull/104355)

* Reading points from source to reduce precision loss [#103698](https://github.com/elastic/elasticsearch/pull/103698)

* Remove deprecated Block APIs [#103592](https://github.com/elastic/elasticsearch/pull/103592)

* Reserve bytes before serializing page [#105269](https://github.com/elastic/elasticsearch/pull/105269)

* Support ST_CENTROID over spatial points [#104218](https://github.com/elastic/elasticsearch/pull/104218) (issue: [#104656](https://github.com/elastic/elasticsearch/issues/104656))

* Support cross clusters query in ESQL [#101640](https://github.com/elastic/elasticsearch/pull/101640)

* Support enrich ANY mode in cross clusters query [#104840](https://github.com/elastic/elasticsearch/pull/104840)

* Support enrich coordinator mode [#104936](https://github.com/elastic/elasticsearch/pull/104936)

* Support enrich remote mode [#104993](https://github.com/elastic/elasticsearch/pull/104993)

Geo

* Add support for Well Known Binary (WKB) in the fields API for spatial fields [#103461](https://github.com/elastic/elasticsearch/pull/103461)

* Add the possibility to transform WKT to WKB directly [#104030](https://github.com/elastic/elasticsearch/pull/104030)

Health

* Add APM metrics to `HealthPeriodicLogger` [#102765](https://github.com/elastic/elasticsearch/pull/102765)

* Extend `repository_integrity` health indicator for unknown and invalid repos [#104614](https://github.com/elastic/elasticsearch/pull/104614) (issue: [#103784](https://github.com/elastic/elasticsearch/issues/103784))

ILM+SLM

* Add "step":"ERROR" to ILM explain response for missing policy [#103720](https://github.com/elastic/elasticsearch/pull/103720) (issue: [#99030](https://github.com/elastic/elasticsearch/issues/99030))

* Add default rollover conditions to ILM explain API response [#104721](https://github.com/elastic/elasticsearch/pull/104721) (issue: [#103395](https://github.com/elastic/elasticsearch/issues/103395))

* ILM/SLM history policies forcemerge in hot and dsl configuration [#103190](https://github.com/elastic/elasticsearch/pull/103190)

Infra/CLI

* Add replay diagnostic dir to system jvm options [#103535](https://github.com/elastic/elasticsearch/pull/103535)

Infra/Circuit Breakers

* Lower G1 minimum full GC interval [#105259](https://github.com/elastic/elasticsearch/pull/105259)

Infra/Core

* Adding threadpool metrics [#102371](https://github.com/elastic/elasticsearch/pull/102371)

* ES - document observing with rejections [#104859](https://github.com/elastic/elasticsearch/pull/104859)

* Thread pool metrics [#104500](https://github.com/elastic/elasticsearch/pull/104500)

Infra/Metrics

* Modify name of threadpool metric for rejected [#105015](https://github.com/elastic/elasticsearch/pull/105015)

Infra/Node Lifecycle

* Wait for async searches to finish when shutting down [#101487](https://github.com/elastic/elasticsearch/pull/101487)

Infra/Transport API

* Make `ParentTaskAssigningClient.getRemoteClusterClient` method also return `ParentTaskAssigningClient` [#100813](https://github.com/elastic/elasticsearch/pull/100813)

Ingest Node

* Adding `ActionRequestLazyBuilder` implementation of `RequestBuilder` [#104927](https://github.com/elastic/elasticsearch/pull/104927)

* Adding a `RequestBuilder` interface [#104778](https://github.com/elastic/elasticsearch/pull/104778)

* Adding a custom exception for problems with the graph of pipelines to be applied to a document [#105196](https://github.com/elastic/elasticsearch/pull/105196)

* Improving the performance of the ingest simulate verbose API [#105265](https://github.com/elastic/elasticsearch/pull/105265)

* Ingest geoip processor cache *no results* from the database [#104092](https://github.com/elastic/elasticsearch/pull/104092)

* Limiting the number of nested pipelines that can be executed [#105428](https://github.com/elastic/elasticsearch/pull/105428)

* Modifying request builders [#104636](https://github.com/elastic/elasticsearch/pull/104636)

Java Low Level REST Client

* Set thread name used by REST client [#103160](https://github.com/elastic/elasticsearch/pull/103160)

Machine Learning

* Add optional pruning configuration (weighted terms scoring) to text expansion query [#102862](https://github.com/elastic/elasticsearch/pull/102862)

* Add text_embedding inference service with multilingual-e5 and custom eland models [#104949](https://github.com/elastic/elasticsearch/pull/104949)

* Add 3 automatic restarts for `pytorch_inference` processes that stop unexpectedly [#104433](https://github.com/elastic/elasticsearch/pull/104433)

* Add support for Cohere inference service [#104559](https://github.com/elastic/elasticsearch/pull/104559)

* Always test for spikes and dips as well as changes in the change point aggregation [#103922](https://github.com/elastic/elasticsearch/pull/103922)

* Apply windowing and chunking to long documents [#104363](https://github.com/elastic/elasticsearch/pull/104363)

* Automatically download the ELSER model when PUT in `_inference` [#104334](https://github.com/elastic/elasticsearch/pull/104334)

* Better handling of number of allocations in pytorch_inference in the case that hardware_concurrency fails [#2607](https://github.com/elastic/ml-cpp/pull/2607)

* Change detection aggregation improvements [#102824](https://github.com/elastic/elasticsearch/pull/102824)

* Conditionally send the dimensions field as part of the openai requests [#105299](https://github.com/elastic/elasticsearch/pull/105299) (issue: [#105005](https://github.com/elastic/elasticsearch/issues/105005))

* Endpoint to find positions of Grok pattern matches [#104394](https://github.com/elastic/elasticsearch/pull/104394)

* Ensure unique IDs between inference models and trained model deployments [#103996](https://github.com/elastic/elasticsearch/pull/103996)

* Expose some ML metrics via APM [#102584](https://github.com/elastic/elasticsearch/pull/102584)

* Make `task_type` optional in `_inference` APIs [#104483](https://github.com/elastic/elasticsearch/pull/104483)

* Update `missingTrainedModel` message to include: you may need to create it [#104155](https://github.com/elastic/elasticsearch/pull/104155)

* Upgrade MKL to version 2024.0 on Linux x86_64 [#2619](https://github.com/elastic/ml-cpp/pull/2619)

* Upgrade PyTorch to version 2.1.2. [#2588](https://github.com/elastic/ml-cpp/pull/2588)

* Upgrade zlib to version 1.2.13 on Windows [#2588](https://github.com/elastic/ml-cpp/pull/2588)

* Use Boost.JSON for JSON processing [#2614](https://github.com/elastic/ml-cpp/pull/2614)

* Validate inference model ids [#103669](https://github.com/elastic/elasticsearch/pull/103669)

Mapping

* Add `index.mapping.total_fields.ignore_dynamic_beyond_limit` setting to ignore dynamic fields when field limit is reached [#96235](https://github.com/elastic/elasticsearch/pull/96235)

* Make field limit more predictable [#102885](https://github.com/elastic/elasticsearch/pull/102885)

Network

* Prune unnecessary information from TransportNodesStatsAction.NodeStatsRequest [#102559](https://github.com/elastic/elasticsearch/pull/102559) (issue: [#100878](https://github.com/elastic/elasticsearch/issues/100878))

Percolator

* Return `matched_queries` in Percolator [#103084](https://github.com/elastic/elasticsearch/pull/103084) (issue: [#10163](https://github.com/elastic/elasticsearch/issues/10163))

Query Languages

* Introduce Alias.unwrap method [#104575](https://github.com/elastic/elasticsearch/pull/104575)

Search

* Dyamically adjust node metrics cache expire [#104460](https://github.com/elastic/elasticsearch/pull/104460)

* Enhancement: Metrics for Search Took Times using Action Listeners [#104996](https://github.com/elastic/elasticsearch/pull/104996)

* Field caps performance pt2 [#105941](https://github.com/elastic/elasticsearch/pull/105941)

* Field-caps field has value lookup use map instead of looping array [#105770](https://github.com/elastic/elasticsearch/pull/105770)

* Flag in `_field_caps` to return only fields with values in index [#103651](https://github.com/elastic/elasticsearch/pull/103651)

* Include better output in profiling & `toString` for automaton based queries [#105468](https://github.com/elastic/elasticsearch/pull/105468)

* Metrics for search latencies [#102557](https://github.com/elastic/elasticsearch/pull/102557)

* Ref count search response bytes [#103763](https://github.com/elastic/elasticsearch/pull/103763) (issue: [#102657](https://github.com/elastic/elasticsearch/issues/102657))

* Remove leniency in msearch parsing [#103232](https://github.com/elastic/elasticsearch/pull/103232)

* Resolve Cluster API [#102726](https://github.com/elastic/elasticsearch/pull/102726)

* Reuse number field mapper tests in other modules [#99142](https://github.com/elastic/elasticsearch/pull/99142) (issue: [#92947](https://github.com/elastic/elasticsearch/issues/92947))

* S3 first byte latency metric [#102435](https://github.com/elastic/elasticsearch/pull/102435)

* Update s3 latency metric to use micros [#103633](https://github.com/elastic/elasticsearch/pull/103633)

* Upgrade to Lucene 9.10.0 [#105578](https://github.com/elastic/elasticsearch/pull/105578)

Security

* Add Query Users API [#104033](https://github.com/elastic/elasticsearch/pull/104033)

* Add `ApiKey` expiration time to audit log [#103959](https://github.com/elastic/elasticsearch/pull/103959)

* Add expiration time to update api key api [#103453](https://github.com/elastic/elasticsearch/pull/103453)

* Add stricter validation for api key expiration time [#103973](https://github.com/elastic/elasticsearch/pull/103973)

* Add support for the `simple_query_string` to the Query API Key API [#104132](https://github.com/elastic/elasticsearch/pull/104132)

* Add support for the `type` parameter, for sorting, to the Query API Key API [#104625](https://github.com/elastic/elasticsearch/pull/104625)

* Aggs support for Query API Key Information API [#104895](https://github.com/elastic/elasticsearch/pull/104895)

* Hot-reloadable remote cluster credentials [#102798](https://github.com/elastic/elasticsearch/pull/102798)

Snapshot/Restore

* Add s3 `HeadObject` request to request stats [#105105](https://github.com/elastic/elasticsearch/pull/105105)

* Expose `OperationPurpose` in S3 access logs using a [custom query-string parameter](https://docs.aws.amazon.com/AmazonS3/latest/userguide/LogFormat.html#LogFormatCustom) [#105044](https://github.com/elastic/elasticsearch/pull/105044)

* Fix blob cache race, decay, time dependency [#104784](https://github.com/elastic/elasticsearch/pull/104784)

* Pause shard snapshots on graceful shutdown [#101717](https://github.com/elastic/elasticsearch/pull/101717)

* Retry indefinitely for s3 indices blob read errors [#103300](https://github.com/elastic/elasticsearch/pull/103300)

Store

* List hidden shard stores by default [#103710](https://github.com/elastic/elasticsearch/pull/103710)

TLS

* *elasticsearch-certutil cert* now verifies the issuing chain of the generated certificate [#103948](https://github.com/elastic/elasticsearch/pull/103948)

TSDB

* Improve storage efficiency for non-metric fields in TSDB [#99747](https://github.com/elastic/elasticsearch/pull/99747)

* Introduce experimental pass-through field type [#103648](https://github.com/elastic/elasticsearch/pull/103648)

* Nest pass-through objects within objects [#105062](https://github.com/elastic/elasticsearch/pull/105062)

* Restrict usage of certain aggregations when in sort order execution is required [#104665](https://github.com/elastic/elasticsearch/pull/104665)

* Small time series agg improvement [#106288](https://github.com/elastic/elasticsearch/pull/106288)

Transform

* Allow transforms to use PIT with remote clusters again [#105192](https://github.com/elastic/elasticsearch/pull/105192) (issue: [#104518](https://github.com/elastic/elasticsearch/issues/104518))

* Transforms: Adding basic stats API param [#104878](https://github.com/elastic/elasticsearch/pull/104878)

Vector Search

* Add new int8_flat and flat vector index types [#104872](https://github.com/elastic/elasticsearch/pull/104872)

* Add support for more than one `inner_hit` when searching nested vectors [#104006](https://github.com/elastic/elasticsearch/pull/104006)

* Making `k` and `num_candidates` optional for knn search [#101209](https://github.com/elastic/elasticsearch/pull/101209) (issue: [#97533](https://github.com/elastic/elasticsearch/issues/97533))

### New features

Data streams

* Add `require_data_stream` parameter to indexing requests to enforce indexing operations target a data stream [#101872](https://github.com/elastic/elasticsearch/pull/101872) (issue: [#97032](https://github.com/elastic/elasticsearch/issues/97032))

* Redirect failed ingest node operations to a failure store when available [#103481](https://github.com/elastic/elasticsearch/pull/103481)

ES|QL

* ESQL: Introduce mode setting for ENRICH [#103949](https://github.com/elastic/elasticsearch/pull/103949)

* ESQL: add =~ operator (case insensitive equality) [#103656](https://github.com/elastic/elasticsearch/pull/103656)

Health

* Create a DSL health indicator as part of the health API [#103130](https://github.com/elastic/elasticsearch/pull/103130)

Infra/Core

* Add gradle tasks and code to modify and access mappings between version ids and release versions [#103627](https://github.com/elastic/elasticsearch/pull/103627)

Mapping

* Add `unmatch_mapping_type`, and support array of types [#103171](https://github.com/elastic/elasticsearch/pull/103171) (issues: [#102807](https://github.com/elastic/elasticsearch/issues/102807), [#102795](https://github.com/elastic/elasticsearch/issues/102795))

Search

* Added Duplicate Word Check Feature to Analysis Nori [#103325](https://github.com/elastic/elasticsearch/pull/103325) (issue: [#103321](https://github.com/elastic/elasticsearch/issues/103321))

* [Synonyms] Mark Synonyms as GA [#103223](https://github.com/elastic/elasticsearch/pull/103223)

### Upgrades

Query Languages

* Upgrade ANTLR4 to 4.13.1 [#105334](https://github.com/elastic/elasticsearch/pull/105334) (issue: [#102953](https://github.com/elastic/elasticsearch/issues/102953))

Search

* Upgrade to Lucene 9.9.0 [#102782](https://github.com/elastic/elasticsearch/pull/102782)

* Upgrade to Lucene 9.9.1 [#103387](https://github.com/elastic/elasticsearch/pull/103387)

* Upgrade to Lucene 9.9.2 [#104753](https://github.com/elastic/elasticsearch/pull/104753)