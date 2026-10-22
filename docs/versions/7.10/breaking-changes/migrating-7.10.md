**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 7.10

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.10.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

* [Authentication changes](migrating-7.10.html#breaking_710_security_changes)

* [Java changes](migrating-7.10.html#breaking_710_java_changes)

* [Networking changes](migrating-7.10.html#breaking_710_networking_changes)

* [Search changes](migrating-7.10.html#breaking_710_search_changes)

* [Cluster deprecations](migrating-7.10.html#breaking_710_cluster_deprecations)

* [Indices deprecations](migrating-7.10.html#breaking_710_indices_changes)

* [Machine learning deprecations](migrating-7.10.html#breaking_710_ml_changes)

* [Mapping deprecations](migrating-7.10.html#breaking_710_mapping_changes)

* [Snapshot and restore deprecations](migrating-7.10.html#breaking_710_snapshot_restore_changes)

### Breaking changes

The following changes in Elasticsearch 7.10 might affect your applications
and prevent them from operating normally.
Before upgrading to 7.10, review these changes and take the described steps
to mitigate the impact.

Breaking changes introduced in minor versions are
normally limited to security and bug fixes.
Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Authentication changes

API keys now require a `name` property.

**Details**

The `name` property is now required to create or grant an API key.

```
{
    "...": "...",
    "api_key": {
      "name": "key-1"
    }
}
```

**Impact**

To avoid errors, specify the `name` property when creating or granting API keys.

#### Java changes

The `MappedFieldType#fielddataBuilder` method now accepts a `Supplier<SearchLookup>` argument.

**Details**

To support future feature development, the existing
`MappedFieldType#fielddataBuilder` method now accepts a new
`Supplier<SearchLookup>` argument.

**Impact**

If you develop or maintain a mapper plugin, update your implementation of the
`MappedFieldType#fielddataBuilder` method to accommodate the new signature.

#### Networking changes

The `*.tcp.keep_idle` and `*.tcp.keep_interval` settings are now limited to `300` seconds.

**Details**

The `{network,transport,http}.tcp.keep_idle` and
`{network,transport,http}.tcp.keep_interval` settings now have a maximum
value of `300` seconds, equivalent to 5 minutes.

**Impact**

If specified, ensure the `{network,transport,http}.tcp.keep_idle` and
`{network,transport,http}.tcp.keep_interval` settings do not exceed `300`
seconds. Setting `{network,transport,http}.tcp.keep_idle` or
`{network,transport,http}.tcp.keep_interval` to a value greater than `300`
seconds in `elasticsearch.yml` will result in an error on startup.

#### Search changes

The `index.max_docvalue_fields_search` setting now limits doc value fields returned by `inner_hits` or the `top_hits` aggregation.

**Details**

The `index.max_docvalue_fields_search` setting limits the number of doc value
fields retrieved by a search. Previously, this setting applied only to doc value
fields returned by the `docvalue_fields` parameter in a top-level search. The
setting now also applies to doc value fields returned by an `inner_hits` section
or `top_hits` aggregation.

**Impact**

If you use `inner_hits` or the `top_hits` aggregation, ensure
`index.max_docvalue_fields_search` is configured correctly for your use case.

### Deprecations

The following functionality has been deprecated in Elasticsearch 7.10
and will be removed in 8.0
While this won’t have an immediate impact on your applications,
we strongly encourage you take the described steps to update your code
after upgrading to 7.10.

Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Cluster deprecations

The `cluster.join.timeout` setting is deprecated.

**Details**

The `cluster.join.timeout` node setting is deprecated and will be removed in
8.0. In 7.x clusters, join attempts no longer time out.

**Impact**

To avoid deprecation warnings, discontinue use of the setting.

#### Indices deprecations

REST API access to system indices is deprecated.

**Details**

We are deprecating REST API access to system indices. Most REST API requests
that attempt to access system indices will return the following deprecation
warning:

```
this request accesses system indices: [.system_index_name], but in a future
major version, direct access to system indices will be prevented by default
```

The following REST API endpoints access system indices as part of their
implementation and will not return the deprecation warning:

* `GET _cluster/health`

* `GET {index}/_recovery`

* `GET _cluster/allocation/explain`

* `GET _cluster/state`

* `POST _cluster/reroute`

* `GET {index}/_stats`

* `GET {index}/_segments`

* `GET {index}/_shard_stores`

* `GET _cat/[indices,aliases,health,recovery,shards,segments]`

**Impact**

To avoid deprecation warnings, do not use unsupported REST APIs to access system
indices.

#### Machine learning deprecations

The `allow_no_jobs` and `allow_no_datafeeds` API parameters are deprecated.

**Details**

The `allow_no_jobs` and `allow_no_datafeeds` parameters in machine learning APIs are
deprecated in favor of `allow_no_match`. The old parameters are still accepted
by the APIs but a deprecation warning is emitted when the old parameter name is
used in the request body or as a request parameter. High-level REST client
classes now send the new `allow_no_match` parameter.

**Impact**

To avoid deprecation warnings, use the `allow_no_match` parameter.

#### Mapping deprecations

The `boost` parameter on field mappings has been deprecated.

**Details**

Index-time boosts have been deprecated since the 5.x line, but it is still possible
to declare field-specific boosts in the mappings.  This is now deprecated as well,
and will be removed entirely in 8.0.0.  Mappings containing field boosts will continue
to work in 7.x but will emit a deprecation warning.

**Impact**

The `boost` setting should be removed from templates and mappings. Use boosts
directly on queries instead.

#### Snapshot and restore deprecations

The repository stats API has been deprecated.

**Details**

The repository stats API was introduced as an experimental API in 7.8.0. The
[repositories metering APIs](/guide/en/elasticsearch/reference/7.17/repositories-metering-apis.html) now replace the
repository stats API. The repository stats API has been deprecated and will be
removed in 8.0.0.

**Impact**

Use the [repositories metering APIs](/guide/en/elasticsearch/reference/7.17/repositories-metering-apis.html).
Discontinue use of the repository stats API.