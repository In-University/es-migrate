**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.2.0

### Known issues

* Parsing a request when the last element in an array is filtered out
(for instance using `_source_includes`) fails. This
is due to [a bug in Jackson parser](https://github.com/FasterXML/jackson-core/issues/882).
Fixed in Elasticsearch 8.6.1 ([#91456](https://github.com/elastic/elasticsearch/pull/92480))

### Bug fixes

Aggregations

* Don’t apply the rewrite-as-range optimization if field is multivalued [#84535](https://github.com/elastic/elasticsearch/pull/84535) (issue: [#82903](https://github.com/elastic/elasticsearch/issues/82903))

* Fix `AdaptingAggregator` `toString` method [#86042](https://github.com/elastic/elasticsearch/pull/86042)

* Fix: nested top metrics sort on keyword field [#85058](https://github.com/elastic/elasticsearch/pull/85058)

* Fix: use the correct field name when reading data from multi fields [#84752](https://github.com/elastic/elasticsearch/pull/84752)

Analysis

* Add tests for `min_hash` configuration and fix settings names [#84753](https://github.com/elastic/elasticsearch/pull/84753) (issue: [#84578](https://github.com/elastic/elasticsearch/issues/84578))

Authorization

* Add delete privilege to `kibana_system` for APM [#85085](https://github.com/elastic/elasticsearch/pull/85085)

* Ensure API key can only see itself with `QueryApiKey` API [#84859](https://github.com/elastic/elasticsearch/pull/84859)

* Fix ownership of refresh tokens [#85010](https://github.com/elastic/elasticsearch/pull/85010)

* Grant `kibana_system` role read access to APM data streams [#85744](https://github.com/elastic/elasticsearch/pull/85744)

* Handle role descriptor retrieval for internal users [#85049](https://github.com/elastic/elasticsearch/pull/85049)

* Ignore app priv failures when resolving superuser [#85519](https://github.com/elastic/elasticsearch/pull/85519)

EQL

* Clean any used memory by the sequence matcher and circuit breaker used bytes in case of exception [#84451](https://github.com/elastic/elasticsearch/pull/84451)

Engine

* Increase store ref before snapshotting index commit [#84776](https://github.com/elastic/elasticsearch/pull/84776)

Geo

* Fix fields wildcard support to vector tile search API [#85595](https://github.com/elastic/elasticsearch/pull/85595) (issue: [#85592](https://github.com/elastic/elasticsearch/issues/85592))

Highlighting

* Fix wildcard highlighting on `match_only_text` [#85500](https://github.com/elastic/elasticsearch/pull/85500) (issue: [#85493](https://github.com/elastic/elasticsearch/issues/85493))

ILM+SLM

* Fix Stacktraces Taking Memory in ILM Error Step Serialization [#84266](https://github.com/elastic/elasticsearch/pull/84266)

* Invoke initial `AsyncActionStep` for newly created indices [#84541](https://github.com/elastic/elasticsearch/pull/84541) (issue: [#77269](https://github.com/elastic/elasticsearch/issues/77269))

* Retry clean and create snapshot if it already exists #83694 [#84829](https://github.com/elastic/elasticsearch/pull/84829) (issue: [#83694](https://github.com/elastic/elasticsearch/issues/83694))

* Skip the shrink step if the number of shards of the shrunk index is the same with the original [#84434](https://github.com/elastic/elasticsearch/pull/84434) (issue: [#80180](https://github.com/elastic/elasticsearch/issues/80180))

Indices APIs

* Remove existing indices/datastreams/aliases before simulating index template [#84675](https://github.com/elastic/elasticsearch/pull/84675) (issue: [#84256](https://github.com/elastic/elasticsearch/issues/84256))

Infra/Core

* Fix `NullPointerException` in `SystemIndexMetadataUpgradeService` hidden alias handling [#84780](https://github.com/elastic/elasticsearch/pull/84780) (issue: [#81411](https://github.com/elastic/elasticsearch/issues/81411))

* Prevent `ThreadContext` header leak when sending response [#68649](https://github.com/elastic/elasticsearch/pull/68649) (issue: [#68278](https://github.com/elastic/elasticsearch/issues/68278))

* Relax data path deprecations from critical to warn [#85952](https://github.com/elastic/elasticsearch/pull/85952)

* Require and preserve content type for filtered rest requests [#84914](https://github.com/elastic/elasticsearch/pull/84914) (issue: [#84784](https://github.com/elastic/elasticsearch/issues/84784))

* Return empty version instead of blowing up if we cannot find it [#85244](https://github.com/elastic/elasticsearch/pull/85244)

* Validate index format agreement for system index descriptors [#85173](https://github.com/elastic/elasticsearch/pull/85173)

* Wrap thread creation in `doPrivileged` call [#85180](https://github.com/elastic/elasticsearch/pull/85180)

Infra/Plugins

* Strengthen elasticsearch plugin version check [#85340](https://github.com/elastic/elasticsearch/pull/85340) (issue: [#85336](https://github.com/elastic/elasticsearch/issues/85336))

Infra/REST API

* Correctly return `_type` field for documents in V7 compatiblity mode [#84873](https://github.com/elastic/elasticsearch/pull/84873) (issue: [#84173](https://github.com/elastic/elasticsearch/issues/84173))

Ingest

* Mark `GeoIpDownloaderTask` as completed after cancellation [#84028](https://github.com/elastic/elasticsearch/pull/84028)

* `CompoundProcessor` should also catch exceptions when executing a processor [#84838](https://github.com/elastic/elasticsearch/pull/84838) (issue: [#84781](https://github.com/elastic/elasticsearch/issues/84781))

License

* Fix license downgrade warnings for API Keys and Tokens [#85276](https://github.com/elastic/elasticsearch/pull/85276) (issue: [#75271](https://github.com/elastic/elasticsearch/issues/75271))

Machine Learning

* Allow retrieving `boolean` fields from `_source` in DFA jobs [#85672](https://github.com/elastic/elasticsearch/pull/85672)

* Avoid multiple queued quantiles documents in renormalizer [#85555](https://github.com/elastic/elasticsearch/pull/85555) (issue: [#85539](https://github.com/elastic/elasticsearch/issues/85539))

* Disallow new trained model deployments when nodes are different versions [#85465](https://github.com/elastic/elasticsearch/pull/85465)

* Do not fetch source when finding index of last state docs [#85334](https://github.com/elastic/elasticsearch/pull/85334)

* Ensure that inference index primary shards are available before attempting to load model [#85569](https://github.com/elastic/elasticsearch/pull/85569)

* Fix Kibana date format and similar overrides in text structure endpoint [#84967](https://github.com/elastic/elasticsearch/pull/84967)

* Fix race condition when stopping a recently relocated datafeed [#84636](https://github.com/elastic/elasticsearch/pull/84636)

* Fix serialisation of text embedding updates [#85863](https://github.com/elastic/elasticsearch/pull/85863)

* Fixes for multi-line start patterns in text structure endpoint [#85066](https://github.com/elastic/elasticsearch/pull/85066)

* Fixes to making old ML indices hidden [#85383](https://github.com/elastic/elasticsearch/pull/85383)

* Reallocate model deployments on node shutdown events [#85310](https://github.com/elastic/elasticsearch/pull/85310)

* Retry datafeed searches on skipped CCS clusters [#84052](https://github.com/elastic/elasticsearch/pull/84052) (issue: [#83838](https://github.com/elastic/elasticsearch/issues/83838))

* Return all Datafeeds with GET Anomaly Detector [#84759](https://github.com/elastic/elasticsearch/pull/84759)

Mapping

* Do not fail on duplicated content field filters [#85382](https://github.com/elastic/elasticsearch/pull/85382)

* Runtime fields core-with-mapped tests support tsdb [#83577](https://github.com/elastic/elasticsearch/pull/83577)

Packaging

* Remove use of Cloudflare zlib [#84680](https://github.com/elastic/elasticsearch/pull/84680)

Rollup

* Add support for comma delimited index patterns to rollup job configuration [#47041](https://github.com/elastic/elasticsearch/pull/47041) (issue: [#45591](https://github.com/elastic/elasticsearch/issues/45591))

SQL

* Add range checks to interval multiplication operation [#83478](https://github.com/elastic/elasticsearch/pull/83478) (issue: [#83336](https://github.com/elastic/elasticsearch/issues/83336))

* Avoid empty last pages for GROUP BY queries when possible [#84356](https://github.com/elastic/elasticsearch/pull/84356) (issue: [#75528](https://github.com/elastic/elasticsearch/issues/75528))

* Fix SQLCompatIT.testCursorFromOldNodeFailsOnNewNode [#85531](https://github.com/elastic/elasticsearch/pull/85531) (issue: [#85520](https://github.com/elastic/elasticsearch/issues/85520))

* Fix issues with format=txt when paging through result sets and in mixed node environments [#83833](https://github.com/elastic/elasticsearch/pull/83833) (issues: [#83581](https://github.com/elastic/elasticsearch/issues/83581), [#83788](https://github.com/elastic/elasticsearch/issues/83788))

* Improve ROUND and TRUNCATE to better manage Long values and big Doubles [#85106](https://github.com/elastic/elasticsearch/pull/85106) (issues: [#85105](https://github.com/elastic/elasticsearch/issues/85105), [#49391](https://github.com/elastic/elasticsearch/issues/49391))

* Use exact attributes for script templates from scalar functions [#84813](https://github.com/elastic/elasticsearch/pull/84813) (issue: [#80551](https://github.com/elastic/elasticsearch/issues/80551))

* `RANDOM(<expr>)` always evaluates to `NULL` if `<expr>` is `NULL` [#84632](https://github.com/elastic/elasticsearch/pull/84632) (issue: [#84627](https://github.com/elastic/elasticsearch/issues/84627))

Search

* Fix point visitor in `DiskUsage` API [#84909](https://github.com/elastic/elasticsearch/pull/84909)

* Fix skip caching factor with `indices.queries.cache.all_segments` [#85510](https://github.com/elastic/elasticsearch/pull/85510)

* Increase store ref before analyzing disk usage [#84774](https://github.com/elastic/elasticsearch/pull/84774)

* Limit concurrent shard requests in disk usage API [#84900](https://github.com/elastic/elasticsearch/pull/84900) (issue: [#84779](https://github.com/elastic/elasticsearch/issues/84779))

* Rewrite `match_all` inside `must_not` [#85999](https://github.com/elastic/elasticsearch/pull/85999)

* `DotExpandingXContentParser` to expose the original token location [#84970](https://github.com/elastic/elasticsearch/pull/84970)

* `TransportBroadcastAction` should always set response for each shard [#84926](https://github.com/elastic/elasticsearch/pull/84926)

Security

* `Authentication.token` now uses version from the existing authentication [#85978](https://github.com/elastic/elasticsearch/pull/85978)

* Ensure tokens represent effective user’s identity in all cases [#84263](https://github.com/elastic/elasticsearch/pull/84263)

Snapshot/Restore

* Don’t fail if there is no symlink for AWS Web Identity Token [#84697](https://github.com/elastic/elasticsearch/pull/84697)

* Expose proxy settings for GCS repositories [#85785](https://github.com/elastic/elasticsearch/pull/85785) (issue: [#84569](https://github.com/elastic/elasticsearch/issues/84569))

* Fix atomic writes in HDFS [#85210](https://github.com/elastic/elasticsearch/pull/85210)

* Fix leaking listeners bug on frozen tier [#85239](https://github.com/elastic/elasticsearch/pull/85239)

* Fix snapshot status messages on node-left [#85021](https://github.com/elastic/elasticsearch/pull/85021)

* Ignore frozen shared cache file during data folder upgrades [#85638](https://github.com/elastic/elasticsearch/pull/85638) (issue: [#85603](https://github.com/elastic/elasticsearch/issues/85603))

* [s3-repository] Lookup AWS Region for STS Client from STS endpoint [#84585](https://github.com/elastic/elasticsearch/pull/84585) (issue: [#83826](https://github.com/elastic/elasticsearch/issues/83826))

Stats

* Discard intermediate results upon cancellation for stats endpoints [#82685](https://github.com/elastic/elasticsearch/pull/82685) (issue: [#82337](https://github.com/elastic/elasticsearch/issues/82337))

Transform

* Correctly validate permissions when retention policy is configured [#85413](https://github.com/elastic/elasticsearch/pull/85413) (issue: [#85409](https://github.com/elastic/elasticsearch/issues/85409))

Watcher

* Avoiding watcher validation errors when a data stream points to more than one index [#85507](https://github.com/elastic/elasticsearch/pull/85507) (issue: [#85508](https://github.com/elastic/elasticsearch/issues/85508))

* Log at WARN level for Watcher cluster state validation errors [#85632](https://github.com/elastic/elasticsearch/pull/85632)

* No longer require master node to install Watcher templates [#85287](https://github.com/elastic/elasticsearch/pull/85287) (issue: [#85043](https://github.com/elastic/elasticsearch/issues/85043))

### Enhancements

Aggregations

* Aggs: no filter-by-filter if `_doc_count` field [#84427](https://github.com/elastic/elasticsearch/pull/84427) (issue: [#84048](https://github.com/elastic/elasticsearch/issues/84048))

* Extract agg bounds from queries in FILTER [#83902](https://github.com/elastic/elasticsearch/pull/83902)

* Give Lucene more opportunities to enable the filter-by-filter optimization [#85322](https://github.com/elastic/elasticsearch/pull/85322)

* Improve performance of `date_histogram` when date histogram is in a BoostingQuery [#83751](https://github.com/elastic/elasticsearch/pull/83751) (issues: [#82384](https://github.com/elastic/elasticsearch/issues/82384), [#75542](https://github.com/elastic/elasticsearch/issues/75542))

Allocation

* Make allocation explanations more actionable [#83983](https://github.com/elastic/elasticsearch/pull/83983)

* Use static empty store files metadata [#84034](https://github.com/elastic/elasticsearch/pull/84034)

Audit

* User Profile - Audit security config change for profile APIs [#84785](https://github.com/elastic/elasticsearch/pull/84785)

Authentication

* Adds domain information to authentication object [#82639](https://github.com/elastic/elasticsearch/pull/82639)

* Improve BWC for persisted authentication headers [#83913](https://github.com/elastic/elasticsearch/pull/83913) (issue: [#83567](https://github.com/elastic/elasticsearch/issues/83567))

* Warn on SAML attributes with special attribute names [#85248](https://github.com/elastic/elasticsearch/pull/85248) (issue: [#48613](https://github.com/elastic/elasticsearch/issues/48613))

Authorization

* Add elastic/enterprise-search-server service account [#83325](https://github.com/elastic/elasticsearch/pull/83325)

* Add index privileges for logs-enterprise_search.api-default to the enterprise-search-server service account [#84965](https://github.com/elastic/elasticsearch/pull/84965)

* Add indices permissions to Enterprise Search service account [#85726](https://github.com/elastic/elasticsearch/pull/85726)

* Note restricted indices in access denied message [#85013](https://github.com/elastic/elasticsearch/pull/85013)

* Security global privilege for updating profile data of applications [#83728](https://github.com/elastic/elasticsearch/pull/83728)

* [Osquery] Extend `kibana_system` role with an access to `osquery_manager` indices [#84279](https://github.com/elastic/elasticsearch/pull/84279)

CRUD

* Speed up Reading `RetentionLeases` from the Wire [#85159](https://github.com/elastic/elasticsearch/pull/85159)

Cluster Coordination

* Avoid deserializing cluster states on master [#58416](https://github.com/elastic/elasticsearch/pull/58416)

* Improve logging for connect-back failures [#84915](https://github.com/elastic/elasticsearch/pull/84915)

* Remove intermediate map from master task execution [#84406](https://github.com/elastic/elasticsearch/pull/84406)

* Reuse `JoinTaskExecutor` [#85325](https://github.com/elastic/elasticsearch/pull/85325)

* Speed up `MetadataStateFormat` Writes [#85138](https://github.com/elastic/elasticsearch/pull/85138)

Data streams

* Speed up `DatastreamTimestampFieldMapper#postParse` [#85270](https://github.com/elastic/elasticsearch/pull/85270)

Discovery-Plugins

* Support IMDSv2 for EC2 Discovery [#84410](https://github.com/elastic/elasticsearch/pull/84410) (issue: [#80398](https://github.com/elastic/elasticsearch/issues/80398))

Distributed

* Add elasticsearch health API [#83119](https://github.com/elastic/elasticsearch/pull/83119)

Geo

* Add `geohex_grid` aggregation to vector tiles API [#84553](https://github.com/elastic/elasticsearch/pull/84553)

* Added buffer pixels to vector tile spec parsing [#84710](https://github.com/elastic/elasticsearch/pull/84710) (issue: [#84492](https://github.com/elastic/elasticsearch/issues/84492))

* Normalise polygons only when necessary [#84229](https://github.com/elastic/elasticsearch/pull/84229) (issue: [#35349](https://github.com/elastic/elasticsearch/issues/35349))

* Support GeoJSON for `geo_point` [#85120](https://github.com/elastic/elasticsearch/pull/85120)

Health

* Fix naming in health indicators [#83587](https://github.com/elastic/elasticsearch/pull/83587)

* ILM/SLM health indicator services [#83440](https://github.com/elastic/elasticsearch/pull/83440)

* Introduce dedicated interface for health indicator details [#83417](https://github.com/elastic/elasticsearch/pull/83417)

* Repository integrity health indicator services [#83445](https://github.com/elastic/elasticsearch/pull/83445)

* Shards allocation health indicator services [#83513](https://github.com/elastic/elasticsearch/pull/83513)

ILM+SLM

* Cache ILM policy name on `IndexMetadata` [#83603](https://github.com/elastic/elasticsearch/pull/83603) (issue: [#83582](https://github.com/elastic/elasticsearch/issues/83582))

* GET _index_template and GET _component_template request support query parameter flat_settings [#83297](https://github.com/elastic/elasticsearch/pull/83297)

* Make rollover cancellable #81763 [#84584](https://github.com/elastic/elasticsearch/pull/84584) (issue: [#81763](https://github.com/elastic/elasticsearch/issues/81763))

* Rollover add max_primary_shard_docs condition [#80981](https://github.com/elastic/elasticsearch/pull/80981)

* Speed up ILM cluster task execution [#85405](https://github.com/elastic/elasticsearch/pull/85405) (issue: [#82708](https://github.com/elastic/elasticsearch/issues/82708))

Indices APIs

* Batch add index block cluster state updates [#84374](https://github.com/elastic/elasticsearch/pull/84374)

* Batch close-indices cluster state updates [#84259](https://github.com/elastic/elasticsearch/pull/84259)

* Batch open-indices cluster state updates [#83760](https://github.com/elastic/elasticsearch/pull/83760)

* Remove LegacyCTRAL from `TransportRolloverAction` [#84166](https://github.com/elastic/elasticsearch/pull/84166)

Infra/Core

* Add support for negtive epoch timestamps [#80208](https://github.com/elastic/elasticsearch/pull/80208) (issues: [#79135](https://github.com/elastic/elasticsearch/issues/79135), [#72123](https://github.com/elastic/elasticsearch/issues/72123), [#40983](https://github.com/elastic/elasticsearch/issues/40983))

* Allow yaml values for dynamic node settings [#85186](https://github.com/elastic/elasticsearch/pull/85186) (issue: [#65577](https://github.com/elastic/elasticsearch/issues/65577))

* Improve XContent Array Parser [#84477](https://github.com/elastic/elasticsearch/pull/84477)

* Optimize `ImmutableOpenMap.Builder` [#85184](https://github.com/elastic/elasticsearch/pull/85184)

* Provide *system* attribute when resolving system indices [#85042](https://github.com/elastic/elasticsearch/pull/85042) (issue: [#82671](https://github.com/elastic/elasticsearch/issues/82671))

* Remove Lucene split packages [#82132](https://github.com/elastic/elasticsearch/pull/82132) (issue: [#81981](https://github.com/elastic/elasticsearch/issues/81981))

* Simplify reading a list and converting it to a map from stream [#84183](https://github.com/elastic/elasticsearch/pull/84183)

* Speed up CompressedXContent Serialization [#84802](https://github.com/elastic/elasticsearch/pull/84802)

* Update `readMap` to avoid resizing map during reading [#84045](https://github.com/elastic/elasticsearch/pull/84045)

Infra/Plugins

* Warn on slow signature verification [#84766](https://github.com/elastic/elasticsearch/pull/84766) (issue: [#80480](https://github.com/elastic/elasticsearch/issues/80480))

Infra/Scripting

* Script: Fields API for Dense Vector [#83550](https://github.com/elastic/elasticsearch/pull/83550)

Ingest

* Do not throw exceptions when resolving paths in ingest documents [#84659](https://github.com/elastic/elasticsearch/pull/84659)

* RemoveProcessor updated to support fieldsToKeep [#83665](https://github.com/elastic/elasticsearch/pull/83665)

Machine Learning

* Add ML memory stats API [#83802](https://github.com/elastic/elasticsearch/pull/83802)

* Add support for RoBERTa and BART NLP models [#84777](https://github.com/elastic/elasticsearch/pull/84777)

* Add throughput stats for Trained Model Deployments [#84628](https://github.com/elastic/elasticsearch/pull/84628)

* Improve `zero_shot_classification` tokenization performance [#84988](https://github.com/elastic/elasticsearch/pull/84988) (issue: [#84820](https://github.com/elastic/elasticsearch/issues/84820))

Mapping

* Check the utf8 length of keyword field is not bigger than 32766 in ES, rather than in Lucene. [#83738](https://github.com/elastic/elasticsearch/pull/83738) (issue: [#80865](https://github.com/elastic/elasticsearch/issues/80865))

* Make `FieldMapper.Param` Cheaper to Construct [#85191](https://github.com/elastic/elasticsearch/pull/85191)

* Terms enum support for doc value only keyword fields [#83482](https://github.com/elastic/elasticsearch/pull/83482) (issue: [#83451](https://github.com/elastic/elasticsearch/issues/83451))

Network

* Use Throttling Netty Write Handler on HTTP Path [#84751](https://github.com/elastic/elasticsearch/pull/84751)

Query Languages

* Add `unsigned_long` type support [#65145](https://github.com/elastic/elasticsearch/pull/65145) (issue: [#63312](https://github.com/elastic/elasticsearch/issues/63312))

Recovery

* Improve failure logging in recovery-from-snapshot [#84910](https://github.com/elastic/elasticsearch/pull/84910)

Reindex

* Use `SecureString` for reindex from remote password [#85091](https://github.com/elastic/elasticsearch/pull/85091)

SQL

* Add leniency option to SQL CLI [#83795](https://github.com/elastic/elasticsearch/pull/83795) (issue: [#67436](https://github.com/elastic/elasticsearch/issues/67436))

* Forward warning headers to JDBC driver [#84499](https://github.com/elastic/elasticsearch/pull/84499)

* List data streams as VIEWs [#85168](https://github.com/elastic/elasticsearch/pull/85168) (issue: [#83449](https://github.com/elastic/elasticsearch/issues/83449))

* PIT for `GROUP BY` and `PIVOT` queries [#84605](https://github.com/elastic/elasticsearch/pull/84605) (issue: [#84349](https://github.com/elastic/elasticsearch/issues/84349))

* Replace scroll cursors with point-in-time and `search_after` [#83381](https://github.com/elastic/elasticsearch/pull/83381) (issues: [#61873](https://github.com/elastic/elasticsearch/issues/61873), [#80523](https://github.com/elastic/elasticsearch/issues/80523))

Search

* Add filtering to fieldcaps endpoint [#83636](https://github.com/elastic/elasticsearch/pull/83636) (issue: [#82966](https://github.com/elastic/elasticsearch/issues/82966))

* Group field caps response by index mapping hash [#83494](https://github.com/elastic/elasticsearch/pull/83494) (issues: [#78665](https://github.com/elastic/elasticsearch/issues/78665), [#82879](https://github.com/elastic/elasticsearch/issues/82879))

* Integrate filtering support for ANN [#84734](https://github.com/elastic/elasticsearch/pull/84734) (issue: [#81788](https://github.com/elastic/elasticsearch/issues/81788))

* Speed up merging field-caps response [#83704](https://github.com/elastic/elasticsearch/pull/83704)

Security

* Bind host all instead of just *site* when needed [#83145](https://github.com/elastic/elasticsearch/pull/83145)

* Fleet: Add a new mapping for .fleet-actions-results `action_input_type` field [#84316](https://github.com/elastic/elasticsearch/pull/84316)

* Update X509Certificate principal methods [#85163](https://github.com/elastic/elasticsearch/pull/85163) (issue: [#81008](https://github.com/elastic/elasticsearch/issues/81008))

* User Profile - Add APIs for enable/disable profile [#84548](https://github.com/elastic/elasticsearch/pull/84548)

* User Profile - Add rest spec files and tests [#83307](https://github.com/elastic/elasticsearch/pull/83307)

* User Profile - More REST spec, tests, API docs [#84597](https://github.com/elastic/elasticsearch/pull/84597)

* User Profile - Update APIs to work with domain [#83570](https://github.com/elastic/elasticsearch/pull/83570)

* User Profile - Update xpack usage output for domains [#84747](https://github.com/elastic/elasticsearch/pull/84747)

* User Profile - capture domain when creating API keys and tokens [#84547](https://github.com/elastic/elasticsearch/pull/84547)

* User Profile: Add feature flag [#83347](https://github.com/elastic/elasticsearch/pull/83347)

* User Profile: Add initial search profile API [#83191](https://github.com/elastic/elasticsearch/pull/83191)

* User Profile: handle racing on creating new profile [#84208](https://github.com/elastic/elasticsearch/pull/84208)

TSDB

* TSDB: Expand `_id` on version conflict [#84957](https://github.com/elastic/elasticsearch/pull/84957)

* TSDB: Reject the nested object fields that are configured time_series_dimension [#83920](https://github.com/elastic/elasticsearch/pull/83920)

* TSDB: routingPath object type check improvement [#83310](https://github.com/elastic/elasticsearch/pull/83310)

* TSDB: shrink `_id` inverted index [#85008](https://github.com/elastic/elasticsearch/pull/85008)

Watcher

* Add list of allowed domains for Watcher email action [#84894](https://github.com/elastic/elasticsearch/pull/84894) (issue: [#84739](https://github.com/elastic/elasticsearch/issues/84739))

### New features

Aggregations

* New `random_sampler` aggregation for sampling documents in aggregations [#84363](https://github.com/elastic/elasticsearch/pull/84363)

Authentication

* Add JWT realm support for JWT validation [#83155](https://github.com/elastic/elasticsearch/pull/83155)

* Add smoke test for JWT realm wiring [#84249](https://github.com/elastic/elasticsearch/pull/84249)

* Support mail, name, and dn claims in JWT realms [#84907](https://github.com/elastic/elasticsearch/pull/84907)

Authorization

* API Key APIs with Security Domain [#84704](https://github.com/elastic/elasticsearch/pull/84704)

Health

* Add Health Indicator Plugin [#83205](https://github.com/elastic/elasticsearch/pull/83205)

* Adding impacts block to the health info API response [#84899](https://github.com/elastic/elasticsearch/pull/84899) (issue: [#84773](https://github.com/elastic/elasticsearch/issues/84773))

Indices APIs

* Adding cat api for component template [#71274](https://github.com/elastic/elasticsearch/pull/71274) (issue: [#68941](https://github.com/elastic/elasticsearch/issues/68941))

Infra/Core

* Introduce an unauthenticated endpoint for readiness checks [#84375](https://github.com/elastic/elasticsearch/pull/84375) (issue: [#81168](https://github.com/elastic/elasticsearch/issues/81168))

Machine Learning

* Adds new `change_point` pipeline aggregation [#83428](https://github.com/elastic/elasticsearch/pull/83428)

Search

* Introduce lookup runtime fields [#82385](https://github.com/elastic/elasticsearch/pull/82385)

* Resolve wildcards in disk usage API [#84832](https://github.com/elastic/elasticsearch/pull/84832)

TSDB

* TSDB: Support GET and DELETE and doc versioning [#82633](https://github.com/elastic/elasticsearch/pull/82633)

### Upgrades

Infra/Core

* Upgrade jackson for x-content to 2.13.2 [#84905](https://github.com/elastic/elasticsearch/pull/84905)

Ingest

* Bump commons-compress to 1.21 [#85581](https://github.com/elastic/elasticsearch/pull/85581)

Network

* Upgrade Netty to 4.1.74 [#84562](https://github.com/elastic/elasticsearch/pull/84562)

Packaging

* Upgrade to JDK 18.0.0+36 [#85376](https://github.com/elastic/elasticsearch/pull/85376) (issue: [#85357](https://github.com/elastic/elasticsearch/issues/85357))

Search

* Upgrade to lucene 9.1.0-snapshot-5b522487ba8 [#85025](https://github.com/elastic/elasticsearch/pull/85025)