**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 6.8.21

Also see [Breaking changes in 6.8](breaking-changes-6.8.html).

### Security updates

* A high severity vulnerability
([CVE-2021-44228](https://cve.mitre.org/cgi-bin/cvename.cgi?name=2021-44228)) for
[Apache Log4j 2](https://logging.apache.org/log4j/2.x/) versions 2.0 to 2.14 was
disclosed publicly on the project’s
[GitHub](https://github.com/apache/logging-log4j2/pull/608) on December 9, 2021.

For information about affected Elasticsearch versions and mitigation steps, see our
related
[security
announcement](https://discuss.elastic.co/t/apache-log4j2-remote-code-execution-rce-vulnerability-cve-2021-44228-esa-2021-31/291476).

### Enhancements

Infra/Logging

* Disable JNDI lookups via the `log4j2.formatMsgNoLookups` system property [#81622](https://github.com/elastic/elasticsearch/pull/81622)

* Patch log4j jar to remove the `JndiLookup` class from the classpath [#81629](https://github.com/elastic/elasticsearch/pull/81629)