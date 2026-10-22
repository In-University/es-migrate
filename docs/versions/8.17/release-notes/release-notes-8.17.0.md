**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.17.0

The 8.17.0 release contains a fix for a potential security vulnerability. See our [security advisory](https://discuss.elastic.co/c/announcements/security-announcements/31) for more details.

Also see [Breaking changes in 8.17](migrating-8.17.html#breaking-changes-8.17).

### License changes

#### Change to synthetic `_source` licensing

Starting with this release, the [synthetic `_source`](mapping-source-field.html#synthetic-source) feature is available exclusively with the Enterprise subscription. Synthetic `_source` is used in logs data streams (`logsdb` index mode), time series data streams (TSDS, using `time_series` index mode), application performance monitoring (APM), and Universal Profiling.

If you are using these capabilities and are not on an Enterprise license, the change will result in increased storage requirements for new data, as the synthetic `_source` setting will be ignored. Existing indices that used synthetic `_source` will remain seamlessly accessible.

Refer to the subscription page for [Elastic Cloud](/subscriptions/cloud) and [Elastic Stack/self-managed](/subscriptions) for the breakdown of available features and their associated subscription tiers. For further details and subscription options, contact your Elastic sales representative or [contact us](/contact).

### Bug fixes

Analysis

* Adjust analyze limit exception to be a `bad_request` [#116325](https://github.com/elastic/elasticsearch/pull/116325)

CCS

* Fix long metric deserialize & add - auto-resize needs to be set manually [#117105](https://github.com/elastic/elasticsearch/pull/117105) (issue: [#116914](https://github.com/elastic/elasticsearch/issues/116914))

CRUD

* Standardize error code when bulk body is invalid [#114869](https://github.com/elastic/elasticsearch/pull/114869)

Data streams

* Acquire stats searcher for data stream stats [#117953](https://github.com/elastic/elasticsearch/pull/117953)

EQL

* Don’t use a `BytesStreamOutput` to copy keys in `BytesRefBlockHash` [#114819](https://github.com/elastic/elasticsearch/pull/114819) (issue: [#114599](https://github.com/elastic/elasticsearch/issues/114599))

ES|QL

* Added stricter range type checks and runtime warnings for ENRICH [#115091](https://github.com/elastic/elasticsearch/pull/115091) (issues: [#107357](https://github.com/elastic/elasticsearch/issues/107357), [#116799](https://github.com/elastic/elasticsearch/issues/116799))

* Don’t return TEXT type for functions that take TEXT [#114334](https://github.com/elastic/elasticsearch/pull/114334) (issues: [#111537](https://github.com/elastic/elasticsearch/issues/111537), [#114333](https://github.com/elastic/elasticsearch/issues/114333))

* ESQL: Fix sorts containing `_source` [#116980](https://github.com/elastic/elasticsearch/pull/116980) (issue: [#116659](https://github.com/elastic/elasticsearch/issues/116659))

* ES|QL: Fix stats by constant expression [#114899](https://github.com/elastic/elasticsearch/pull/114899)

* Fix BWC for ES|QL cluster request [#117865](https://github.com/elastic/elasticsearch/pull/117865)

* Fix CCS exchange when multi cluster aliases point to same cluster [#117297](https://github.com/elastic/elasticsearch/pull/117297)

* Fix COUNT filter pushdown [#117503](https://github.com/elastic/elasticsearch/pull/117503) (issue: [#115522](https://github.com/elastic/elasticsearch/issues/115522))

* Fix NPE in `EnrichLookupService` on mixed clusters with <8.14 versions [#116583](https://github.com/elastic/elasticsearch/pull/116583) (issues: [#116529](https://github.com/elastic/elasticsearch/issues/116529), [#116544](https://github.com/elastic/elasticsearch/issues/116544))

* Fix stats by constant expresson with alias [#117551](https://github.com/elastic/elasticsearch/pull/117551)

* Fix validation of SORT by aggregate functions [#117316](https://github.com/elastic/elasticsearch/pull/117316)

* Fixing remote ENRICH by pushing the Enrich inside `FragmentExec` [#114665](https://github.com/elastic/elasticsearch/pull/114665) (issue: [#105095](https://github.com/elastic/elasticsearch/issues/105095))

* Ignore cancellation exceptions [#117657](https://github.com/elastic/elasticsearch/pull/117657)

* Limit size of `Literal#toString` [#117842](https://github.com/elastic/elasticsearch/pull/117842)

* Opt into extra data stream resolution [#118378](https://github.com/elastic/elasticsearch/pull/118378)

* Use `SearchStats` instead of field.isAggregatable in data node planning [#115744](https://github.com/elastic/elasticsearch/pull/115744) (issue: [#115737](https://github.com/elastic/elasticsearch/issues/115737))

* [ESQL] Fix Binary Comparisons on Date Nanos [#116346](https://github.com/elastic/elasticsearch/pull/116346)

* [ES|QL] To_DatePeriod and To_TimeDuration return better error messages on `union_type` fields [#114934](https://github.com/elastic/elasticsearch/pull/114934)

Infra/CLI

* Fix NPE on plugin sync [#115640](https://github.com/elastic/elasticsearch/pull/115640) (issue: [#114818](https://github.com/elastic/elasticsearch/issues/114818))

Ingest Node

* Fix enrich cache size setting name [#117575](https://github.com/elastic/elasticsearch/pull/117575)

* Fix log message format bugs [#118354](https://github.com/elastic/elasticsearch/pull/118354)

* Fix reconstituting version string from components [#117213](https://github.com/elastic/elasticsearch/pull/117213) (issue: [#116950](https://github.com/elastic/elasticsearch/issues/116950))

* Reducing error-level stack trace logging for normal events in `GeoIpDownloader` [#114924](https://github.com/elastic/elasticsearch/pull/114924)

License

* Distinguish `LicensedFeature` by family field [#116809](https://github.com/elastic/elasticsearch/pull/116809)

Logs

* Prohibit changes to index mode, source, and sort settings during resize [#115812](https://github.com/elastic/elasticsearch/pull/115812)

Machine Learning

* Fix deberta tokenizer bug caused by bug in normalizer [#117189](https://github.com/elastic/elasticsearch/pull/117189)

* Fix for Deberta tokenizer when input sequence exceeds 512 tokens [#117595](https://github.com/elastic/elasticsearch/pull/117595)

* Hides `hugging_face_elser` service from the `GET _inference/_services API` [#116664](https://github.com/elastic/elasticsearch/pull/116664) (issue: [#116644](https://github.com/elastic/elasticsearch/issues/116644))

* Mitigate IOSession timeouts [#115414](https://github.com/elastic/elasticsearch/pull/115414) (issues: [#114385](https://github.com/elastic/elasticsearch/issues/114385), [#114327](https://github.com/elastic/elasticsearch/issues/114327), [#114105](https://github.com/elastic/elasticsearch/issues/114105), [#114232](https://github.com/elastic/elasticsearch/issues/114232))

* Propagate scoring function through random sampler [#116957](https://github.com/elastic/elasticsearch/pull/116957) (issue: [#110134](https://github.com/elastic/elasticsearch/issues/110134))

* Wait for the worker service to shutdown before closing task processor [#117920](https://github.com/elastic/elasticsearch/pull/117920) (issue: [#117563](https://github.com/elastic/elasticsearch/issues/117563))

* Increase the upper limits for the Boost.JSON SAX parser [#2809](https://github.com/elastic/ml-cpp/pull/2809)

* Correct handling of config updates [#2821](https://github.com/elastic/ml-cpp/pull/2821)

Mapping

* Address mapping and compute engine runtime field issues [#117792](https://github.com/elastic/elasticsearch/pull/117792) (issue: [#117644](https://github.com/elastic/elasticsearch/issues/117644))

* Always Emit Inference ID in Semantic Text Mapping [#117294](https://github.com/elastic/elasticsearch/pull/117294)

* Fix concurrency issue with `ReinitializingSourceProvider` [#118370](https://github.com/elastic/elasticsearch/pull/118370) (issue: [#118238](https://github.com/elastic/elasticsearch/issues/118238))

* Fix false positive date detection with trailing dot [#116953](https://github.com/elastic/elasticsearch/pull/116953) (issue: [#116946](https://github.com/elastic/elasticsearch/issues/116946))

* Parse the contents of dynamic objects for [subobjects:false] [#117762](https://github.com/elastic/elasticsearch/pull/117762) (issue: [#117544](https://github.com/elastic/elasticsearch/issues/117544))

Network

* Use underlying `ByteBuf` `refCount` for `ReleasableBytesReference` [#116211](https://github.com/elastic/elasticsearch/pull/116211)

Ranking

* Fix for propagating filters from compound to inner retrievers [#117914](https://github.com/elastic/elasticsearch/pull/117914)

Search

* Add missing `async_search` query parameters to rest-api-spec [#117312](https://github.com/elastic/elasticsearch/pull/117312)

* Don’t skip shards in coord rewrite if timestamp is an alias [#117271](https://github.com/elastic/elasticsearch/pull/117271)

* Fields caps does not honour ignore_unavailable [#116021](https://github.com/elastic/elasticsearch/pull/116021) (issue: [#107767](https://github.com/elastic/elasticsearch/issues/107767))

* _validate does not honour ignore_unavailable [#116656](https://github.com/elastic/elasticsearch/pull/116656) (issue: [#116594](https://github.com/elastic/elasticsearch/issues/116594))

Vector Search

* Correct bit * byte and bit * float script comparisons [#117404](https://github.com/elastic/elasticsearch/pull/117404)

Watcher

* Watch Next Run Interval Resets On Shard Move or Node Restart [#115102](https://github.com/elastic/elasticsearch/pull/115102) (issue: [#111433](https://github.com/elastic/elasticsearch/issues/111433))

### Deprecations

Infra/REST API

* Add a basic deprecation warning that the JSON format for non-detailed error responses is changing in v9 [#114739](https://github.com/elastic/elasticsearch/pull/114739) (issue: [#89387](https://github.com/elastic/elasticsearch/issues/89387))

Mapping

* Deprecate `_source.mode` in mappings [#116689](https://github.com/elastic/elasticsearch/pull/116689)

### Enhancements

Authorization

* Add a `monitor_stats` privilege and allow that privilege for remote cluster privileges [#114964](https://github.com/elastic/elasticsearch/pull/114964)

Data streams

* Adding a deprecation info API warning for data streams with old indices [#116447](https://github.com/elastic/elasticsearch/pull/116447)

ES|QL

* Add ES|QL `bit_length` function [#115792](https://github.com/elastic/elasticsearch/pull/115792)

* ESQL: Honor skip_unavailable setting for nonmatching indices errors at planning time [#116348](https://github.com/elastic/elasticsearch/pull/116348) (issue: [#114531](https://github.com/elastic/elasticsearch/issues/114531))

* ESQL: Remove parent from `FieldAttribute` [#112881](https://github.com/elastic/elasticsearch/pull/112881)

* ESQL: extract common filter from aggs [#115678](https://github.com/elastic/elasticsearch/pull/115678)

* ESQL: optimise aggregations filtered by false/null into evals [#115858](https://github.com/elastic/elasticsearch/pull/115858)

* ES|QL CCS uses `skip_unavailable` setting for handling disconnected remote clusters [#115266](https://github.com/elastic/elasticsearch/pull/115266) (issue: [#114531](https://github.com/elastic/elasticsearch/issues/114531))

* ES|QL: add metrics for functions [#114620](https://github.com/elastic/elasticsearch/pull/114620)

* Esql Enable Date Nanos (tech preview) [#117080](https://github.com/elastic/elasticsearch/pull/117080)

* [ES|QL] Implicit casting string literal to intervals [#115814](https://github.com/elastic/elasticsearch/pull/115814) (issue: [#115352](https://github.com/elastic/elasticsearch/issues/115352))

Indices APIs

* Ensure class resource stream is closed in `ResourceUtils` [#116437](https://github.com/elastic/elasticsearch/pull/116437)

Inference

* Add version prefix to Inference Service API path [#117366](https://github.com/elastic/elasticsearch/pull/117366)

* Update sparse text embeddings API route for Inference Service [#118368](https://github.com/elastic/elasticsearch/pull/118368)

Infra/Core

* Support for unsigned 64 bit numbers in Cpu stats [#114681](https://github.com/elastic/elasticsearch/pull/114681) (issue: [#112274](https://github.com/elastic/elasticsearch/issues/112274))

Ingest Node

* Adding support for additional mapping to simulate ingest API [#114742](https://github.com/elastic/elasticsearch/pull/114742)

* Adding support for simulate ingest mapping adddition for indices with mappings that do not come from templates [#115359](https://github.com/elastic/elasticsearch/pull/115359)

Logs

* Add logsdb telemetry [#115994](https://github.com/elastic/elasticsearch/pull/115994)

* Add num docs and size to logsdb telemetry [#116128](https://github.com/elastic/elasticsearch/pull/116128)

* Feature: re-structure document ID generation favoring _id inverted index compression [#104683](https://github.com/elastic/elasticsearch/pull/104683)

Machine Learning

* Add special case for elastic reranker in inference API [#116962](https://github.com/elastic/elasticsearch/pull/116962)

* Adding inference endpoint validation for `AzureAiStudioService` [#113713](https://github.com/elastic/elasticsearch/pull/113713)

* Adds support for `input_type` field to Vertex inference service [#116431](https://github.com/elastic/elasticsearch/pull/116431)

* Enable built-in Inference Endpoints and default for Semantic Text [#116931](https://github.com/elastic/elasticsearch/pull/116931)

* Increase default `queue_capacity` to 10_000 and decrease max `queue_capacity` to 100_000 [#115041](https://github.com/elastic/elasticsearch/pull/115041)

* [Inference API] Add API to get configuration of inference services [#114862](https://github.com/elastic/elasticsearch/pull/114862)

* [Inference API] Improve chunked results error message [#115807](https://github.com/elastic/elasticsearch/pull/115807)

Recovery

* Attempt to clean up index before remote transfer [#115142](https://github.com/elastic/elasticsearch/pull/115142) (issue: [#104473](https://github.com/elastic/elasticsearch/issues/104473))

Relevance

* Add query rules retriever [#114855](https://github.com/elastic/elasticsearch/pull/114855)

Search

* Add Search Phase APM metrics [#113194](https://github.com/elastic/elasticsearch/pull/113194)

* Add `docvalue_fields` Support for `dense_vector` Fields [#114484](https://github.com/elastic/elasticsearch/pull/114484) (issue: [#108470](https://github.com/elastic/elasticsearch/issues/108470))

* Add initial support for `semantic_text` field type [#113920](https://github.com/elastic/elasticsearch/pull/113920)

* Adds access to flags no_sub_matches and no_overlapping_matches to hyphenation-decompounder-tokenfilter [#115459](https://github.com/elastic/elasticsearch/pull/115459) (issue: [#97849](https://github.com/elastic/elasticsearch/issues/97849))

* Better sizing `BytesRef` for Strings in Queries [#115655](https://github.com/elastic/elasticsearch/pull/115655)

* Enable `_tier` based coordinator rewrites for all indices (not just mounted indices) [#115797](https://github.com/elastic/elasticsearch/pull/115797)

Vector Search

* Add support for bitwise inner-product in painless [#116082](https://github.com/elastic/elasticsearch/pull/116082)

* Improve halfbyte transposition performance, marginally improving bbq performance [#117350](https://github.com/elastic/elasticsearch/pull/117350)

### New features

Data streams

* Add default ILM policies and switch to ILM for apm-data plugin [#115687](https://github.com/elastic/elasticsearch/pull/115687)

ES|QL

* Add support for `BYTE_LENGTH` scalar function [#116591](https://github.com/elastic/elasticsearch/pull/116591)

* Esql/lookup join grammar [#116515](https://github.com/elastic/elasticsearch/pull/116515)

* Remove snapshot build restriction for match and qstr functions [#114482](https://github.com/elastic/elasticsearch/pull/114482)

Search

* ESQL - Add match operator (:) [#116819](https://github.com/elastic/elasticsearch/pull/116819)

### Upgrades

Security

* Upgrade Bouncy Castle FIPS dependencies [#112989](https://github.com/elastic/elasticsearch/pull/112989)

### Known issues

ES|QL

* Some valid queries using an `ENRICH` command can fail when a match field is used that is absent from some indices or shards, either with a 500 status code due to `NullPointerException` or `ClassCastException` or with a 400 status code and `IllegalArgumentException`. This is fixed in [#126187](https://github.com/elastic/elasticsearch/pull/126187).

Vector Search

* Vector search performance can degrade on Linux systems running kernel 6.1 or later when Multi-Gen LRU (MGLRU) is enabled.

Affected Elasticsearch versions can experience significant vector search slowdowns and delayed Lucene index merges. MGLRU was introduced in Linux kernel 6.1 and is enabled by default in some Linux distributions, including Ubuntu 24.04. An interaction between MGLRU and Lucene’s read advice behavior can result in excessive major page faults and I/O activity during vector operations.

To determine whether MGLRU is enabled, run:

```
cat /sys/kernel/mm/lru_gen/enabled
```

A value of `0x0007` indicates that MGLRU and all its currently supported features are enabled.
This issue is fixed in Elasticsearch 8.17.5 and later, 8.18.1 and later, and 9.0.2 and later.
It does not affect Elasticsearch 8.19.
For more information, refer to [#124499](https://github.com/elastic/elasticsearch/issues/124499).