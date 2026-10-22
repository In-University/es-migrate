**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.18

Also see [Breaking changes in 7.17](migrating-7.17.html#breaking-changes-7.17).

### Known issues

* The deprecated `index.mapper.dynamic` setting can break your cluster. It can only
be set using the **Update index settings API**. Symptoms include nodes failing to start
or shards failing to allocate. Do not use this setting in versions prior to 7.17.22.
The bug is fixed in 7.17.22.
(issue: [#109160](https://github.com/elastic/elasticsearch/issues/109160))

### Bug fixes

Ingest Node

* Better handling of async processor failures [#104289](https://github.com/elastic/elasticsearch/pull/104289) (issue: [#101921](https://github.com/elastic/elasticsearch/issues/101921))

* Ingest correctly handle upsert operations and drop processors together [#104585](https://github.com/elastic/elasticsearch/pull/104585) (issue: [#36746](https://github.com/elastic/elasticsearch/issues/36746))

Snapshot/Restore

* Fix deleting index during snapshot finalization [#103817](https://github.com/elastic/elasticsearch/pull/103817) (issue: [#101029](https://github.com/elastic/elasticsearch/issues/101029))

### Upgrades

Snapshot/Restore

* [7x] upgrade aws client depdencies [#104346](https://github.com/elastic/elasticsearch/pull/104346)