**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.5.0

Also see [Breaking changes in 8.5](migrating-8.5.html#breaking-changes-8.5).

### Known issues

* It is possible to inadvertently create an alias with the same name as an
index in version 8.5.0. This action leaves the cluster in an invalid state in
which several features will not work correctly, and it may not even be possible
to restart nodes while in this state. Upgrade to 8.5.1 as soon as possible to
avoid the risk of this occurring ([#91456](https://github.com/elastic/elasticsearch/pull/91456)). If your cluster is
affected by this issue, upgrade to 8.5.3 to repair it ([#91887](https://github.com/elastic/elasticsearch/pull/91887)).

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

### Breaking changes

CRUD

* Reject unknown bulk actions [#89450](https://github.com/elastic/elasticsearch/pull/89450)

### Bug fixes

Aggregations

* Fix `auto_date_histogram` > `ip_range` [#90317](https://github.com/elastic/elasticsearch/pull/90317) (issue: [#90121](https://github.com/elastic/elasticsearch/issues/90121))

* Fail when rebuilding scorer in `breadth_first` mode and query context has changed [#89993](https://github.com/elastic/elasticsearch/pull/89993) (issue: [#37650](https://github.com/elastic/elasticsearch/issues/37650))

* Fix merging with empty results [#86939](https://github.com/elastic/elasticsearch/pull/86939) (issue: [#84622](https://github.com/elastic/elasticsearch/issues/84622))

* Fix partial reduce bug in `ip_prefix` [#89734](https://github.com/elastic/elasticsearch/pull/89734) (issue: [#89686](https://github.com/elastic/elasticsearch/issues/89686))

* Remove unexpected meta parameter in aggregation response [#89467](https://github.com/elastic/elasticsearch/pull/89467) (issue: [#89455](https://github.com/elastic/elasticsearch/issues/89455))

* Consistently allow sorting `top_metrics` aggregations whose size is greater than 1 [#89974](https://github.com/elastic/elasticsearch/pull/89974) (issue: [#86663](https://github.com/elastic/elasticsearch/issues/86663))

* Check parent circuit breaker when allocating an empty bucket [#89568](https://github.com/elastic/elasticsearch/pull/89568) (issue: [#80789](https://github.com/elastic/elasticsearch/issues/80789))

Authorization

* Remove magic string for the `"__empty"` role [#89766](https://github.com/elastic/elasticsearch/pull/89766)

CCR

* Order follower backing indices for data streams by original name [#90850](https://github.com/elastic/elasticsearch/pull/90850) (issue: [#90820](https://github.com/elastic/elasticsearch/issues/90820))

Cluster Coordination

* Capture deprecation warnings in batched master tasks [#85525](https://github.com/elastic/elasticsearch/pull/85525) (issue: [#85506](https://github.com/elastic/elasticsearch/issues/85506))

* Check circuit breaker before sending join request [#89318](https://github.com/elastic/elasticsearch/pull/89318) (issue: [#85003](https://github.com/elastic/elasticsearch/issues/85003))

Distributed

* Fork `TransportClusterStateAction` to `MANAGEMENT` thread pool [#90996](https://github.com/elastic/elasticsearch/pull/90996)

Engine

* Fix `"path.conf'"` typo in `Security.java` [#89248](https://github.com/elastic/elasticsearch/pull/89248) (issue: [#89327](https://github.com/elastic/elasticsearch/issues/89327))

Geo

* Buffer H3Polygon2D bounding boxes to avoid edge precision issues [#89196](https://github.com/elastic/elasticsearch/pull/89196) (issues: [#89868](https://github.com/elastic/elasticsearch/issues/89868), [#87391](https://github.com/elastic/elasticsearch/issues/87391))

* Fix date histogram range edge case [#88957](https://github.com/elastic/elasticsearch/pull/88957)

* Format runtime `geo_points` [#85449](https://github.com/elastic/elasticsearch/pull/85449) (issue: [#85245](https://github.com/elastic/elasticsearch/issues/85245))

* Generate error if scripts load `_source` with synthetic `_source` enabled [#88334](https://github.com/elastic/elasticsearch/pull/88334)

Graph

* Fix race condition in timeout [#88946](https://github.com/elastic/elasticsearch/pull/88946) (issue: [#55396](https://github.com/elastic/elasticsearch/issues/55396))

Health

* Modify disk indicator details to provide an overview of the disk space health [#90189](https://github.com/elastic/elasticsearch/pull/90189)

* Fix disk indicator impacts and diagnosis [#90262](https://github.com/elastic/elasticsearch/pull/90262)

* Fix the details calculation of the disk indicator [#90869](https://github.com/elastic/elasticsearch/pull/90869)

* Report impact and diagnosis data nodes without disk space and no blocked indices [#90772](https://github.com/elastic/elasticsearch/pull/90772) (issue: [#90442](https://github.com/elastic/elasticsearch/issues/90442))

* Update minimum version for health node reporting to 8.5 [#90365](https://github.com/elastic/elasticsearch/pull/90365) (issue: [#90359](https://github.com/elastic/elasticsearch/issues/90359))

Indices APIs

* Avoid capturing per-task `RolloverResult` [#90626](https://github.com/elastic/elasticsearch/pull/90626) (issue: [#90620](https://github.com/elastic/elasticsearch/issues/90620))

* Fix shard splitting for `nested` [#89351](https://github.com/elastic/elasticsearch/pull/89351) (issue: [#88109](https://github.com/elastic/elasticsearch/issues/88109))

Infra/Core

* Fix `allow_no_indices` request option in special cases [#89622](https://github.com/elastic/elasticsearch/pull/89622)

* Fix repeated error save loops in File Settings Service [#90271](https://github.com/elastic/elasticsearch/pull/90271) (issue: [#90222](https://github.com/elastic/elasticsearch/issues/90222))

* Fix date rounding for date math parsing [#90458](https://github.com/elastic/elasticsearch/pull/90458) (issue: [#90187](https://github.com/elastic/elasticsearch/issues/90187))

* Fix disabling APM tracing for `CancellableTask` in `TrainedModelAssignmentNodeService` [#90972](https://github.com/elastic/elasticsearch/pull/90972) (issue: [#89850](https://github.com/elastic/elasticsearch/issues/89850))

* Support camel case dates on 7.x indices [#88914](https://github.com/elastic/elasticsearch/pull/88914) (issue: [#84199](https://github.com/elastic/elasticsearch/issues/84199))

Infra/Scripting

* Fix true/false accumulation bug in boolean `source` fallback [#90895](https://github.com/elastic/elasticsearch/pull/90895)

Ingest Node

* Set the enrich maintenance cluster lifecycle listener only once [#90486](https://github.com/elastic/elasticsearch/pull/90486)

Machine Learning

* Require correct tier processors when multiple AZs are present [#90903](https://github.com/elastic/elasticsearch/pull/90903)

* Return 408 instead of 500 when open/start APIs time out [#89775](https://github.com/elastic/elasticsearch/pull/89775) (issue: [#89585](https://github.com/elastic/elasticsearch/issues/89585))

Mapping

* Fix duplication bug for `source` fallback in numeric types [#89352](https://github.com/elastic/elasticsearch/pull/89352)

* Include runtime fields in total fields count [#89251](https://github.com/elastic/elasticsearch/pull/89251) (issue: [#88265](https://github.com/elastic/elasticsearch/issues/88265))

* Fix `aggregate_metric_double` multi-values exception [#90290](https://github.com/elastic/elasticsearch/pull/90290)

* Validate field names when subobjects are disabled [#90950](https://github.com/elastic/elasticsearch/pull/90950)

Monitoring

* Add fields to fix Logstash cgroup graphs [#90493](https://github.com/elastic/elasticsearch/pull/90493)

Network

* Fix `RecyclerBytesStreamOutput` allocating unlimited heap for some capacities [#90632](https://github.com/elastic/elasticsearch/pull/90632)

Recovery

* Fix overcounting recovered bytes after network disconnect [#90477](https://github.com/elastic/elasticsearch/pull/90477) (issue: [#90441](https://github.com/elastic/elasticsearch/issues/90441))

Search

* Add support for predefined char class regexp on wildcard fields [#90064](https://github.com/elastic/elasticsearch/pull/90064)

* Deduplicate fetching doc-values fields [#89094](https://github.com/elastic/elasticsearch/pull/89094)

* Don’t shortcut the total hit count for text fields [#90341](https://github.com/elastic/elasticsearch/pull/90341) (issue: [#89760](https://github.com/elastic/elasticsearch/issues/89760))

* Safeguard `RegExp` use against `StackOverflowError` [#84624](https://github.com/elastic/elasticsearch/pull/84624) (issue: [#82923](https://github.com/elastic/elasticsearch/issues/82923))

* Use MB rather than GB to calculate max boolean clauses [#90309](https://github.com/elastic/elasticsearch/pull/90309) (issue: [#86136](https://github.com/elastic/elasticsearch/issues/86136))

Snapshot/Restore

* Fix incorrect failed shards count in APIs for current snapshots [#89534](https://github.com/elastic/elasticsearch/pull/89534)

* Fix over-allocation of mounted indices on a cold/frozen node [#86331](https://github.com/elastic/elasticsearch/pull/86331)

* Fix quadratic complexity in `SnapshotStatus` serialization [#90795](https://github.com/elastic/elasticsearch/pull/90795)

* Fork building snapshot status response off of transport thread [#90651](https://github.com/elastic/elasticsearch/pull/90651)

* Make sure listener is resolved when file queue is cleared [#89929](https://github.com/elastic/elasticsearch/pull/89929)

* Re-register a corrupt repository to unblock it [#89719](https://github.com/elastic/elasticsearch/pull/89719) (issue: [#89130](https://github.com/elastic/elasticsearch/issues/89130))

* Reject unknown request body fields in mount API [#88987](https://github.com/elastic/elasticsearch/pull/88987) (issue: [#75982](https://github.com/elastic/elasticsearch/issues/75982))

TSDS

* Fix segment stats in TSDS [#89754](https://github.com/elastic/elasticsearch/pull/89754) (issue: [#89609](https://github.com/elastic/elasticsearch/issues/89609))

* Fix extra fields in `GET` request for synthetic `_source` [#89778](https://github.com/elastic/elasticsearch/pull/89778)

* Fix `scaled_float` rounding for synthetic `_source` [#88916](https://github.com/elastic/elasticsearch/pull/88916) (issue: [#88854](https://github.com/elastic/elasticsearch/issues/88854))

Transform

* Don’t fail a transform on a ClusterBlockException, this may be due to ILM closing an index [#90396](https://github.com/elastic/elasticsearch/pull/90396) (issue: [#89802](https://github.com/elastic/elasticsearch/issues/89802))

* Fix NPE in transform scheduling [#90347](https://github.com/elastic/elasticsearch/pull/90347) (issues: [#90356](https://github.com/elastic/elasticsearch/issues/90356), [#88203](https://github.com/elastic/elasticsearch/issues/88203), [#90301](https://github.com/elastic/elasticsearch/issues/90301), [#90255](https://github.com/elastic/elasticsearch/issues/90255))

* Improve error handling in state persistence [#88910](https://github.com/elastic/elasticsearch/pull/88910) (issue: [#88905](https://github.com/elastic/elasticsearch/issues/88905))

* Return `408` instead of `500` when the start API times out [#89774](https://github.com/elastic/elasticsearch/pull/89774)

Vector Search

* Fix bug for `kNN` with filtered aliases [#89621](https://github.com/elastic/elasticsearch/pull/89621)

Watcher

* Allow `xpack.notification.email.account.domain_allowlist` to be set dynamically [#90426](https://github.com/elastic/elasticsearch/pull/90426) (issue: [#89913](https://github.com/elastic/elasticsearch/issues/89913))

* Handling timeout exceptions on watcher startup [#90421](https://github.com/elastic/elasticsearch/pull/90421) (issue: [#44981](https://github.com/elastic/elasticsearch/issues/44981))

### Deprecations

Infra/Plugins

* Deprecate network plugins [#88924](https://github.com/elastic/elasticsearch/pull/88924)

* Deprecate overriding `DiscoveryPlugin` internals [#88925](https://github.com/elastic/elasticsearch/pull/88925)

### Enhancements

Authentication

* Add more accurate error message for LDAP user modes [#89492](https://github.com/elastic/elasticsearch/pull/89492)

Authorization

* Add indices permissions to Enterprise Search service account [#89869](https://github.com/elastic/elasticsearch/pull/89869)

* Add information of resolved roles in denial messages [#89680](https://github.com/elastic/elasticsearch/pull/89680)

Autoscaling

* Centralize the concept of processors configuration [#89662](https://github.com/elastic/elasticsearch/pull/89662)

Cluster Coordination

* Preemptively compute `RoutingNodes` and the indices lookup during publication [#89005](https://github.com/elastic/elasticsearch/pull/89005)

* Preemptively initialize routing nodes and indices lookup on all node types [#89032](https://github.com/elastic/elasticsearch/pull/89032)

Distributed

* Batch index delete cluster state updates [#90033](https://github.com/elastic/elasticsearch/pull/90033) (issue: [#90022](https://github.com/elastic/elasticsearch/issues/90022))

* Increase the minimum size of the management pool to `2` [#90193](https://github.com/elastic/elasticsearch/pull/90193)

Health

* Add IDs to health API diagnoses and impacts [#90072](https://github.com/elastic/elasticsearch/pull/90072)

* Add a check to the master stability health API when there is no master and the current node is not master eligible [#89219](https://github.com/elastic/elasticsearch/pull/89219)

* Add logic to `master_is_stable` indicator to check for discovery problems [#88020](https://github.com/elastic/elasticsearch/pull/88020)

* Poll for cluster diagnostics information [#89014](https://github.com/elastic/elasticsearch/pull/89014)

* Update SLM health diagnosis message to include unhealthy policy details [#89138](https://github.com/elastic/elasticsearch/pull/89138)

Highlighting

* Improve efficiency of `BoundedBreakIteratorScanner` fragmentation algorithm [#89041](https://github.com/elastic/elasticsearch/pull/89041) (issues: [#73569](https://github.com/elastic/elasticsearch/issues/73569), [#73785](https://github.com/elastic/elasticsearch/issues/73785))

ILM+SLM

* Add validations for the downsampling ILM action [#90295](https://github.com/elastic/elasticsearch/pull/90295)

* Ensure that ILM does not roll over empty indices [#89557](https://github.com/elastic/elasticsearch/pull/89557) (issue: [#86203](https://github.com/elastic/elasticsearch/issues/86203))

* Reuse informational message in lifecycle step [#89419](https://github.com/elastic/elasticsearch/pull/89419)

* Move log-related logic into log block in `IndexLifecycleRunner` [#89292](https://github.com/elastic/elasticsearch/pull/89292)

Infra/Core

* Add reserved `/_snapshot/repo` file based settings [#89601](https://github.com/elastic/elasticsearch/pull/89601)

* Add `upgrade_status` attributes to Fleet Agents [#89845](https://github.com/elastic/elasticsearch/pull/89845)

* Add support for `/_autoscaling/policy` for file based settings [#89708](https://github.com/elastic/elasticsearch/pull/89708)

* Add support for `/_security/role_mapping` for file based settings [#89667](https://github.com/elastic/elasticsearch/pull/89667)

* Add support for support for `/_slm/policy` in file based settings [#89567](https://github.com/elastic/elasticsearch/pull/89567)

* Retry file watch registration [#90537](https://github.com/elastic/elasticsearch/pull/90537) (issue: [#89500](https://github.com/elastic/elasticsearch/issues/89500))

Infra/Node Lifecycle

* Distinguish no shutdowns case in `NodeShutdownAllocationDecider` [#89851](https://github.com/elastic/elasticsearch/pull/89851) (issue: [#89823](https://github.com/elastic/elasticsearch/issues/89823))

Infra/Plugins

* Add deprecation message for deprecated plugin APIs [#88961](https://github.com/elastic/elasticsearch/pull/88961)

* Register stable plugins in `ActionModule` [#90067](https://github.com/elastic/elasticsearch/pull/90067)

* Load plugin named components [#89969](https://github.com/elastic/elasticsearch/pull/89969)

Infra/Scripting

* Initial code to support binary expression scripts [#89895](https://github.com/elastic/elasticsearch/pull/89895)

* Protect `_source` inside update scripts [#88733](https://github.com/elastic/elasticsearch/pull/88733)

* Reindex and `UpdateByQuery` metadata [#88665](https://github.com/elastic/elasticsearch/pull/88665)

* Add write Field API `NestedDocument` support [#90021](https://github.com/elastic/elasticsearch/pull/90021)

* Add write Field API path manipulation [#89889](https://github.com/elastic/elasticsearch/pull/89889)

* Add write Field API with basic path resolution [#89738](https://github.com/elastic/elasticsearch/pull/89738)

* Add write Fields API for reindex, update, and update by query [#90145](https://github.com/elastic/elasticsearch/pull/90145)

Infra/Settings

* Introduce max headroom for disk watermark stages [#88639](https://github.com/elastic/elasticsearch/pull/88639) (issue: [#81406](https://github.com/elastic/elasticsearch/issues/81406))

License

* License check for user profile collaboration feature [#89990](https://github.com/elastic/elasticsearch/pull/89990)

Machine Learning

* Add measure of non-cache hit inference count [#90464](https://github.com/elastic/elasticsearch/pull/90464)

* Add new `text_similarity` nlp task [#88439](https://github.com/elastic/elasticsearch/pull/88439)

* Add new trained model deployment cache clear API [#89074](https://github.com/elastic/elasticsearch/pull/89074)

* Add processor autoscaling decider [#89645](https://github.com/elastic/elasticsearch/pull/89645)

* Distribute trained model allocations across availability zones [#89822](https://github.com/elastic/elasticsearch/pull/89822)

* Use a bitset for deduplication of frequent items [#88943](https://github.com/elastic/elasticsearch/pull/88943)

* Optimize frequent items transaction lookup [#89062](https://github.com/elastic/elasticsearch/pull/89062)

* Release native inference functionality as beta [#90418](https://github.com/elastic/elasticsearch/pull/90418)

* Return `408` when the start deployment API times out [#89612](https://github.com/elastic/elasticsearch/pull/89612)

* Skip renormalization after calling the node shutdown API [#89347](https://github.com/elastic/elasticsearch/pull/89347)

* Compute outlier feature influence via the Gateaux derivative to improve attribution for high dimension vectors [#2256](https://github.com/elastic/ml-cpp/pull/2256)

* Improve classification and regression model train runtimes for data sets with many numeric features [#2380](https://github.com/elastic/ml-cpp/pull/2380), [#2388](https://github.com/elastic/ml-cpp/pull/2388), [#2390](https://github.com/elastic/ml-cpp/pull/2390), [#2401](https://github.com/elastic/ml-cpp/pull/2401)

* Increase the limit on the maximum number of classes to `100` for training classification models [#2395](https://github.com/elastic/ml-cpp/pull/2395) (issue: [#2246](https://github.com/elastic/ml-cpp/issues/2246))

Mapping

* Add `synthetic_source` support to `aggregate_metric_double` fields [#88909](https://github.com/elastic/elasticsearch/pull/88909)

* Add `source` fallback for keyword fields using operation [#88735](https://github.com/elastic/elasticsearch/pull/88735)

* Add `source` fallback support for `match_only_text` mapped type [#89473](https://github.com/elastic/elasticsearch/pull/89473)

* Add `source` fallback support for date and `date_nanos` mapped types [#89440](https://github.com/elastic/elasticsearch/pull/89440)

* Add `source` fallback support for unsigned long mapped type [#89349](https://github.com/elastic/elasticsearch/pull/89349)

* Add support for `source` fallback with scaled float field type [#89053](https://github.com/elastic/elasticsearch/pull/89053)

* Add support for `source` fallback with the boolean field type [#89052](https://github.com/elastic/elasticsearch/pull/89052)

* Add text field support in the Painless scripting fields API [#89396](https://github.com/elastic/elasticsearch/pull/89396)

* Clarify that fielddata is not supported for text fields error message [#89770](https://github.com/elastic/elasticsearch/pull/89770) (issue: [#89485](https://github.com/elastic/elasticsearch/issues/89485))

* Add new mappings for Fleet Agent `last_checkin_message` and components fields [#89599](https://github.com/elastic/elasticsearch/pull/89599)

* Support `source` fallback for `byte`, `short`, and `long` fields [#88954](https://github.com/elastic/elasticsearch/pull/88954)

* Support `source` fallback for `double`, `float`, and `half_float` field types [#89010](https://github.com/elastic/elasticsearch/pull/89010)

Network

* Use chunked REST serialization for large REST responses [#88311](https://github.com/elastic/elasticsearch/pull/88311)

Recovery

* Disable recovering from snapshots in searchable snapshots [#86388](https://github.com/elastic/elasticsearch/pull/86388)

SQL

* Implement `DATE_FORMAT` function [#88388](https://github.com/elastic/elasticsearch/pull/88388) (issue: [#55065](https://github.com/elastic/elasticsearch/issues/55065))

* Set `track_total_hits` to false when not needed [#89106](https://github.com/elastic/elasticsearch/pull/89106) (issue: [#88764](https://github.com/elastic/elasticsearch/issues/88764))

Search

* Enable `BloomFilter` for `_id` of non-datastream indices [#88409](https://github.com/elastic/elasticsearch/pull/88409)

* In the field capabilities API, renew support for fields in the request body [#88972](https://github.com/elastic/elasticsearch/pull/88972) (issue: [#86875](https://github.com/elastic/elasticsearch/issues/86875))

Security

* Add usage stats report for user profiles [#90123](https://github.com/elastic/elasticsearch/pull/90123)

* Implement grace period for user profile activation [#89566](https://github.com/elastic/elasticsearch/pull/89566)

* Return limited-by role descriptors in Get/QueryApiKey response [#89273](https://github.com/elastic/elasticsearch/pull/89273)

* Add option to return profile uid in `GetUser` response [#89570](https://github.com/elastic/elasticsearch/pull/89570)

* Return `400` error for `GetUserPrivileges` call with API keys [#89333](https://github.com/elastic/elasticsearch/pull/89333)

* Show assigned role descriptors in Get/QueryApiKey response [#89166](https://github.com/elastic/elasticsearch/pull/89166)

* Add detailed errors in `hasPrivileges` response [#89224](https://github.com/elastic/elasticsearch/pull/89224)

* Add support for multiple UIDs to the `GetProfile` API [#89023](https://github.com/elastic/elasticsearch/pull/89023)

Snapshot/Restore

* Add support for comparing `SnapshotsInProgress` [#89619](https://github.com/elastic/elasticsearch/pull/89619) (issue: [#88732](https://github.com/elastic/elasticsearch/issues/88732))

* Prioritize shard snapshot tasks over file snapshot tasks and limit the number of the concurrently running snapshot tasks [#88209](https://github.com/elastic/elasticsearch/pull/88209) (issue: [#83408](https://github.com/elastic/elasticsearch/issues/83408))

Stats

* Introduce node mappings stats [#89807](https://github.com/elastic/elasticsearch/pull/89807)

TSDS

* Support `match_only_text` for synthetic `_source` [#89516](https://github.com/elastic/elasticsearch/pull/89516)

* Support histogram field for synthetic `_source` [#89833](https://github.com/elastic/elasticsearch/pull/89833)

* Support version field type for synthetic `_source` [#89706](https://github.com/elastic/elasticsearch/pull/89706)

* Build `_id` without reparsing [#88789](https://github.com/elastic/elasticsearch/pull/88789)

* Return metric fields in the field caps API [#88695](https://github.com/elastic/elasticsearch/pull/88695)

Transform

* Add an unattended mode setting to transform [#89212](https://github.com/elastic/elasticsearch/pull/89212)

### New features

Authorization

* Introduce the new `read_security` cluster privilege [#89790](https://github.com/elastic/elasticsearch/pull/89790) (issue: [#89245](https://github.com/elastic/elasticsearch/issues/89245))

Health

* Enable the health node and the disk health indicator [#90085](https://github.com/elastic/elasticsearch/pull/90085) (issue: [#84811](https://github.com/elastic/elasticsearch/issues/84811))

Infra/Core

* Provide tracing implementation using OpenTelemetry and APM Java agent [#88443](https://github.com/elastic/elasticsearch/pull/88443) (issue: [#84369](https://github.com/elastic/elasticsearch/issues/84369))

Infra/Plugins

* Add the stable Plugin API module and analysis interfaces [#88775](https://github.com/elastic/elasticsearch/pull/88775)

Machine Learning

* Make `bucket_correlation` aggregation generally available [#88655](https://github.com/elastic/elasticsearch/pull/88655)

* Make `bucket_count_ks_test` aggregation generally available [#88657](https://github.com/elastic/elasticsearch/pull/88657)

Security

* Support bulk updates of API keys [#88856](https://github.com/elastic/elasticsearch/pull/88856)

TSDS

* Add a TSID global ordinal to `TimeSeriesIndexSearcher` [#90035](https://github.com/elastic/elasticsearch/pull/90035)

* Release time series data stream functionality [#90116](https://github.com/elastic/elasticsearch/pull/90116) (issue: [#74660](https://github.com/elastic/elasticsearch/issues/74660))

* Add synthetic `_source` support for the `ignore_above` parameter on `keyword` fields [#89466](https://github.com/elastic/elasticsearch/pull/89466)

Vector Search

* Add synthetic `_source` support for `dense_vector` [#89840](https://github.com/elastic/elasticsearch/pull/89840)

### Regressions

Infra/Scripting

* Fix fields API caching regression [#90017](https://github.com/elastic/elasticsearch/pull/90017)

### Upgrades

Client

* Upgrade Apache Commons Logging to 1.2 [#85745](https://github.com/elastic/elasticsearch/pull/85745) (issue: [#40305](https://github.com/elastic/elasticsearch/issues/40305))

Packaging

* Upgrade bundled JDK to Java 19 [#90571](https://github.com/elastic/elasticsearch/pull/90571)