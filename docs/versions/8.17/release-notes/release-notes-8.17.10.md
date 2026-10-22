**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.17.10

Also see [Breaking changes in 8.17](migrating-8.17.html#breaking-changes-8.17).

### Bug fixes

Aggregations

* Aggs: Add validation to Bucket script pipeline agg [#132320](https://github.com/elastic/elasticsearch/pull/132320) (issue: [#132272](https://github.com/elastic/elasticsearch/issues/132272))

ES|QL

* FIx Driver creating status with a live list of operators [#132260](https://github.com/elastic/elasticsearch/pull/132260) (issue: [#131564](https://github.com/elastic/elasticsearch/issues/131564))

### Upgrades

Ingest Node

* Updating tika to 2.9.3 [#127353](https://github.com/elastic/elasticsearch/pull/127353)