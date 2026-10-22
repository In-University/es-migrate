**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.19

Also see [Breaking changes in 7.17](migrating-7.17.html#breaking-changes-7.17).

### Known issues

* Due to a bug in the bundled JDK 22 nodes might crash abruptly under high memory pressure.
We recommend [downgrading to JDK 21.0.2](install-elasticsearch.html#jvm-version) asap to mitigate the issue.

* The deprecated `index.mapper.dynamic` setting can break your cluster. It can only
be set using the **Update index settings API**. Symptoms include nodes failing to start
or shards failing to allocate. Do not use this setting in versions prior to 7.17.22.
The bug is fixed in 7.17.22.
(issue: [#109160](https://github.com/elastic/elasticsearch/issues/109160))

### Bug fixes

Ingest Node

* Adding `executedPipelines` to the `IngestDocument` copy constructor [#105427](https://github.com/elastic/elasticsearch/pull/105427)

Machine Learning

* Detect 8.x ML nodes correctly [#105653](https://github.com/elastic/elasticsearch/pull/105653)

Search

* Force execution of `SearchService.Reaper` [#106544](https://github.com/elastic/elasticsearch/pull/106544) (issue: [#106543](https://github.com/elastic/elasticsearch/issues/106543))

* Update to latest Lucene bugfix version 8.11.3 [#106365](https://github.com/elastic/elasticsearch/pull/106365)

Watcher

* Handling exceptions on watcher reload [#105442](https://github.com/elastic/elasticsearch/pull/105442) (issue: [#69842](https://github.com/elastic/elasticsearch/issues/69842))

### Enhancements

Ingest Node

* Adding a custom exception for problems with the graph of pipelines to be applied to a document [#105196](https://github.com/elastic/elasticsearch/pull/105196)

* Improving the performance of the ingest simulate verbose API [#105265](https://github.com/elastic/elasticsearch/pull/105265)

* Limiting the number of nested pipelines that can be executed [#105428](https://github.com/elastic/elasticsearch/pull/105428)

### Upgrades

Infra/Core

* Upgrade joda time to 2.12.6 [#104720](https://github.com/elastic/elasticsearch/pull/104720)

Ingest Node

* Upgrade mime4j on the 7.17 line [#106380](https://github.com/elastic/elasticsearch/pull/106380)