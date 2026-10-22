**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.4

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Enhancements

Engine

* Limit number of retaining translog files for peer recovery [#47414](https://github.com/elastic/elasticsearch/pull/47414)

Infra/Settings

* Add more meaningful keystore version mismatch errors [#46291](https://github.com/elastic/elasticsearch/pull/46291) (issue: [#44624](https://github.com/elastic/elasticsearch/issues/44624))

Machine Learning

* Throttle the delete-by-query of expired results [#47177](https://github.com/elastic/elasticsearch/pull/47177) (issues: [#47003](https://github.com/elastic/elasticsearch/issues/47003))

### Bug fixes

Authentication

* Fallback to realm authc if ApiKey fails [#46538](https://github.com/elastic/elasticsearch/pull/46538)

CRUD

* Do not use ifSeqNo if doc does not have seq_no [#46198](https://github.com/elastic/elasticsearch/pull/46198)

Distributed

* Fix false positive out of sync warning in synced-flush [#46576](https://github.com/elastic/elasticsearch/pull/46576) (issues: [#28464](https://github.com/elastic/elasticsearch/issues/28464), [#30244](https://github.com/elastic/elasticsearch/issues/30244))

* Suppress warning logs from background sync on relocated primary [#46247](https://github.com/elastic/elasticsearch/pull/46247) (issues: [#40800](https://github.com/elastic/elasticsearch/issues/40800), [#42241](https://github.com/elastic/elasticsearch/issues/42241))

Engine

* Improve translog corruption detection [#47873](https://github.com/elastic/elasticsearch/pull/47873) (issues: [#41480](https://github.com/elastic/elasticsearch/issues/41480), [#42744](https://github.com/elastic/elasticsearch/issues/42744), [#42980](https://github.com/elastic/elasticsearch/issues/42980), [#44217](https://github.com/elastic/elasticsearch/issues/44217))

* Always rebuild checkpoint tracker for old indices [#46340](https://github.com/elastic/elasticsearch/pull/46340) (issues: [#38879](https://github.com/elastic/elasticsearch/issues/38879), [#46311](https://github.com/elastic/elasticsearch/issues/46311))

Features/Indices APIs

* Fix Rollover error when alias has closed indices [#47839](https://github.com/elastic/elasticsearch/pull/47839) (issue: [#47148](https://github.com/elastic/elasticsearch/issues/47148))

Features/Ingest

* Allow dropping documents with auto-generated ID [#46773](https://github.com/elastic/elasticsearch/pull/46773) (issue: [#46678](https://github.com/elastic/elasticsearch/issues/46678))

Features/Watcher

* Watcher - workaround for potential deadlock [#47603](https://github.com/elastic/elasticsearch/pull/47603) (issues: [#41451](https://github.com/elastic/elasticsearch/issues/41451), [#47599](https://github.com/elastic/elasticsearch/issues/47599))

* Fix class used to initialize logger in Watcher [#46467](https://github.com/elastic/elasticsearch/pull/46467)

Machine Learning

* Reinstate ML daily maintenance actions [#47103](https://github.com/elastic/elasticsearch/pull/47103) (issue: [#47003](https://github.com/elastic/elasticsearch/issues/47003))

* Fix two datafeed flush lockup bugs [#46982](https://github.com/elastic/elasticsearch/pull/46982)

* Throw an error when a datafeed needs CCS but it is not enabled for the node [#46044](https://github.com/elastic/elasticsearch/pull/46044)

* Fix possibility of crash when calculating forecasts that overflow to disk [#688](https://github.com/elastic/ml-cpp/pull/688)

SQL

* SQL: Allow whitespaces in escape patterns [#47577](https://github.com/elastic/elasticsearch/pull/47577) (issue: [#47401](https://github.com/elastic/elasticsearch/issues/47401))

* SQL: Fix issue with common type resolution [#46565](https://github.com/elastic/elasticsearch/pull/46565) (issue: [#46551](https://github.com/elastic/elasticsearch/issues/46551))

* SQL: wrong number of values for columns [#42122](https://github.com/elastic/elasticsearch/pull/42122)

Snapshot/Restore

* Fix Bug in Azure Repo Exception Handling [#47968](https://github.com/elastic/elasticsearch/pull/47968)

* Fix Snapshot Corruption in Edge Case [#47552](https://github.com/elastic/elasticsearch/pull/47552) (issues: [#46250](https://github.com/elastic/elasticsearch/issues/46250), [#47550](https://github.com/elastic/elasticsearch/issues/47550))

* Fix TransportSnapshotsStatusAction ThreadPool Use [#45824](https://github.com/elastic/elasticsearch/pull/45824)

### Upgrades

Engine

* Upgrade to lucene 7.7.2 [#47901](https://github.com/elastic/elasticsearch/pull/47901)