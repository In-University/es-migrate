**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.17

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Security updates

* An uncontrolled recursion vulnerability that could lead to a
denial of service attack was identified in the Elasticsearch Grok parser.
A user with the ability to submit arbitrary queries to Elasticsearch could create
a malicious Grok query that will crash the Elasticsearch node.
All versions of Elasticsearch prior to 6.8.17 are affected by this flaw.
You must upgrade to Elasticsearch version 6.8.17 to obtain the fix.
[CVE-2021-22144](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-22144)

### Bug fixes

Features/Ingest

* Improve circular reference detection in grok processor [#74581](https://github.com/elastic/elasticsearch/pull/74581)