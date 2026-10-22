**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 8.17.7

Coming in 8.17.7.

Also see [Breaking changes in 8.17](migrating-8.17.html#breaking-changes-8.17).

### Breaking changes

Snapshot/Restore

* Make S3 custom query parameter optional [#128043](https://github.com/elastic/elasticsearch/pull/128043)

### Bug fixes

Audit

* Handle streaming request body in audit log [#127798](https://github.com/elastic/elasticsearch/pull/127798)

Downsampling

* Downsampling does not consider passthrough fields as dimensions [#127752](https://github.com/elastic/elasticsearch/pull/127752) (issue: [#125156](https://github.com/elastic/elasticsearch/issues/125156))

Infra/Scripting

* Avoid nested docs in painless execute api [#127991](https://github.com/elastic/elasticsearch/pull/127991) (issue: [#41004](https://github.com/elastic/elasticsearch/issues/41004))

Relevance

* Fix: Add `NamedWriteable` for `RuleQueryRankDoc` [#128153](https://github.com/elastic/elasticsearch/pull/128153) (issue: [#126071](https://github.com/elastic/elasticsearch/issues/126071))

Security

* Remove dangling spaces wherever found [#127475](https://github.com/elastic/elasticsearch/pull/127475)

TSDB

* Skip the validation when retrieving the index mode during reindexing a time series data stream [#127824](https://github.com/elastic/elasticsearch/pull/127824)