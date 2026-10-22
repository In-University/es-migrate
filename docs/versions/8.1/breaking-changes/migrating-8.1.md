**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 8.1

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.1.

See also [*What’s new in 8.17*](release-highlights.html) and [Release notes](es-release-notes.html).

### Breaking changes

The following changes in Elasticsearch 8.1 might affect your applications
and prevent them from operating normally.
Before upgrading to 8.1, review these changes and take the described steps
to mitigate the impact.

#### REST API changes

The search API’s `fields` parameter now normalizes geometry objects that cross the international dateline

**Details**

The search API’s `fields` parameter now normalizes `geo_shape` objects that
cross the international dateline (+/-180° longitude). For example, if a polygon
crosses the dateline, the `fields` parameter returns it as two polygons. You can
still retrieve original, unnormalized geometry objects from `_source`.

**Impact**

If your application requires unnormalized geometry objects, retrieve them from
`_source` rather than using the `fields` parameter.

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.1
and will be removed in a future version.
While this won’t have an immediate impact on your applications,
we strongly encourage you take the described steps to update your code
after upgrading to 8.1.

To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Cluster and node setting deprecations

Legacy values for the `discovery.type` setting are deprecated

**Details**

Legacy values for the `discovery.type` setting are deprecated and will be
forbidden in a future version.

**Impact**

Do not set `discovery.type` to any value except `single-node` or `multi-node`.
All other values are equivalent to the default discovery type which is
`multi-node`. Where possible, omit this setting so that Elasticsearch uses the default
discovery type.

#### REST API deprecations

Lenient parsing of bulk actions is deprecated

**Details**

Older versions of Elasticsearch parse the action lines of bulk requests very permissively
and would silently ignore invalid or malformed actions. This lenience is
deprecated and a future version will reject bulk requests containing invalid
actions.

**Impact**

Ensure that bulk actions are well-formed JSON objects containing a single entry
with the correct key.

Deprecate `index_include_frozen` request parameter in `_sql` API

**Details**

Following the deprecation of frozen indices, the `index_include_frozen`
parameter and `FROZEN` syntax is now also deprecated.

**Impact**

You should unfreeze frozen indices using the
[unfreeze index API](/guide/en/elasticsearch/reference/8.17/unfreeze-index-api.html) and stop using the
`index_include_frozen` parameter or the `FROZEN` keyword in SQL
queries. For some use cases, the frozen tier may be a suitable
replacement for frozen indices. See [data tiers](/guide/en/elasticsearch/reference/8.17/data-tiers.html)
for more information.