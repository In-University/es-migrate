**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.10.0

Also see [Breaking changes in 8.10](migrating-8.10.html#breaking-changes-8.10).

### Known issues

* Snapshot-based downgrades

The snapshot repository format changed in a manner that prevents earlier
versions of Elasticsearch from reading the repository contents if it contains
snapshots from this version and the last cluster to write to this repository
was in the 8.10 series. This will prevent you from reverting an upgrade to the
8.10 series by restoring a snapshot taken before the upgrade.

Snapshot repositories written by clusters running versions 8.11.0 and later are
compatible with all earlier versions. Moreover, clusters running version 8.11.0
or later will also automatically repair the repository format the first time
they write to the repository to take or delete a snapshot, making it so that
all earlier versions can read its contents again.

If you wish to downgrade to a version prior to 8.9.0, take or delete a snapshot
using a cluster running version 8.11.0 or later to repair the repository format
first. If you cannot repair the repository in this way, first delete all the
snapshots in the repository taken with version 8.9.0 or later. To do this will
require using a cluster running version 8.10.0 or later.

If you wish to downgrade to a version in the 8.9 series, you must take or delete
a snapshot using a cluster running version 8.11.0 or later to repair the
repository format first. If you cannot repair the repository in this way, first
delete all the snapshots in the repository taken with version 8.10.0 or later
using a cluster running version 8.10.4.

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

Analysis

* Change pre-configured and cached analyzer components to use IndexVersion instead of Version [#97319](https://github.com/elastic/elasticsearch/pull/97319)

Geo

* Remove the unused executor builder for vector tile plugin [#96577](https://github.com/elastic/elasticsearch/pull/96577)

### Bug fixes

Aggregations

* Cardinality nested in time series doc values bug [#99007](https://github.com/elastic/elasticsearch/pull/99007)

* Skip segment for `MatchNoDocsQuery` filters [#98295](https://github.com/elastic/elasticsearch/pull/98295) (issue: [#94637](https://github.com/elastic/elasticsearch/issues/94637))

Allocation

* Do not assign ignored shards [#98265](https://github.com/elastic/elasticsearch/pull/98265)

* Remove exception wrapping in `BatchedRerouteService` [#97224](https://github.com/elastic/elasticsearch/pull/97224)

Application

* [Profiling] Abort index creation on outdated index [#98864](https://github.com/elastic/elasticsearch/pull/98864)

* [Profiling] Consider static settings in status [#97890](https://github.com/elastic/elasticsearch/pull/97890)

* [Profiling] Mark executables without a name [#98884](https://github.com/elastic/elasticsearch/pull/98884)

CRUD

* Add missing sync on `indicesThatCannotBeCreated` [#97869](https://github.com/elastic/elasticsearch/pull/97869)

Cluster Coordination

* Fix cluster bootstrap warning for single-node discovery [#96895](https://github.com/elastic/elasticsearch/pull/96895) (issue: [#96874](https://github.com/elastic/elasticsearch/issues/96874))

* Fix election scheduling after discovery outage [#98420](https://github.com/elastic/elasticsearch/pull/98420)

* Improve reliability of elections with message delays [#98354](https://github.com/elastic/elasticsearch/pull/98354) (issue: [#97909](https://github.com/elastic/elasticsearch/issues/97909))

* Make `TransportAddVotingConfigExclusionsAction` retryable [#98386](https://github.com/elastic/elasticsearch/pull/98386)

* Release master service task on timeout [#97711](https://github.com/elastic/elasticsearch/pull/97711)

Data streams

* Avoid lifecycle NPE in the data stream lifecycle usage API [#98260](https://github.com/elastic/elasticsearch/pull/98260)

Distributed

* Avoid `transport_worker` thread in `TransportBroadcastAction` [#98001](https://github.com/elastic/elasticsearch/pull/98001)

* Avoid `transport_worker` thread in `TransportBroadcastByNodeAction` [#97920](https://github.com/elastic/elasticsearch/pull/97920) (issue: [#97914](https://github.com/elastic/elasticsearch/issues/97914))

* Fork response reading in `TransportNodesAction` [#97899](https://github.com/elastic/elasticsearch/pull/97899)

Downsampling

* Copy "index.lifecycle.name" for ILM managed indices [#97110](https://github.com/elastic/elasticsearch/pull/97110) (issue: [#96732](https://github.com/elastic/elasticsearch/issues/96732))

* Downsampling: copy the `_tier_preference` setting [#96982](https://github.com/elastic/elasticsearch/pull/96982) (issue: [#96733](https://github.com/elastic/elasticsearch/issues/96733))

EQL

* Fix async missing events [#97718](https://github.com/elastic/elasticsearch/pull/97718) (issue: [#97644](https://github.com/elastic/elasticsearch/issues/97644))

Geo

* Fix how Maps#flatten handle map values inside a list [#98828](https://github.com/elastic/elasticsearch/pull/98828)

* Fix mvt error when returning partial results [#98765](https://github.com/elastic/elasticsearch/pull/98765) (issue: [#98730](https://github.com/elastic/elasticsearch/issues/98730))

Health

* `_health_report` SLM indicator should use the policy ID (not the name) [#99111](https://github.com/elastic/elasticsearch/pull/99111)

Indices APIs

* Ensure frozen indices have correct tier preference [#97967](https://github.com/elastic/elasticsearch/pull/97967)

Infra/REST API

* Fix possible NPE when transportversion is null in `MainResponse` [#97203](https://github.com/elastic/elasticsearch/pull/97203)

Ingest Node

* Revert "Add mappings for enrich fields" [#98683](https://github.com/elastic/elasticsearch/pull/98683)

Machine Learning

* Avoid risk of OOM in datafeeds when memory is constrained [#98324](https://github.com/elastic/elasticsearch/pull/98324) (issue: [#89769](https://github.com/elastic/elasticsearch/issues/89769))

* Detect infinite loop in the WordPiece tokenizer [#98206](https://github.com/elastic/elasticsearch/pull/98206)

* Fix to stop aggregatable subobjects from being considered multi-fields, to support `"subobjects": false` in data frame analytics [#97705](https://github.com/elastic/elasticsearch/pull/97705) (issue: [#88605](https://github.com/elastic/elasticsearch/issues/88605))

* Fix weird `change_point` bug where all data values are equivalent [#97588](https://github.com/elastic/elasticsearch/pull/97588)

* The model loading service should not notify listeners in a sync block [#97142](https://github.com/elastic/elasticsearch/pull/97142)

Mapping

* Fix `fields` API with `subobjects: false` [#97092](https://github.com/elastic/elasticsearch/pull/97092) (issue: [#96700](https://github.com/elastic/elasticsearch/issues/96700))

Network

* Fork remote-cluster response handling [#97922](https://github.com/elastic/elasticsearch/pull/97922)

Search

* Fork CCS remote-cluster responses [#98124](https://github.com/elastic/elasticsearch/pull/98124) (issue: [#97997](https://github.com/elastic/elasticsearch/issues/97997))

* Fork CCS search-shards handling [#98209](https://github.com/elastic/elasticsearch/pull/98209)

* Improve test coverage for CCS search cancellation and fix response bugs [#97029](https://github.com/elastic/elasticsearch/pull/97029)

* Make `terminate_after` early termination friendly [#97540](https://github.com/elastic/elasticsearch/pull/97540) (issue: [#97269](https://github.com/elastic/elasticsearch/issues/97269))

* Track `max_score` in collapse when requested [#97703](https://github.com/elastic/elasticsearch/pull/97703) (issue: [#97653](https://github.com/elastic/elasticsearch/issues/97653))

Security

* Fix NPE when `GetUser` with profile uid before profile index exists [#98961](https://github.com/elastic/elasticsearch/pull/98961)

Snapshot/Restore

* Fix `BlobCacheBufferedIndexInput` large read after clone [#98970](https://github.com/elastic/elasticsearch/pull/98970)

TSDB

* Mapped field types searchable with doc values [#97724](https://github.com/elastic/elasticsearch/pull/97724)

Transform

* Fix transform incorrectly calculating date bucket on updating old data [#97401](https://github.com/elastic/elasticsearch/pull/97401) (issue: [#97101](https://github.com/elastic/elasticsearch/issues/97101))

Watcher

* Changing watcher to disable cookies in shared http client [#97591](https://github.com/elastic/elasticsearch/pull/97591)

### Deprecations

Authorization

* Mark `apm_user` for removal in a future major release [#87674](https://github.com/elastic/elasticsearch/pull/87674)

### Enhancements

Aggregations

* Improve error message when aggregation doesn’t support counter field [#93545](https://github.com/elastic/elasticsearch/pull/93545)

* Set default index mode for `TimeSeries` to `null` [#98808](https://github.com/elastic/elasticsearch/pull/98808) (issue: [#97429](https://github.com/elastic/elasticsearch/issues/97429))

Allocation

* Add `node.roles` to cat allocation API [#96994](https://github.com/elastic/elasticsearch/pull/96994)

Application

* [Profiling] Add initial support for upgrades [#97380](https://github.com/elastic/elasticsearch/pull/97380)

* [Profiling] Support index migrations [#97773](https://github.com/elastic/elasticsearch/pull/97773)

Authentication

* Avoid double get [#98067](https://github.com/elastic/elasticsearch/pull/98067) (issue: [#97928](https://github.com/elastic/elasticsearch/issues/97928))

* Give all acces to .slo-observability.* indice to kibana user [#97539](https://github.com/elastic/elasticsearch/pull/97539)

* Refresh tokens without search [#97395](https://github.com/elastic/elasticsearch/pull/97395)

Authorization

* Add "operator" field to authenticate response [#97234](https://github.com/elastic/elasticsearch/pull/97234)

* Read operator privs enabled from Env settings [#98246](https://github.com/elastic/elasticsearch/pull/98246)

* [Fleet] Allow `kibana_system` to put datastream lifecycle [#97732](https://github.com/elastic/elasticsearch/pull/97732)

Data streams

* Install data stream template for Kibana reporting [#97765](https://github.com/elastic/elasticsearch/pull/97765)

Downsampling

* Change `MetricFieldProducer#metrics` field type from list to array [#97344](https://github.com/elastic/elasticsearch/pull/97344)

* Improve iterating over many field producers during downsample operation [#97281](https://github.com/elastic/elasticsearch/pull/97281)

* Run downsampling using persistent tasks [#97557](https://github.com/elastic/elasticsearch/pull/97557) (issue: [#93582](https://github.com/elastic/elasticsearch/issues/93582))

EQL

* EQL to use only the necessary fields in the internal `field_caps` calls [#98987](https://github.com/elastic/elasticsearch/pull/98987)

Engine

* Fix edge case for active flag for flush on idle [#97332](https://github.com/elastic/elasticsearch/pull/97332) (issue: [#97154](https://github.com/elastic/elasticsearch/issues/97154))

Health

* Adding special logic to the disk health check for search-only nodes [#98508](https://github.com/elastic/elasticsearch/pull/98508)

* Health API Periodic Logging [#96772](https://github.com/elastic/elasticsearch/pull/96772)

ILM+SLM

* Separating SLM from ILM [#98184](https://github.com/elastic/elasticsearch/pull/98184)

Infra/Core

* Infrastructure to report upon document parsing [#97961](https://github.com/elastic/elasticsearch/pull/97961)

Infra/Node Lifecycle

* Check ILM status before reporting node migration STALLED [#98367](https://github.com/elastic/elasticsearch/pull/98367) (issue: [#89486](https://github.com/elastic/elasticsearch/issues/89486))

Infra/Plugins

* Adding `ApiFilteringActionFilter` [#97985](https://github.com/elastic/elasticsearch/pull/97985)

Infra/REST API

* Enable Serverless API protections dynamically [#97079](https://github.com/elastic/elasticsearch/pull/97079)

* Make `RestController` pluggable [#98187](https://github.com/elastic/elasticsearch/pull/98187)

Infra/Settings

* Mark customer settings for serverless [#98051](https://github.com/elastic/elasticsearch/pull/98051)

Ingest Node

* Allow custom geo ip database files to be downloaded [#97850](https://github.com/elastic/elasticsearch/pull/97850)

Network

* Add request header size limit for RCS transport connections [#98692](https://github.com/elastic/elasticsearch/pull/98692)

Search

* Add `completion_time` time field to `async_search` get and status response [#97700](https://github.com/elastic/elasticsearch/pull/97700) (issue: [#88640](https://github.com/elastic/elasticsearch/issues/88640))

* Add setting for search parallelism [#98455](https://github.com/elastic/elasticsearch/pull/98455)

* Add support for concurrent collection when size is greater than zero [#98425](https://github.com/elastic/elasticsearch/pull/98425)

* Cross-cluster search provides details about search on each cluster [#97731](https://github.com/elastic/elasticsearch/pull/97731)

* Enable parallel collection in Dfs phase [#97416](https://github.com/elastic/elasticsearch/pull/97416)

* Exclude clusters from a cross-cluster search [#97865](https://github.com/elastic/elasticsearch/pull/97865)

* Improve MatchNoDocsQuery description [#96069](https://github.com/elastic/elasticsearch/pull/96069) (issue: [#95741](https://github.com/elastic/elasticsearch/issues/95741))

* Improve exists query rewrite [#97159](https://github.com/elastic/elasticsearch/pull/97159)

* Improve match query rewrite [#97208](https://github.com/elastic/elasticsearch/pull/97208)

* Improve prefix query rewrite [#97209](https://github.com/elastic/elasticsearch/pull/97209)

* Improve wildcard query and terms query rewrite [#97594](https://github.com/elastic/elasticsearch/pull/97594)

* Introduce Synonyms Management API used for synonym and synonym_graph filters [#97962](https://github.com/elastic/elasticsearch/pull/97962) (issue: [#38523](https://github.com/elastic/elasticsearch/issues/38523))

* Introduce a collector manager for `PartialHitCountCollector` [#97550](https://github.com/elastic/elasticsearch/pull/97550)

* Introduce a collector manager for `QueryPhaseCollector` [#97410](https://github.com/elastic/elasticsearch/pull/97410)

* Limit `_terms_enum` prefix size [#97488](https://github.com/elastic/elasticsearch/pull/97488) (issue: [#96572](https://github.com/elastic/elasticsearch/issues/96572))

* Support minimum_should_match field for terms_set query [#96082](https://github.com/elastic/elasticsearch/pull/96082)

* Support type for simple query string [#96717](https://github.com/elastic/elasticsearch/pull/96717)

* Unwrap IOException in `ContextIndexSearcher` concurrent code-path [#98459](https://github.com/elastic/elasticsearch/pull/98459)

* Use a collector manager in DfsPhase Knn Search [#96689](https://github.com/elastic/elasticsearch/pull/96689)

* Use the Weight#matches mode for highlighting by default [#96068](https://github.com/elastic/elasticsearch/pull/96068)

* Wire `QueryPhaseCollectorManager` into the query phase [#97726](https://github.com/elastic/elasticsearch/pull/97726)

* Wire concurrent top docs collector managers when size is 0 [#97755](https://github.com/elastic/elasticsearch/pull/97755)

* `ProfileCollectorManager` to support child profile collectors [#97387](https://github.com/elastic/elasticsearch/pull/97387)

* cleanup some code NoriTokenizerFactory and KuromojiTokenizerFactory [#92574](https://github.com/elastic/elasticsearch/pull/92574)

Security

* Add an API for managing the settings of Security system indices [#97630](https://github.com/elastic/elasticsearch/pull/97630)

* Support getting active-only API keys via Get API keys API [#98259](https://github.com/elastic/elasticsearch/pull/98259) (issue: [#97995](https://github.com/elastic/elasticsearch/issues/97995))

Snapshot/Restore

* Add Setting to optionally use mmap for shared cache IO [#97581](https://github.com/elastic/elasticsearch/pull/97581)

* Collect additional object store stats for S3 [#98083](https://github.com/elastic/elasticsearch/pull/98083)

* HDFS plugin add replication_factor param [#94132](https://github.com/elastic/elasticsearch/pull/94132)

Store

* Allow Lucene directory implementations to estimate their size [#97822](https://github.com/elastic/elasticsearch/pull/97822)

* Allow `ByteSizeDirectory` to expose their data set sizes [#98085](https://github.com/elastic/elasticsearch/pull/98085)

TSDB

* Add tsdb metrics builtin component template [#97602](https://github.com/elastic/elasticsearch/pull/97602)

* Include more downsampling status statistics [#96930](https://github.com/elastic/elasticsearch/pull/96930) (issue: [#96760](https://github.com/elastic/elasticsearch/issues/96760))

* `TimeSeriesIndexSearcher` to offload to the provided executor [#98414](https://github.com/elastic/elasticsearch/pull/98414)

Transform

* Support boxplot aggregation in transform [#96515](https://github.com/elastic/elasticsearch/pull/96515)

### New features

Application

* Enable Query Rules as technical preview [#97466](https://github.com/elastic/elasticsearch/pull/97466)

* [Enterprise Search] Add connectors indices and ent-search pipeline [#97463](https://github.com/elastic/elasticsearch/pull/97463)

Data streams

* Introduce downsampling configuration for data stream lifecycle [#97041](https://github.com/elastic/elasticsearch/pull/97041)

Search

* Introduce executor for concurrent search [#98204](https://github.com/elastic/elasticsearch/pull/98204)

Security

* Beta release for API key based cross-cluster access [#98307](https://github.com/elastic/elasticsearch/pull/98307)

### Upgrades

Network

* Upgrade Netty to 4.1.94.Final [#97040](https://github.com/elastic/elasticsearch/pull/97040)