**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Elasticsearch version 7.17.25

Also see [Breaking changes in 7.17](migrating-7.17.html#breaking-changes-7.17).

### Enhancements

Infra/Scripting

* Add a `mustache.max_output_size_bytes` setting to limit the length of results from mustache scripts [#114002](https://github.com/elastic/elasticsearch/pull/114002)

### Upgrades

Snapshot/Restore

* Upgrade protobufer to 3.25.5 [#113869](https://github.com/elastic/elasticsearch/pull/113869)