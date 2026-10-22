**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 6.7

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 6.7.

* [Indexing changes](breaking-changes-6.7.html#breaking_67_indexing_changes)

* [Plugin changes](breaking-changes-6.7.html#breaking_67_plugin_changes)

* [Settings changes](breaking-changes-6.7.html#breaking_67_settings_changes)

* [API changes](breaking-changes-6.7.html#breaking_67_api_changes)

* [Security changes](breaking-changes-6.7.html#breaking_67_security_changes)

See also [Release Highlights](release-highlights.html) and [Release Notes](es-release-notes.html).

### Indexing changes

#### Deprecated usage of `internal` versioning for optimistic concurrency control

`internal` version may not uniquely identify a document’s version if an indexed document
wasn’t fully replicated when a primary fails. As such it is unsafe to use for
optimistic concurrency control, is deprecated and the option will no longer be available
in Elasticsearch 7.0.0. Please use the `if_seq_no` and `if_primary_term` parameters instead.
See [*Optimistic concurrency control*](optimistic-concurrency-control.html) for more details.

### Plugin changes

#### `ingest-geoip` and `ingest-user-agent` are no longer distributed as plugins

The `ingest-geoip` and `ingest-user-agent` plugins have been converted to
modules and are now included with all Elasticsearch distributions. Starting with
Elasticsearch 6.7.0, attempting to install or remove these plugins will result
in a no-op. In Elasticsearch 7.0.0, attempting to install or remove these plugins
will result in an error. Additionally, there are two minor breaking changes here:
- `elasticsearch-plugin list` will no longer output `ingest-geoip` nor
  `ingest-user-agent`
- `plugin.mandatory` is no longer compatible with `ingest-geoip` nor
  `ingest-user-agent`

Elasticsearch 6.7.0 checks that there are no leftover geoip database files in
the plugin configuration directory because the new module does not use them.
Therefore, remove the `ingest-geoip` plugin prior to upgrading to 6.7.0 with
the `--purge` option to also delete the old database files:

```
./bin/elasticsearch-plugin remove --purge ingest-geoip
```

Otherwise you will see the following error message upon startup (assuming
`/etc/elasticsearch/ingest-geoip` as the plugin configuration directory):

```
expected database [GeoLite2-ASN.mmdb] to not exist in [/etc/elasticsearch/ingest-geoip]
```

### Settings changes

#### Disabling memory-mapping

The setting `node.store.allow_mmapfs` has been deprecated. Use
`node.store.allow_mmap` instead.

### API changes

#### Removing compressed size of cluster state

Since 6.0.0, the `/_cluster/state` REST endpoint and cluster state API on the
transport client would compute and return the compressed size of the cluster
state as if it were serialized for inter-node communication. This metric would
be returned in the `compressed_size` or `compressed_size_in_bytes` fields in the
REST endpoint, or `ClusterStateResponse#getTotalCompressedSize` via the
transport client. Computing this field is expensive, and has dubious reporting
value as it does not reflect the actual size of the cluster state on disk. The
expense of computing this field is such that in some situations it can disrupt
all activity on a node including indexing activity. Therefore we have elected to
by default stop computing this field in a minor release. We are providing a
backwards compatibility flag via the system property
`-Des.cluster_state.size=true` which will return to the previous 6.0.0—​6.6.2
behavior.  Computing this metric and displaying this field will be completely
removed in 7.0.0, and using this backwards compatibility flag will fail.

### Security changes

#### Removed support for pre v6.2 tokens

The token service no longer accepts tokens that were generated on an Elasticsearch version
earlier than 6.2.0

No applications in the Elastic Stack made use of Elasticsearch tokens prior to 6.2.0, so this
change does not affect access to Kibana or any official Elasticsearch clients.
If you have an application that uses Elasticsearch tokens, and a token from 6.1 or earlier
is presented for authentication, Elasticsearch will reject the token with a `401` status code.