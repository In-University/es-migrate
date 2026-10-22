**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.24

Also see [Breaking changes in 7.17](migrating-7.17.html#breaking-changes-7.17).

### Bug fixes

Authentication

* Improve security-crypto threadpool overflow handling [#111369](https://github.com/elastic/elasticsearch/pull/111369)

Geo

* Add maximum nested depth check to WKT parser [#111843](https://github.com/elastic/elasticsearch/pull/111843)

Snapshot/Restore

* Fix `NullPointerException` in shard snapshot code [#111524](https://github.com/elastic/elasticsearch/pull/111524)