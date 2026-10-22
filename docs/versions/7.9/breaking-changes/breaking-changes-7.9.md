**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 7.9

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.9.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

* [Indices changes](breaking-changes-7.9.html#breaking_79_indices_changes)

* [Script cache changes](breaking-changes-7.9.html#breaking_79_script_cache_changes)

* [Settings changes](breaking-changes-7.9.html#breaking_79_settings_changes)

### Indices changes

Elasticsearch includes built-in index templates for `logs-*-*` and `metrics-*-*`.

**Details**

In 7.9, Elasticsearch added built-in index templates for the `metrics-*-*` and
`logs-*-*` index patterns, each with a priority of `100`.
[Elastic Agent](/guide/en/fleet/7.17/fleet-overview.html) uses these templates to
create data streams.

**Impact**

If you use Elastic Agent, assign your index templates a priority
lower than `100` to avoid overriding the built-in templates.

Otherwise, to avoid accidentally applying the built-in templates, use a
non-overlapping index pattern or assign templates with an overlapping pattern a
`priority` higher than `100`.

For example, if you don’t use Elastic Agent and want to use a template for the
`logs-*` index pattern, assign your template a priority of `200`. This ensures
your template is applied instead of the built-in template for `logs-*-*`.

To disable all built-in index and component templates, set
[`stack.templates.enabled`](/guide/en/elasticsearch/reference/7.17/index-management-settings.html#stack-templates-enabled)
to `false` in [`elasticsearch.yml`](/guide/en/elasticsearch/reference/7.17/settings.html#config-files-location)
before start up. If the templates already exist, this setting ensures Elasticsearch does
not recreate the built-in templates after deletion.

### Script cache changes

The `script.cache.max_size` setting is deprecated.

**Details**

The `script.cache.max_size` setting is deprecated. In Elasticsearch 8.0.0, this is
set per-context.

**Impact**

To avoid deprecation warnings, discontinue use of the `script.cache.max_size`
setting. You may use `script.context.$CONTEXT.cache_max_size` for the particular context.
For example, for the `ingest` context, use `script.context.ingest.cache_max_size`.

The `script.cache.expire` setting is deprecated.

**Details**

The `script.cache.expire` setting is deprecated. In Elasticsearch 8.0.0, this is
set per-context.

**Impact**

To avoid deprecation warnings, discontinue use of the `script.cache.expire`
setting. You may use `script.context.$CONTEXT.cache_expire` for the particular context.
For example, for the `update` context, use `script.context.update.cache_expire`.

The `script.max_compilations_rate` setting is deprecated.

**Details**

The `script.max_compilations_rate` setting is deprecated. In Elasticsearch 8.0.0, this is
set per-context.

**Impact**

To avoid deprecation warnings, discontinue use of the `script.max_compilations_rate`
setting. You may use `script.context.$CONTEXT.max_compilations_rate` for the particular
context.  For example, for the `processor_conditional` context, use
`script.context.processor_conditional.max_compilations_rate`.

Mapping actions have been deprecated for the `create_doc`, `create`, `index` and `write` privileges.

**Details**

In Elasticsearch 8.0.0, the following privileges will no longer allow users to
explicitly update the mapping of an index:

* `create_doc`

* `create`

* `index`

* `write`

Additionally, in Elasticsearch 8.0.0, the following privileges will no longer allow users to
[dynamically update the mapping](/guide/en/elasticsearch/reference/7.17/dynamic-mapping.html) of an index
during indexing or ingest:

* `create_doc`

* `create`

* `index`

These privileges will continue to allow mapping actions on indices (but not on data streams) until
Elasticsearch 8.0.0. However, deprecation warnings will be returned.

**Impact**

To allow users to explicitly update the mapping of an index,
grant the `manage` privilege.

To dynamically update the mapping of an index during indexing or
ingest, grant the `auto_configure` privilege and use index templates. This lets
you dynamically update the index mapping based on the template’s mapping configuration.

### Settings changes

Automatically importing dangling indices is disabled by default.

**Details**

Automatically importing [dangling indices](modules-gateway.html#dangling-indices) into the cluster
is unsafe and is now disabled by default. This feature will be removed entirely
in Elasticsearch 8.0.0.

**Impact**

Use the [Dangling indices API](indices.html#dangling-indices-api) to list, delete or import
any dangling indices manually.

Alternatively you can enable automatic imports of dangling indices, recovering
the unsafe behaviour of earlier versions, by setting
`gateway.auto_import_dangling_indices` to `true`. This setting is deprecated
and will be removed in Elasticsearch 8.0.0. We do not recommend using this setting.

Several node role settings are deprecated.

**Details**

The following node role settings are now deprecated:

* `node.data`

* `node.ingest`

* `node.master`

* `node.ml`

* `node.remote_cluster_client`

* `node.transform`

* `node.voting_only`

Use the [`node.roles` setting](/guide/en/elasticsearch/reference/7.17/modules-node.html#node-roles) instead.

If you used the deprecated node role settings on a 7.13 or later cluster, you
will have a [deprecation log message](/guide/en/elasticsearch/reference/7.17/logging.html#deprecation-logging) on
each of your nodes indicating the exact replacement value for `node.roles`.

**Impact**

To avoid deprecation warnings, discontinue use of the deprecated settings.