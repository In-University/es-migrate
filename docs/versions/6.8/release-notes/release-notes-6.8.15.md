**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.15

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Security updates

* A document disclosure flaw was found in the Elasticsearch suggester and
profile API when Document and Field Level Security are enabled.
The suggester and profile API are normally disabled for an index when document
level security is enabled on the index. Certain queries are able to enable the
profiler and suggester which could lead to disclosing the existence of documents
and fields the attacker should not be able to view.
All versions of Elasticsearch before 6.8.15 and 7.11.2 are affected by this flaw.
You must upgrade to 6.8.15 or 7.11.2 to obtain the fix.
[CVE-2021-22137](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-22137)

### Enhancements

Authorization

* Improve shard-level request cache efficiency [#69505](https://github.com/elastic/elasticsearch/pull/69505)

### Upgrades

Packaging

* Upgrade to Java Native Access (JNA) 5.7.0-1 [#69653](https://github.com/elastic/elasticsearch/pull/69653)