**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.4.0

Also see [Breaking changes in 8.4](migrating-8.4.html#breaking-changes-8.4).

### Known issues

* Machine learning datafeeds cannot be listed if any are not modified since version 6.x

If you have a datafeed that was created in version 5.x or 6.x and has not
been updated since 7.0, it is not possible to list datafeeds in
8.4 and 8.5. This means that anomaly detection jobs cannot be managed using
Kibana. This issue is fixed in 8.6.0.

If you upgrade to 8.4 or 8.5 with such a datafeed, you need to
work around the problem by updating each datafeed’s authorization information
using [these steps](https://support.elastic.dev/knowledge/view/b5a879db).

* Orchestrators which use a `settings.json` file to configure Elasticsearch may
encounter deadlocks during master elections (issue: [#92812](https://github.com/elastic/elasticsearch/issues/92812))

To resolve the deadlock, remove the `settings.json` file and restart the
affected node.

* Parsing a request when the last element in an array is filtered out
(for instance using `_source_includes`) fails. This
is due to [a bug in Jackson parser](https://github.com/FasterXML/jackson-core/issues/882).
Fixed in Elasticsearch 8.6.1 ([#91456](https://github.com/elastic/elasticsearch/pull/92480))

* When the [ingest attachment processor](/guide/en/elasticsearch/reference/8.17/attachment.html) is used, the
interaction of [Tika](https://tika.apache.org/) with log4j 2.18.0 and higher
(introduced in Elasticsearch 8.4.0) results in excessive logging. This logging is so
excessive that it can lead to cluster instability, to the point where the
cluster is unusable and nodes must be restarted. (issue: [#91964](https://github.com/elastic/elasticsearch/issues/91964)).
This issue is fixed in Elasticsearch 8.7.0 ([#93878](https://github.com/elastic/elasticsearch/pull/93878))

To resolve the issue, upgrade to 8.7.0 or higher.

### Bug fixes

Aggregations

* Fix multi-value handling in composite agg [#88638](https://github.com/elastic/elasticsearch/pull/88638)

* Fix: extract matrix stats using `bucket_selector` `buckets_path` [#88271](https://github.com/elastic/elasticsearch/pull/88271) (issue: [#87454](https://github.com/elastic/elasticsearch/issues/87454))

* Make the metric in the `buckets_path` parameter optional [#87220](https://github.com/elastic/elasticsearch/pull/87220) (issue: [#72983](https://github.com/elastic/elasticsearch/issues/72983))

* Propagate alias filters to significance aggs filters [#88221](https://github.com/elastic/elasticsearch/pull/88221) (issue: [#81585](https://github.com/elastic/elasticsearch/issues/81585))

Allocation

* Clamp auto-expand replicas to the closest value [#87505](https://github.com/elastic/elasticsearch/pull/87505) (issue: [#84788](https://github.com/elastic/elasticsearch/issues/84788))

* Prevent re-balancing using outdated node weights in some cases [#88385](https://github.com/elastic/elasticsearch/pull/88385) (issue: [#88384](https://github.com/elastic/elasticsearch/issues/88384))

* Remove any existing `read_only_allow_delete` index blocks when `cluster.routing.allocation.disk.threshold_enabled` is set to `false` [#87841](https://github.com/elastic/elasticsearch/pull/87841) (issue: [#86383](https://github.com/elastic/elasticsearch/issues/86383))

* Replace health request with a state observer [#88641](https://github.com/elastic/elasticsearch/pull/88641)

Authentication

* Fix unique realm name check to cover default realms [#87999](https://github.com/elastic/elasticsearch/pull/87999)

Authorization

* Add rollover permissions for `remote_monitoring_agent` [#87717](https://github.com/elastic/elasticsearch/pull/87717) (issue: [#84161](https://github.com/elastic/elasticsearch/issues/84161))

Autoscaling

* Autoscaling during shrink [#88292](https://github.com/elastic/elasticsearch/pull/88292) (issue: [#85480](https://github.com/elastic/elasticsearch/issues/85480))

* Do not include desired nodes in snapshots [#87695](https://github.com/elastic/elasticsearch/pull/87695)

Cluster Coordination

* Improve rejection of ambiguous voting config name [#89239](https://github.com/elastic/elasticsearch/pull/89239)

Data streams

* Fix renaming data streams with CCR replication [#88875](https://github.com/elastic/elasticsearch/pull/88875) (issue: [#81751](https://github.com/elastic/elasticsearch/issues/81751))

Distributed

* Fixed NullPointerException on bulk request [#88385](https://github.com/elastic/elasticsearch/pull/88385)

EQL

* Avoid attempting PIT close on PIT open failure [#87498](https://github.com/elastic/elasticsearch/pull/87498)

* Improve EQL Sequence circuit breaker precision [#88538](https://github.com/elastic/elasticsearch/pull/88538) (issue: [#88300](https://github.com/elastic/elasticsearch/issues/88300))

Geo

* Geo_line aggregation returns a geojson point when the resulting line has only one point [#89199](https://github.com/elastic/elasticsearch/pull/89199) (issue: [#85748](https://github.com/elastic/elasticsearch/issues/85748))

* Sort ranges in `geo_distance` aggregation [#89154](https://github.com/elastic/elasticsearch/pull/89154) (issue: [#89147](https://github.com/elastic/elasticsearch/issues/89147))

Health

* Fix NPE when checking if the last snapshot was success [#88811](https://github.com/elastic/elasticsearch/pull/88811)

* Fixing a version check for master stability functionality [#89322](https://github.com/elastic/elasticsearch/pull/89322)

* Fixing internal action names [#89182](https://github.com/elastic/elasticsearch/pull/89182)

* Using the correct connection to fetch remote master history [#87299](https://github.com/elastic/elasticsearch/pull/87299)

Highlighting

* Handle ordering in plain highlighter for multiple inputs [#87414](https://github.com/elastic/elasticsearch/pull/87414) (issue: [#87210](https://github.com/elastic/elasticsearch/issues/87210))

ILM+SLM

* Batch ILM move to retry step task update [#86759](https://github.com/elastic/elasticsearch/pull/86759)

Infra/CLI

* Quote paths with whitespace in Windows service CLIs [#89072](https://github.com/elastic/elasticsearch/pull/89072) (issue: [#89043](https://github.com/elastic/elasticsearch/issues/89043))

Infra/Core

* Always close directory streams [#88560](https://github.com/elastic/elasticsearch/pull/88560)

* Delete invalid settings for system indices [#88903](https://github.com/elastic/elasticsearch/pull/88903) (issue: [#88324](https://github.com/elastic/elasticsearch/issues/88324))

* Disallow three-digit minor and revision versions [#87338](https://github.com/elastic/elasticsearch/pull/87338)

* Handle snapshot restore in file settings [#89321](https://github.com/elastic/elasticsearch/pull/89321) (issue: [#89183](https://github.com/elastic/elasticsearch/issues/89183))

* System indices ignore all user templates [#87260](https://github.com/elastic/elasticsearch/pull/87260) (issues: [#42508](https://github.com/elastic/elasticsearch/issues/42508), [#74271](https://github.com/elastic/elasticsearch/issues/74271))

Infra/Node Lifecycle

* Fix message for stalled shutdown [#89254](https://github.com/elastic/elasticsearch/pull/89254)

Infra/Plugins

* Disable URL connection caching in SPIClassIterator [#88586](https://github.com/elastic/elasticsearch/pull/88586) (issue: [#88275](https://github.com/elastic/elasticsearch/issues/88275))

Infra/Scripting

* Script: `UpdateByQuery` can read doc version if requested [#88740](https://github.com/elastic/elasticsearch/pull/88740)

Machine Learning

* Address potential bug where trained models get stuck in starting after being allocated to node [#88945](https://github.com/elastic/elasticsearch/pull/88945)

* Fix BERT and MPNet tokenization bug when handling unicode accents [#88907](https://github.com/elastic/elasticsearch/pull/88907) (issue: [#88900](https://github.com/elastic/elasticsearch/issues/88900))

* Fix NLP `question_answering` task when best answer is only one token [#88347](https://github.com/elastic/elasticsearch/pull/88347)

* Include start params in `_stats` for non-started model deployments [#89091](https://github.com/elastic/elasticsearch/pull/89091)

* Fix minor tokenization bug when using fill_mask task with roberta tokenizer [#88825](https://github.com/elastic/elasticsearch/pull/88825)

* Fix potential cause of classification and regression job failures [#2385](https://github.com/elastic/ml-cpp/pull/2385)

Mapping

* Assign the right path to objects merged when parsing mappings [#89389](https://github.com/elastic/elasticsearch/pull/89389) (issue: [#88573](https://github.com/elastic/elasticsearch/issues/88573))

* Don’t modify source map when parsing composite runtime field [#89114](https://github.com/elastic/elasticsearch/pull/89114)

Network

* Ensure that the extended socket options TCP_KEEPXXX are available [#88935](https://github.com/elastic/elasticsearch/pull/88935) (issue: [#88897](https://github.com/elastic/elasticsearch/issues/88897))

SQL

* Fix `SqlSearchIT` `testAllTypesWithRequestToOldNodes` [#88883](https://github.com/elastic/elasticsearch/pull/88883) (issue: [#88866](https://github.com/elastic/elasticsearch/issues/88866))

* Fix date range checks [#87151](https://github.com/elastic/elasticsearch/pull/87151) (issue: [#77179](https://github.com/elastic/elasticsearch/issues/77179))

* fix object equals [#87887](https://github.com/elastic/elasticsearch/pull/87887)

Search

* Fix: use status code 500 for aggregation reduce phase errors if no shard failed [#88551](https://github.com/elastic/elasticsearch/pull/88551) (issue: [#20004](https://github.com/elastic/elasticsearch/issues/20004))

* Override bulk visit methods of exitable point visitor [#82120](https://github.com/elastic/elasticsearch/pull/82120)

Security

* Ensure `secureString` remain open when reloading secure settings [#88922](https://github.com/elastic/elasticsearch/pull/88922)

Snapshot/Restore

* Fix queued snapshot assignments after partial snapshot fails due to delete [#88470](https://github.com/elastic/elasticsearch/pull/88470) (issue: [#86724](https://github.com/elastic/elasticsearch/issues/86724))

Transform

* Handle update error correctly [#88619](https://github.com/elastic/elasticsearch/pull/88619)

### Deprecations

Vector Search

* Deprecate the `_knn_search` endpoint [#88828](https://github.com/elastic/elasticsearch/pull/88828)

### Enhancements

Aggregations

* Adding cardinality support for `random_sampler` agg [#86838](https://github.com/elastic/elasticsearch/pull/86838)

* Minor `RangeAgg` optimization [#86935](https://github.com/elastic/elasticsearch/pull/86935) (issue: [#84262](https://github.com/elastic/elasticsearch/issues/84262))

* Speed counting filters/range/date_histogram aggs [#81322](https://github.com/elastic/elasticsearch/pull/81322)

* Update bucket metric pipeline agg paths to allow intermediate single bucket and bucket qualified multi-bucket aggs [#85729](https://github.com/elastic/elasticsearch/pull/85729)

Allocation

* Add debug information to `ReactiveReason` about assigned and unassigned shards [#86132](https://github.com/elastic/elasticsearch/pull/86132) (issue: [#85243](https://github.com/elastic/elasticsearch/issues/85243))

* Optimize log cluster health performance. [#87723](https://github.com/elastic/elasticsearch/pull/87723)

* Use desired nodes during data tier allocation decisions [#87735](https://github.com/elastic/elasticsearch/pull/87735)

Audit

* Audit API key ID when create or grant API keys [#88456](https://github.com/elastic/elasticsearch/pull/88456)

* Include API key metadata in audit log when an API key is created, granted, or updated [#88642](https://github.com/elastic/elasticsearch/pull/88642)

* Updatable API keys - logging audit trail event [#88276](https://github.com/elastic/elasticsearch/pull/88276)

* User Profile - audit support for security domain [#87097](https://github.com/elastic/elasticsearch/pull/87097)

Authentication

* If signature validation fails, reload JWKs and retry if new JWKs are found [#88023](https://github.com/elastic/elasticsearch/pull/88023)

Authorization

* App permissions with action patterns do not retrieve privileges [#85455](https://github.com/elastic/elasticsearch/pull/85455)

* Cancellable Profile Has Privilege check [#87224](https://github.com/elastic/elasticsearch/pull/87224)

* Return action denied error when user with insufficient privileges (`manage_own_api_key`) attempts a grant API key request [#87461](https://github.com/elastic/elasticsearch/pull/87461) (issue: [#87438](https://github.com/elastic/elasticsearch/issues/87438))

* Update indices permissions to Enterprise Search service account [#88703](https://github.com/elastic/elasticsearch/pull/88703)

Autoscaling

* Add processors to autoscaling capacity response [#87895](https://github.com/elastic/elasticsearch/pull/87895)

* Keep track of desired nodes status in cluster state [#87474](https://github.com/elastic/elasticsearch/pull/87474)

Cluster Coordination

* Deduplicate mappings in persisted cluster state [#88479](https://github.com/elastic/elasticsearch/pull/88479)

* Expose segment details in PCSS debug log [#87412](https://github.com/elastic/elasticsearch/pull/87412)

* Periodic warning for 1-node cluster w/ seed hosts [#88013](https://github.com/elastic/elasticsearch/pull/88013) (issue: [#85222](https://github.com/elastic/elasticsearch/issues/85222))

* Report overall mapping size in cluster stats [#87556](https://github.com/elastic/elasticsearch/pull/87556)

Data streams

* Give doc-value-only mappings to numeric fields on metrics templates [#87100](https://github.com/elastic/elasticsearch/pull/87100)

Distributed

* Adding the ability to register a `PeerFinderListener` to Coordinator [#88626](https://github.com/elastic/elasticsearch/pull/88626)

* Make Desired Nodes API operator-only [#87778](https://github.com/elastic/elasticsearch/pull/87778) (issue: [#87777](https://github.com/elastic/elasticsearch/issues/87777))

* Support "dry run" mode for updating Desired Nodes [#88305](https://github.com/elastic/elasticsearch/pull/88305)

FIPS

* Log warning when hash function used by cache is not recommended in FIPS mode [#86740](https://github.com/elastic/elasticsearch/pull/86740)

* Log warning when hashers for stored API keys or service tokens are not compliant with FIPS [#87363](https://github.com/elastic/elasticsearch/pull/87363)

Geo

* Optimize geogrid aggregations for singleton points [#87439](https://github.com/elastic/elasticsearch/pull/87439)

* Support cartesian shape with doc values [#88487](https://github.com/elastic/elasticsearch/pull/88487)

* Use a faster but less accurate log algorithm for computing Geotile Y coordinate [#87515](https://github.com/elastic/elasticsearch/pull/87515)

* Use faster maths to project WGS84 to mercator [#88231](https://github.com/elastic/elasticsearch/pull/88231)

Health

* Add health user action for unhealthy SLM policy failure counts [#88523](https://github.com/elastic/elasticsearch/pull/88523)

* Adding a transport action to get cluster formation info [#87306](https://github.com/elastic/elasticsearch/pull/87306)

* Adding additional capability to the `master_is_stable` health indicator service [#87482](https://github.com/elastic/elasticsearch/pull/87482)

* Creating a transport action for the `CoordinationDiagnosticsService` [#87984](https://github.com/elastic/elasticsearch/pull/87984)

* Move the master stability logic into its own service separate from the `HealthIndicatorService` [#87672](https://github.com/elastic/elasticsearch/pull/87672)

* Polling cluster formation state for master-is-stable health indicator [#88397](https://github.com/elastic/elasticsearch/pull/88397)

* Remove cluster block preflight check from health api [#87520](https://github.com/elastic/elasticsearch/pull/87520) (issue: [#87464](https://github.com/elastic/elasticsearch/issues/87464))

ILM+SLM

* Add min_* conditions to rollover [#83345](https://github.com/elastic/elasticsearch/pull/83345)

* Track the count of failed invocations since last successful policy snapshot [#88398](https://github.com/elastic/elasticsearch/pull/88398)

Infra/Core

* Improve console exception messages [#87942](https://github.com/elastic/elasticsearch/pull/87942)

* Print full exception when console is non-interactive [#88297](https://github.com/elastic/elasticsearch/pull/88297)

* Stop making index read-only when executing force merge index lifecycle management action [#81162](https://github.com/elastic/elasticsearch/pull/81162) (issue: [#81162](https://github.com/elastic/elasticsearch/issues/81162))

* Stream input and output support for optional collections [#88127](https://github.com/elastic/elasticsearch/pull/88127)

* Update version of internal http client [#87491](https://github.com/elastic/elasticsearch/pull/87491)

Infra/Logging

* Catch an exception when formatting a string fails [#87132](https://github.com/elastic/elasticsearch/pull/87132)

Infra/Scripting

* Script: Add Metadata to ingest context [#87309](https://github.com/elastic/elasticsearch/pull/87309)

* Script: Metadata for update context [#88333](https://github.com/elastic/elasticsearch/pull/88333)

Infra/Settings

* Convert disk watermarks to RelativeByteSizeValues [#88719](https://github.com/elastic/elasticsearch/pull/88719)

Ingest

* Allow pipeline processor to ignore missing pipelines [#87354](https://github.com/elastic/elasticsearch/pull/87354)

* Move the ingest attachment processor to the default distribution [#87989](https://github.com/elastic/elasticsearch/pull/87989)

* Only perform `ensureNoSelfReferences` check during ingest when needed [#87352](https://github.com/elastic/elasticsearch/pull/87352) (issue: [#87335](https://github.com/elastic/elasticsearch/issues/87335))

* Removing `BouncyCastle` dependencies from ingest-attachment plugin [#88031](https://github.com/elastic/elasticsearch/pull/88031)

Machine Learning

* Add authorization info to ML config listings [#87884](https://github.com/elastic/elasticsearch/pull/87884)

* Add deployed native models to `inference_stats` in trained model stats response [#88187](https://github.com/elastic/elasticsearch/pull/88187)

* Add inference cache hit count to inference node stats [#88807](https://github.com/elastic/elasticsearch/pull/88807)

* Add new `cache_size` parameter to `trained_model` deployments API [#88450](https://github.com/elastic/elasticsearch/pull/88450)

* Expand allowed NER labels to be any I-O-B tagged labels [#87091](https://github.com/elastic/elasticsearch/pull/87091)

* Improve scalability of NLP models [#87366](https://github.com/elastic/elasticsearch/pull/87366)

* Indicate overall deployment failure if all node routes are failed [#88378](https://github.com/elastic/elasticsearch/pull/88378)

* New `frequent_items` aggregation [#83055](https://github.com/elastic/elasticsearch/pull/83055)

* Fairer application of size penalty for model selection for training classification and regression models [#2291](https://github.com/elastic/ml-cpp/pull/2291)

* Accelerate training for data frame analytics by skipping fine parameter tuning if it is unnecessary [#2298](https://github.com/elastic/ml-cpp/pull/2298)

* Address some causes of high runtimes training regression and classification models on large data sets with many features [#2332](https://github.com/elastic/ml-cpp/pull/2332)

* Add caching for PyTorch inference [#2305](https://github.com/elastic/ml-cpp/pull/2305)

* Improve accuracy of anomaly detection median estimation [#2367](https://github.com/elastic/ml-cpp/pull/2367) (issue: [#2364](https://github.com/elastic/ml-cpp/issues/2364))

Mapping

* Enable synthetic source support on constant keyword fields [#88603](https://github.com/elastic/elasticsearch/pull/88603)

* Speed up `NumberFieldMapper` [#85688](https://github.com/elastic/elasticsearch/pull/85688)

Monitoring

* JvmService use SingleObjectCache [#87236](https://github.com/elastic/elasticsearch/pull/87236)

Network

* Allow start cluster with unreachable remote clusters [#87298](https://github.com/elastic/elasticsearch/pull/87298)

* Increase `http.max_header_size` default to 16kb [#88725](https://github.com/elastic/elasticsearch/pull/88725) (issue: [#88501](https://github.com/elastic/elasticsearch/issues/88501))

Query Languages

* Add support for VERSION field type in SQL and EQL [#87590](https://github.com/elastic/elasticsearch/pull/87590) (issue: [#83375](https://github.com/elastic/elasticsearch/issues/83375))

Rollup

* [TSDB] Add Kahan support to downsampling summation [#87554](https://github.com/elastic/elasticsearch/pull/87554)

SQL

* Implement support for partial search results in SQL CLI [#86982](https://github.com/elastic/elasticsearch/pull/86982) (issue: [#86082](https://github.com/elastic/elasticsearch/issues/86082))

* Update Tableau connector to use connection dialog v2 [#88462](https://github.com/elastic/elasticsearch/pull/88462)

Search

* Add mapping stats for indexed `dense_vectors` [#86859](https://github.com/elastic/elasticsearch/pull/86859)

* Improve error when sorting on incompatible types [#88399](https://github.com/elastic/elasticsearch/pull/88399) (issue: [#73146](https://github.com/elastic/elasticsearch/issues/73146))

* Support kNN vectors in disk usage action [#88785](https://github.com/elastic/elasticsearch/pull/88785) (issue: [#84801](https://github.com/elastic/elasticsearch/issues/84801))

Security

* Add setting for `tcp_keepalive` for oidc back-channel [#87868](https://github.com/elastic/elasticsearch/pull/87868)

* Support `run_as` another user when granting API keys [#88335](https://github.com/elastic/elasticsearch/pull/88335)

* Support exists query for API key query [#87229](https://github.com/elastic/elasticsearch/pull/87229)

* Updatable API keys - REST API spec and tests [#88270](https://github.com/elastic/elasticsearch/pull/88270)

* Updatable API keys - noop check [#88346](https://github.com/elastic/elasticsearch/pull/88346)

Snapshot/Restore

* INFO logging of snapshot restore and completion [#88257](https://github.com/elastic/elasticsearch/pull/88257) (issue: [#86610](https://github.com/elastic/elasticsearch/issues/86610))

* Make snapshot deletes not block the repository during data blob deletes [#86514](https://github.com/elastic/elasticsearch/pull/86514)

* Retry after all S3 get failures that made progress [#88015](https://github.com/elastic/elasticsearch/pull/88015) (issue: [#87243](https://github.com/elastic/elasticsearch/issues/87243))

* Speed up creating new `IndexMetaDataGenerations` without removed snapshots [#88344](https://github.com/elastic/elasticsearch/pull/88344)

* Update HDFS Repository to HDFS 3.3.3 [#88039](https://github.com/elastic/elasticsearch/pull/88039)

Stats

* Sort ingest pipeline stats by use [#88035](https://github.com/elastic/elasticsearch/pull/88035)

TLS

* Add issuer to GET _ssl/certificates [#88445](https://github.com/elastic/elasticsearch/pull/88445)

Transform

* Add authorization info to transform config listings [#87570](https://github.com/elastic/elasticsearch/pull/87570)

* Implement per-transform num_failure_retries setting [#87361](https://github.com/elastic/elasticsearch/pull/87361)

### New features

Authentication

* Support updates of API key attributes (single operation route) [#88186](https://github.com/elastic/elasticsearch/pull/88186)

Health

* Master stability health indicator part 1 (when a master has been seen recently) [#86524](https://github.com/elastic/elasticsearch/pull/86524)

* Remove help_url,rename summary to symptom, and `user_actions` to diagnosis [#88553](https://github.com/elastic/elasticsearch/pull/88553) (issue: [#88474](https://github.com/elastic/elasticsearch/issues/88474))

Infra/Core

* File Settings Service [#88329](https://github.com/elastic/elasticsearch/pull/88329)

Infra/Logging

* Stable logging API - the basic use case [#86612](https://github.com/elastic/elasticsearch/pull/86612)

Machine Learning

* Make composite aggs in datafeeds Generally Available [#88589](https://github.com/elastic/elasticsearch/pull/88589)

Search

* Add *mode* option to `_source` field mapper [#88211](https://github.com/elastic/elasticsearch/pull/88211)

TSDB

* TSDB: Implement downsampling ILM Action for time-series indices [#87269](https://github.com/elastic/elasticsearch/pull/87269) (issue: [#68609](https://github.com/elastic/elasticsearch/issues/68609))

Vector Search

* Integrate ANN into `_search` endpoint [#88694](https://github.com/elastic/elasticsearch/pull/88694) (issue: [#87625](https://github.com/elastic/elasticsearch/issues/87625))

### Upgrades

Infra/Core

* Upgrade to Log4J 2.18.0 [#88237](https://github.com/elastic/elasticsearch/pull/88237)

Network

* Upgrade to Netty 4.1.77 [#86630](https://github.com/elastic/elasticsearch/pull/86630)