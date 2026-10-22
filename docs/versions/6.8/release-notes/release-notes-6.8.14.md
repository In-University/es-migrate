**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.14

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Security updates

* Elasticsearch versions before 7.10.0 and 6.8.14 have an information
disclosure issue when audit logging and the `emit_request_body` option are
enabled. The Elasticsearch audit log could contain sensitive information,
such as password hashes or authentication tokens. This could allow an
Elasticsearch administrator to view these details.
You must upgrade to Elasticsearch version 6.8.14 to obtain the fix.
[CVE-2020-7021](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-7021)

### Bug fixes

CCR

* Stop renew retention leases when follow task fails [#65168](https://github.com/elastic/elasticsearch/pull/65168)

Engine

* Fix the version and term field initialization error of `NoOpResult` [#66269](https://github.com/elastic/elasticsearch/pull/66269) (issue: [#66267](https://github.com/elastic/elasticsearch/issues/66267))

Features/Monitoring

* Do not report negative values for swap sizes [#57317](https://github.com/elastic/elasticsearch/pull/57317) (issue: [#57312](https://github.com/elastic/elasticsearch/issues/57312))

Infra/Core

* Fix missing `QuotaPath.unwrap()` instances [#67165](https://github.com/elastic/elasticsearch/pull/67165) (issue: [#67164](https://github.com/elastic/elasticsearch/issues/67164))

Machine learning

* Fixes missing state in persist and restore for anomaly detection. This caused
suboptimal modeling after a job was closed and reopened or failed over to a
different node [#1668](https://github.com/elastic/ml-cpp/pull/1668)

Network

* Ensure notify when proxy connections disconnect [#65697](https://github.com/elastic/elasticsearch/pull/65697) (issue: [#65443](https://github.com/elastic/elasticsearch/issues/65443))

Search

* Do not wrap `can_match` searchers [#64742](https://github.com/elastic/elasticsearch/pull/64742)

### Upgrades

Packaging

* Upgrade bundled jdk to 15.0.1 and switch back to `AdoptOpenJDK` [#64253](https://github.com/elastic/elasticsearch/pull/64253) (issue: [#64026](https://github.com/elastic/elasticsearch/issues/64026))