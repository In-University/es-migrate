## Migrating to 8.1

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.1.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

### Breaking changes

The following changes in Elasticsearch 8.1 might affect your applications
and prevent them from operating normally.
Before upgrading to 8.1, review these changes and take the described steps
to mitigate the impact.

#### REST API changes

.The search API's `fields` parameter now normalizes geometry objects that cross the international dateline
[%collapsible]
====
*Details* +
The search API's `fields` parameter now normalizes `geo_shape` objects that
cross the international dateline (+/-180° longitude). For example, if a polygon
crosses the dateline, the `fields` parameter returns it as two polygons. You can
still retrieve original, unnormalized geometry objects from `_source`.

*Impact* +
If your application requires unnormalized geometry objects, retrieve them from
`_source` rather than using the `fields` parameter.
====

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.1
and will be removed in a future version.
While this won't have an immediate impact on your applications,
we strongly encourage you take the described steps to update your code
after upgrading to 8.1.

To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

#### Cluster and node setting deprecations

.Legacy values for the `discovery.type` setting are deprecated
[%collapsible]
====
*Details* +
Legacy values for the `discovery.type` setting are deprecated and will be
forbidden in a future version.

*Impact* +
Do not set `discovery.type` to any value except `single-node` or `multi-node`.
All other values are equivalent to the default discovery type which is
`multi-node`. Where possible, omit this setting so that Elasticsearch uses the default
discovery type.
====

#### REST API deprecations

.Lenient parsing of bulk actions is deprecated
[%collapsible]
====
*Details* +
Older versions of Elasticsearch parse the action lines of bulk requests very permissively
and would silently ignore invalid or malformed actions. This lenience is
deprecated and a future version will reject bulk requests containing invalid
actions.

*Impact* +
Ensure that bulk actions are well-formed JSON objects containing a single entry
with the correct key.
====

.Deprecate `index_include_frozen` request parameter in `_sql` API
[%collapsible]
====
*Details* +
Following the deprecation of frozen indices, the `index_include_frozen`
parameter and `FROZEN` syntax is now also deprecated.

*Impact* +
You should unfreeze frozen indices using the
{ref}/unfreeze-index-api.html[unfreeze index API] and stop using the
`index_include_frozen` parameter or the `FROZEN` keyword in SQL
queries. For some use cases, the frozen tier may be a suitable
replacement for frozen indices. See {ref}/data-tiers.html[data tiers]
for more information.
====