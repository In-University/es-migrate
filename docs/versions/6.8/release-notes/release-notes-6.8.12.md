**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.12

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Security updates

* A field disclosure flaw was found in Elasticsearch when running a scrolling search with
field level security. If a user runs the same query another more privileged user
recently ran, the scrolling search can leak fields that should be hidden. This
could result in an attacker gaining additional permissions against a restricted
index. All versions of Elasticsearch before 7.9.0 and 6.8.12 are affected by this flaw.
You must upgrade to Elasticsearch version 7.9.0 or 6.8.12 to obtain the fix.
[CVE-2020-7019](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-7019)

### Bug fixes

CCR

* CCR recoveries using wrong setting for chunk sizes [#59597](https://github.com/elastic/elasticsearch/pull/59597)

* Fix synchronization in ShardFollowNodeTask [#60490](https://github.com/elastic/elasticsearch/pull/60490)

* Relax ShardFollowTasksExecutor validation [#60054](https://github.com/elastic/elasticsearch/pull/60054) (issue: [#59625](https://github.com/elastic/elasticsearch/issues/59625))

* Set timeout of master node requests on follower to unbounded [#60070](https://github.com/elastic/elasticsearch/pull/60070) (issue: [#56891](https://github.com/elastic/elasticsearch/issues/56891))

Distributed

* Fix cluster health rest api wait_for_no_initializing_shards bug [#58379](https://github.com/elastic/elasticsearch/pull/58379)

Machine Learning

* Fix restoration of change detectors after seasonality change [#1391](https://github.com/elastic/ml-cpp/pull/1391)