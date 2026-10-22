**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.7

Also see [Breaking changes in 7.17](migrating-7.17.html#breaking-changes-7.17).

### Known issues

* Parsing a request when the last element in an array is filtered out
(for instance using `_source_includes`) fails. This
is due to [a bug in Jackson parser](https://github.com/FasterXML/jackson-core/issues/882).
Fixed in Elasticsearch 8.6.1 ([#91456](https://github.com/elastic/elasticsearch/pull/92480))

* The deprecated `index.mapper.dynamic` setting can break your cluster. It can only
be set using the **Update index settings API**. Symptoms include nodes failing to start
or shards failing to allocate. Do not use this setting in versions prior to 7.17.22.
The bug is fixed in 7.17.22.
(issue: [#109160](https://github.com/elastic/elasticsearch/issues/109160))

### Bug fixes

Allocation

* Fix debug mode in `MaxRetryAllocationDecider` [#89973](https://github.com/elastic/elasticsearch/pull/89973)

Authentication

* Fix double sending of response in `TransportOpenIdConnectPrepareAuthenticationAction` [#89930](https://github.com/elastic/elasticsearch/pull/89930)

ILM+SLM

* Copy `isHidden` during ILM alias swap [#89650](https://github.com/elastic/elasticsearch/pull/89650) (issue: [#89604](https://github.com/elastic/elasticsearch/issues/89604))

Infra/Core

* Extend the date rounding logic to be conditional [#89693](https://github.com/elastic/elasticsearch/pull/89693) (issues: [#89096](https://github.com/elastic/elasticsearch/issues/89096), [#58986](https://github.com/elastic/elasticsearch/issues/58986))

* Fix date rounding for date math parsing [#90458](https://github.com/elastic/elasticsearch/pull/90458) (issue: [#90187](https://github.com/elastic/elasticsearch/issues/90187))

Ingest Node

* Fix pipeline id not being present in ingest metadata inside `on_failure` block [#89632](https://github.com/elastic/elasticsearch/pull/89632)

Machine Learning

* Do not retain categorization tokens when existing category matches [#2398](https://github.com/elastic/ml-cpp/pull/2398)

Network

* Fix memory leak when double invoking `RestChannel.sendResponse` [#89873](https://github.com/elastic/elasticsearch/pull/89873)

Ranking

* Avoid negative scores with `cross_fields` type [#89016](https://github.com/elastic/elasticsearch/pull/89016) (issue: [#44700](https://github.com/elastic/elasticsearch/issues/44700))

Rollup

* Fork `TransportRollupCapsAction` to management threadpool [#89803](https://github.com/elastic/elasticsearch/pull/89803)

Search

* Safeguard `RegExp` use against `StackOverflowError` [#84624](https://github.com/elastic/elasticsearch/pull/84624) (issue: [#82923](https://github.com/elastic/elasticsearch/issues/82923))

Watcher

* Allow `xpack.notification.email.account.domain_allowlist` to be set dynamically [#90426](https://github.com/elastic/elasticsearch/pull/90426) (issue: [#89913](https://github.com/elastic/elasticsearch/issues/89913))

* Handling timeout exceptions on watcher startup [#90421](https://github.com/elastic/elasticsearch/pull/90421) (issue: [#44981](https://github.com/elastic/elasticsearch/issues/44981))

### Upgrades

Packaging

* Update OpenJDK to 18.0.2.1 [#89535](https://github.com/elastic/elasticsearch/pull/89535) (issue: [#89531](https://github.com/elastic/elasticsearch/issues/89531))

* Upgrade bundled JDK to Java 19 [#90571](https://github.com/elastic/elasticsearch/pull/90571)