**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.3

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Enhancements

CCR

* Include leases in error message when operations no longer available [#45681](https://github.com/elastic/elasticsearch/pull/45681)

Infra/Core

* Add OCI annotations and adjust existing annotations [#45167](https://github.com/elastic/elasticsearch/pull/45167)

Infra/Settings

* Normalize environment paths [#45179](https://github.com/elastic/elasticsearch/pull/45179) (issue: [#45176](https://github.com/elastic/elasticsearch/issues/45176))

### Bug fixes

Aggregations

* Fix early termination of aggregators that run with breadth-first mode [#44963](https://github.com/elastic/elasticsearch/pull/44963) (issue: [#44909](https://github.com/elastic/elasticsearch/issues/44909))

Allocation

* Avoid overshooting watermarks during relocation [#46079](https://github.com/elastic/elasticsearch/pull/46079) (issue: [#45177](https://github.com/elastic/elasticsearch/issues/45177))

CCR

* Clean up ShardFollowTasks for deleted indices [#44702](https://github.com/elastic/elasticsearch/pull/44702) (issue: [#34404](https://github.com/elastic/elasticsearch/issues/34404))

CRUD

* Allow _update on write alias [#45318](https://github.com/elastic/elasticsearch/pull/45318) (issue: [#31520](https://github.com/elastic/elasticsearch/issues/31520))

Distributed

* Ensure AsyncTask#isScheduled remain false after close [#45687](https://github.com/elastic/elasticsearch/pull/45687) (issue: [#45576](https://github.com/elastic/elasticsearch/issues/45576))

Engine

* Handle delete document level failures [#46100](https://github.com/elastic/elasticsearch/pull/46100)

* Handle no-op document level failures [#46083](https://github.com/elastic/elasticsearch/pull/46083)

Features/Indices APIs

* Check shard limit after applying index templates [#44619](https://github.com/elastic/elasticsearch/pull/44619) (issue: [#44567](https://github.com/elastic/elasticsearch/issues/44567))

* Prevent NullPointerException in TransportRolloverAction [#43353](https://github.com/elastic/elasticsearch/pull/43353) (issue: [#43296](https://github.com/elastic/elasticsearch/issues/43296))

Features/Java High Level REST Client

* Add rest_total_hits_as_int in HLRC’s search requests [#46076](https://github.com/elastic/elasticsearch/pull/46076) (issue: [#43925](https://github.com/elastic/elasticsearch/issues/43925))

Infra/Core

* Add default CLI JVM options [#44545](https://github.com/elastic/elasticsearch/pull/44545) (issue: [#42021](https://github.com/elastic/elasticsearch/issues/42021))

Infra/Plugins

* Do not checksum all bytes at once in plugin install [#44649](https://github.com/elastic/elasticsearch/pull/44649) (issue: [#44545](https://github.com/elastic/elasticsearch/issues/44545))

SQL

* Fix URI path being lost in case of hosted ES scenario [#44776](https://github.com/elastic/elasticsearch/pull/44776) (issue: [#44721](https://github.com/elastic/elasticsearch/issues/44721))

* Interval arithmetics failure [#42014](https://github.com/elastic/elasticsearch/pull/42014) (issue: [#41200](https://github.com/elastic/elasticsearch/issues/41200))

Search

* Prevent Leaking Search Tasks on Exceptions in FetchSearchPhase and DfsQueryPhase [#45500](https://github.com/elastic/elasticsearch/pull/45500)

Security

* Use system context for looking up connected nodes [#43991](https://github.com/elastic/elasticsearch/pull/43991) (issue: [#43974](https://github.com/elastic/elasticsearch/issues/43974))

### Upgrades

Infra/Packaging

* Upgrade to JDK 12.0.2 [#45172](https://github.com/elastic/elasticsearch/pull/45172)