**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.13

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Enhancements

Features/Java Low Level REST Client

* Add simple support for gzip compression [#63230](https://github.com/elastic/elasticsearch/pull/63230) (issue: [#62044](https://github.com/elastic/elasticsearch/issues/62044))

### Bug fixes

Audit

* Move RestRequestFilter to core [#63507](https://github.com/elastic/elasticsearch/pull/63507)

Authorization

* Ensure authz operation overrides transient authz headers [#61621](https://github.com/elastic/elasticsearch/pull/61621)

* Relax the index access control check for scroll searches [#61446](https://github.com/elastic/elasticsearch/pull/61446)

CCR

* CCR should retry on CircuitBreakingException [#62013](https://github.com/elastic/elasticsearch/pull/62013) (issue: [#55633](https://github.com/elastic/elasticsearch/issues/55633))

* Retry CCR shard follow task when no seed node left [#63225](https://github.com/elastic/elasticsearch/pull/63225)

* Set timeout of auto put-follow request to unbounded [#61679](https://github.com/elastic/elasticsearch/pull/61679) (issue: [#56891](https://github.com/elastic/elasticsearch/issues/56891))

Features/Java High Level REST Client

* Add hlrc_rest_total_hits_as_int parameter in scroll request [#61685](https://github.com/elastic/elasticsearch/pull/61685) (issue: [#61677](https://github.com/elastic/elasticsearch/issues/61677))

### Upgrades

Infra/Packaging

* Upgrade the bundled JDK to JDK 15 [#62580](https://github.com/elastic/elasticsearch/pull/62580)