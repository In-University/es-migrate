**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.1

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Enhancements

Java High Level REST Client

* Added param ignore_throttled=false when indicesOptions.ignoreThrottle [#42393](https://github.com/elastic/elasticsearch/pull/42393) (issue: [#42358](https://github.com/elastic/elasticsearch/issues/42358))

### Bug fixes

Allocation

* Avoid bubbling up failures from a shard that is recovering [#42287](https://github.com/elastic/elasticsearch/pull/42287) (issues: [#30919](https://github.com/elastic/elasticsearch/issues/30919), [#40107](https://github.com/elastic/elasticsearch/issues/40107))

Authentication

* Only index into "doc" type in security index [#42563](https://github.com/elastic/elasticsearch/pull/42563) (issue: [#42562](https://github.com/elastic/elasticsearch/issues/42562))

Distributed

* Do not use ifSeqNo for update requests on mixed cluster [#42596](https://github.com/elastic/elasticsearch/pull/42596) (issue: [#42561](https://github.com/elastic/elasticsearch/issues/42561))

* Avoid unnecessary persistence of retention leases [#42299](https://github.com/elastic/elasticsearch/pull/42299)

* Execute actions under permit in primary mode only [#42241](https://github.com/elastic/elasticsearch/pull/42241) (issues: [#40386](https://github.com/elastic/elasticsearch/issues/40386), [#41686](https://github.com/elastic/elasticsearch/issues/41686))

Engine

* Account soft deletes for committed segments [#43126](https://github.com/elastic/elasticsearch/pull/43126) (issue: [#43103](https://github.com/elastic/elasticsearch/issues/43103))

Infra/Core

* scheduleAtFixedRate would hang [#42993](https://github.com/elastic/elasticsearch/pull/42993) (issue: [#38441](https://github.com/elastic/elasticsearch/issues/38441))

* Only ignore IOException when fsyncing on dirs [#42972](https://github.com/elastic/elasticsearch/pull/42972) (issue: [#42950](https://github.com/elastic/elasticsearch/issues/42950))

* Deprecation info for joda-java migration [#41956](https://github.com/elastic/elasticsearch/pull/41956) (issue: [#42010](https://github.com/elastic/elasticsearch/issues/42010))

Machine Learning

* Fix possible race condition when closing an opening job [#42506](https://github.com/elastic/elasticsearch/pull/42506)

Mapping

* Fix possible NPE in put mapping validators [#43000](https://github.com/elastic/elasticsearch/pull/43000) (issue: [#37675](https://github.com/elastic/elasticsearch/issues/37675))

Percolator

* Fixed ignoring name parameter for percolator queries [#42598](https://github.com/elastic/elasticsearch/pull/42598) (issue: [#40405](https://github.com/elastic/elasticsearch/issues/40405))

* Exclude nested documents [#42554](https://github.com/elastic/elasticsearch/pull/42554) (issue: [#42361](https://github.com/elastic/elasticsearch/issues/42361))

Recovery

* Recovery with syncId should verify seqno infos [#41265](https://github.com/elastic/elasticsearch/pull/41265)

Reindex

* Remote reindex failure parse fix [#42928](https://github.com/elastic/elasticsearch/pull/42928)

Rollup

* Fix max boundary for rollup jobs that use a delay [#42158](https://github.com/elastic/elasticsearch/pull/42158)

SQL

* Fix wrong results when sorting on aggregate [#43154](https://github.com/elastic/elasticsearch/pull/43154) (issue: [#42851](https://github.com/elastic/elasticsearch/issues/42851))

* Cover the Integer type when extracting values from _source [#42859](https://github.com/elastic/elasticsearch/pull/42859) (issue: [#42858](https://github.com/elastic/elasticsearch/issues/42858))

Search

* SearchRequest#allowPartialSearchResults does not handle successful retries [#43095](https://github.com/elastic/elasticsearch/pull/43095) (issue: [#40743](https://github.com/elastic/elasticsearch/issues/40743))

* Fix auto fuzziness in query_string query [#42897](https://github.com/elastic/elasticsearch/pull/42897)

* Wire query cache into sorting nested-filter computation [#42906](https://github.com/elastic/elasticsearch/pull/42906) (issue: [#42813](https://github.com/elastic/elasticsearch/issues/42813))

* Fix sorting on nested field with unmapped [#42451](https://github.com/elastic/elasticsearch/pull/42451) (issue: [#33644](https://github.com/elastic/elasticsearch/issues/33644))

* Fixes a bug in AnalyzeRequest.toXContent() [#42795](https://github.com/elastic/elasticsearch/pull/42795) (issues: [#39670](https://github.com/elastic/elasticsearch/issues/39670), [#42197](https://github.com/elastic/elasticsearch/issues/42197))

* Fix concurrent search and index delete [#42621](https://github.com/elastic/elasticsearch/pull/42621) (issue: [#28053](https://github.com/elastic/elasticsearch/issues/28053))

Snapshot/Restore

* Fix Azure List by Prefix Bug [#42713](https://github.com/elastic/elasticsearch/pull/42713)