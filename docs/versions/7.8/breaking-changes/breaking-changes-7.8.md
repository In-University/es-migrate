**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 7.8

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.8.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

* [License Information changes](breaking-changes-7.8.html#breaking_781_license_changes)

* [Aggregation changes](breaking-changes-7.8.html#breaking_78_aggregation_changes)

* [Mappings changes](breaking-changes-7.8.html#breaking_78_mappings_changes)

* [Settings changes](breaking-changes-7.8.html#breaking_78_settings_changes)

### License Information changes

As of the `7.8.1` release

Displays Enterprise license as Platinum in /_xpack

**Details**
The `GET /_license` endpoint displays Enterprise licenses as
Platinum by default so that old clients (including Beats, Kibana and
Logstash) know to interpret this new license type as if it were a
Platinum license.

This compatibility layer was not applied to the `GET /_xpack/`
endpoint, which also displays a license type and mode. [#58217](https://github.com/elastic/elasticsearch/pull/58217)

### Aggregation changes

Privilege `indices:admin/create` will no longer allow the auto creation of indices

**Details**
The privilege named `indices:admin/create` will no longer allow the auto
creation of indices. Use `create_index` instead. [#55858](https://github.com/elastic/elasticsearch/pull/55858)

`value_count` aggregation optimization

**Details**
Scripts used in `value_count` will now receive a number if they are
counting a numeric field and a `GeoPoint` if they are counting a
`geo_point` fields.  They used to always receive the `String`
representation of those values.  [#54854](https://github.com/elastic/elasticsearch/pull/54854)

### Mappings changes

The `enabled` mapping parameter cannot be changed for a root mapping.

**Details**

Mapping requests that attempt to change the [`enabled`](/guide/en/elasticsearch/reference/7.17/enabled.html)
mapping parameter for a root mapping will fail and return an error.

Previously, Elasticsearch accepted mapping requests that attempted to change the
`enabled` parameter of the root mapping. Theses changes were not applied, but
such requests didn’t return an error.

**Impact**

To avoid errors, do not submit mapping requests that change the
[`enabled`](/guide/en/elasticsearch/reference/7.17/enabled.html) mapping parameter.

The `include_in_parent` and `include_in_root` mapping parameters cannot be changed for `nested` fields.

**Details**

Mapping requests that attempt to change the
[`include_in_parent`](/guide/en/elasticsearch/reference/7.17/nested.html#nested-include-in-parent-parm) or
[`include_in_root`](/guide/en/elasticsearch/reference/7.17/nested.html#nested-include-in-root-parm) mapping
parameter for a `nested` field will fail and return an error.

Previously, Elasticsearch accepted mapping requests that attempted to change the
`include_in_parent` or `include_in_root` parameter. Theses changes were not
applied, but such requests didn’t return an error.

**Impact**

To avoid errors, do not submit mapping requests that change the
[`include_in_parent`](/guide/en/elasticsearch/reference/7.17/nested.html#nested-include-in-parent-parm) or
[`include_in_root`](/guide/en/elasticsearch/reference/7.17/nested.html#nested-include-in-root-parm) mapping
parameter.

The get field mapping API’s `local` query parameter is deprecated.

**Details**

The [get field mapping API](/guide/en/elasticsearch/reference/7.17/indices-get-field-mapping.html)'s `local` query
parameter is deprecated and will be removed in Elasticsearch 8.0.0.

The `local` parameter is a no-op. The API always retrieves field mappings
locally.

**Impact**

To avoid deprecation warnings, discontinue use of the `local` parameter.

### Settings changes

The `node.local_storage` setting is deprecated.

**Details**

The `node.local_storage` setting is deprecated. In Elasticsearch 8.0.0, all nodes require
local storage.

**Impact**

To avoid deprecation warnings, discontinue use of the `node.local_storage`
setting.

Several X-Pack settings no longer have any effect and are deprecated.

**Details**

Basic X-Pack license features are always enabled for the default distribution
and the following settings no longer have any effect:

* `xpack.enrich.enabled`

* `xpack.flattened.enabled`

* `xpack.ilm.enabled`

* `xpack.monitoring.enabled`

* `xpack.rollup.enabled`

* `xpack.slm.enabled`

* `xpack.sql.enabled`

* `xpack.transform.enabled`

* `xpack.vectors.enabled`

Previously, they could be set to `false` to disable the feature’s APIs in a cluster.

**Impact**

To avoid deprecation warnings, discontinue use of these settings.
If you have disabled ILM so that you can use another tool to manage Watcher
indices, the newly introduced `xpack.watcher.use_ilm_index_management` setting
may be set to false.

#### Changes to built-in users

The `kibana` user has been deprecated in favor of the `kibana_system` user.

**Details**

The `kibana` user was historically used to authenticate Kibana to Elasticsearch.
The name of this user was confusing, and was often mistakenly used to login to Kibana.
We’ve replaced the `kibana` user with the `kibana_system` user to reduce
confusion and to better align with other built-in system accounts.

**Impact**

If your `kibana.yml` used to contain:

```
elasticsearch.username: kibana
```

then you should update to use the new `kibana_system` user instead:

```
elasticsearch.username: kibana_system
```

The new `kibana_system` user does not preserve the previous `kibana`
user password. You must explicitly set a password for the `kibana_system` user.

#### Changes to built-in roles

The `kibana_user` role has been deprecated in favor of the `kibana_admin` role.

**Details**

Users who were previously assigned the `kibana_user` role should instead be assigned
the `kibana_admin` role. This role grants the same set of privileges as `kibana_user`, but has been
renamed to better reflect its intended use.

**Impact**

Assign users with the `kibana_user` role to the `kibana_admin` role.
Discontinue use of the `kibana_user` role.

### Cluster coordination changes

The voting configuration exclusions API’s `POST _cluster/voting_config_exclusions/<node_name>` request path is deprecated.

**Details**

The voting configuration exclusions API’s
`POST _cluster/voting_config_exclusions/<node_name>` request path is now
deprecated. To add a voting configuration exclusion, specify node names or node
IDs using a query parameter instead:

* `POST _cluster/voting_config_exclusions?node_names=<node_names>`

* `POST _cluster/voting_config_exclusions?node_ids=<node_ids>`

**Impact**

To avoid deprecation warnings, discontinue use of the
`POST _cluster/voting_config_exclusions/<node_name>` request path.

### Transforms changes

The `max_page_search_size` property is deprecated in the `pivot` transform configuration object

**Details**

The `max_page_search_size` property within `pivot` is deprecated in the
[create transform](put-transform.html) and [preview transform](preview-transform.html)
APIs.

**Impact**

Use the `max_page_search_size` property within `settings` instead.