**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.2

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Enhancements

Machine Learning

* Improve message when native controller cannot connect [#43565](https://github.com/elastic/elasticsearch/pull/43565) (issue: [#42341](https://github.com/elastic/elasticsearch/issues/42341))

* Introduce a setting for the process connect timeout [#43234](https://github.com/elastic/elasticsearch/pull/43234)

Ranking

* Fix parameter value for calling `data.advanceExact` [#44205](https://github.com/elastic/elasticsearch/pull/44205)

Snapshot/Restore

* Add SAS token authentication support to Azure Repository plugin [#42982](https://github.com/elastic/elasticsearch/pull/42982) (issue: [#42117](https://github.com/elastic/elasticsearch/issues/42117))

### Bug fixes

Allocation

* Do not copy initial recovery filter during an index split [#44053](https://github.com/elastic/elasticsearch/pull/44053) (issue: [#43955](https://github.com/elastic/elasticsearch/issues/43955))

Analysis

* Fix varying responses for `<index>/_analyze` request [#44342](https://github.com/elastic/elasticsearch/pull/44342) (issues: [#44078](https://github.com/elastic/elasticsearch/issues/44078), [#44284](https://github.com/elastic/elasticsearch/issues/44284))

CCR

* Skip update if leader and follower settings are identical [#44535](https://github.com/elastic/elasticsearch/pull/44535) (issue: [#44521](https://github.com/elastic/elasticsearch/issues/44521))

* Avoid stack overflow in auto-follow coordinator [#44421](https://github.com/elastic/elasticsearch/pull/44421) (issue: [#43251](https://github.com/elastic/elasticsearch/issues/43251))

* Avoid NPE when checking for CCR index privileges [#44397](https://github.com/elastic/elasticsearch/pull/44397) (issue: [#44172](https://github.com/elastic/elasticsearch/issues/44172))

Engine

* Preserve thread context in AsyncIOProcessor [#43729](https://github.com/elastic/elasticsearch/pull/43729)

Features/ILM

* Fix swapped variables in error message [#44300](https://github.com/elastic/elasticsearch/pull/44300)

* Account for node versions during allocation in ILM shrink [#43300](https://github.com/elastic/elasticsearch/pull/43300) (issue: [#41879](https://github.com/elastic/elasticsearch/issues/41879))

* Narrow period of shrink action in which ILM prevents stopping [#43254](https://github.com/elastic/elasticsearch/pull/43254) (issue: [#43253](https://github.com/elastic/elasticsearch/issues/43253))

Features/Indices APIs

* Validate index settings after applying templates [#44612](https://github.com/elastic/elasticsearch/pull/44612) (issues: [#34021](https://github.com/elastic/elasticsearch/issues/34021), [#44567](https://github.com/elastic/elasticsearch/issues/44567))

Features/Stats

* Return 0 for negative "free" and "total" memory reported by the OS [#42725](https://github.com/elastic/elasticsearch/pull/42725) (issue: [#42157](https://github.com/elastic/elasticsearch/issues/42157))

Machine Learning

* Fix ML memory tracker lockup when inner step fails [#44158](https://github.com/elastic/elasticsearch/pull/44158) (issue: [#44156](https://github.com/elastic/elasticsearch/issues/44156))

* Fix datafeed checks when a concrete remote index is present [#43923](https://github.com/elastic/elasticsearch/pull/43923) (issue: [#42113](https://github.com/elastic/elasticsearch/issues/42113))

* Don’t write model size stats when job is closed without any input [#512](https://github.com/elastic/ml-cpp/pull/512) (issue: [#394](https://github.com/elastic/ml-cpp/issues/394))

* Don’t persist model state at the end of lookback if the lookback did not generate any input [#521](https://github.com/elastic/ml-cpp/pull/521) (issue: [#519](https://github.com/elastic/ml-cpp/issues/519))

Mapping

* Prevent types deprecation warning for indices.exists requests [#43963](https://github.com/elastic/elasticsearch/pull/43963) (issue: [#43905](https://github.com/elastic/elasticsearch/issues/43905))

* Add `include_type_name` in `indices.exists` REST API specification [#43910](https://github.com/elastic/elasticsearch/pull/43910) (issue: [#43905](https://github.com/elastic/elasticsearch/issues/43905))

Network

* Reconnect remote cluster when seeds are changed [#43379](https://github.com/elastic/elasticsearch/pull/43379) (issue: [#37799](https://github.com/elastic/elasticsearch/issues/37799))

SQL

* Handle the edge case of an empty array of values to return from source [#43868](https://github.com/elastic/elasticsearch/pull/43868) (issue: [#43863](https://github.com/elastic/elasticsearch/issues/43863))

* Fix NPE in case of subsequent scrolled requests for a CSV/TSV formatted response [#43365](https://github.com/elastic/elasticsearch/pull/43365) (issue: [#43327](https://github.com/elastic/elasticsearch/issues/43327))

* Increase hard limit for sorting on aggregates [#43220](https://github.com/elastic/elasticsearch/pull/43220) (issue: [#43168](https://github.com/elastic/elasticsearch/issues/43168))

Search

* Fix wrong logic in `match_phrase` query with multi-word synonyms [#43941](https://github.com/elastic/elasticsearch/pull/43941) (issue: [#43308](https://github.com/elastic/elasticsearch/issues/43308))

Security

* Do not swallow I/O exception getting authentication [#44398](https://github.com/elastic/elasticsearch/pull/44398) (issues: [#44172](https://github.com/elastic/elasticsearch/issues/44172), [#44397](https://github.com/elastic/elasticsearch/issues/44397))

* `SecurityIndexSearcherWrapper` doesn’t always carry over caches and similarity [#43436](https://github.com/elastic/elasticsearch/pull/43436)