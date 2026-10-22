**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 6.6

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 6.6.

* [API changes](breaking-changes-6.6.html#breaking_66_api_changes)

* [Mappings changes](breaking-changes-6.6.html#breaking_66_mapping_changes)

* [Search changes](breaking-changes-6.6.html#breaking_66_search_changes)

* [Settings changes](breaking-changes-6.6.html#breaking_66_setting_changes)

See also [Release Highlights](release-highlights.html) and [Release Notes](es-release-notes.html).

### API changes

#### Machine learning API changes

The get jobs API and get job stats API can retrieve a maximum of 10,000 jobs.
Likewise, the get datafeeds API and get datafeed stats API can retrieve a
maximum of 10,000 datafeeds. Prior to version 6.6, there were no limits on the
results from these APIs.

#### Watcher API changes

If you used the `metric` parameter with the
[stats API](/guide/en/elasticsearch/reference/6.8/watcher-api-stats.html), the response contained incorrect labels,
which are fixed in 6.6 and later releases. If you choose to retrieve
`queued_watches` metrics, it now returns a `queued_watches` list instead of a  `current_watches` list. Likewise, if you retrieve `pending_watches` metrics, it
returns a `current_watches` list instead of a `queued_watches` list. The
`pending_watches` metric is deprecated; use `current_watches` instead.

### Search changes

#### `query_string`, `multi_match` and `simple_query_string` query

Using automatically expanded fields for the "all fields" mode ("default_field": "*")
for the `query_string`, `multi_match` and `simple_query_string` now raises a warning and
a deprecation notice to be logged for queries beyond a certain number of fields. This limit
will be enforced with a hard error starting in 7.0 and is determined by the
`indices.query.bool.max_clause_count` setting which defaults to 1024.

#### Deprecate `_source_exclude` and `_source_include` URL Parameters

`_source_exclude` and `_source_include` are deprecated in favor of
`_source_excludes` and `_source_includes` because those line up better with the
rest of Elasticsearc’s APIs and Elasticsearch will raise a deprecation warning
if those are used on any APIs. We plan to drop support for `_source_exclude` and
`_source_include` in 7.0.

#### Deprecate boosts on inner span queries.

Setting `boost` on inner span queries is deprecated. In the next major version
setting `boost` on inner span queries will throw a parsing exception.

#### Deprecate `.values` and `.getValues()` on doc values in scripts

In scripts `.values` and `.getValues()` hasn’t been needed for a long, long
time because the doc values objects themselves are Lists. So instead of:

```
GET /stackoverflow/_search
{
  "script_fields": {
    "tags_count": {
      "script" : {
        "source": "doc['tags'].values.size()"
      }
    }
  }
}
```

do

```
GET /stackoverflow/_search
{
  "script_fields": {
    "tags_count": {
      "script" : {
        "source": "doc['tags'].size()"
      }
    }
  }
}
```

### Settings changes

#### Watcher notifications account settings

The following settings have been deprecated and the secure variants should
be used instead. The [secure settings](secure-settings.html) have to be defined
inside each cluster node’s keystore, i.e., they are not to be specified via
the cluster settings API.

* `xpack.notification.email.account.<id>.smtp.password`, instead use
`xpack.notification.email.account.<id>.smtp.secure_password`

* `xpack.notification.hipchat.account.<id>.auth_token`, instead use
`xpack.notification.hipchat.account.<id>.secure_auth_token`

* `xpack.notification.jira.account.<id>.url`, instead use
`xpack.notification.jira.account.<id>.secure_url`

* `xpack.notification.jira.account.<id>.user`, instead use
`xpack.notification.jira.account.<id>.secure_user`

* `xpack.notification.jira.account.<id>.password`, instead use
`xpack.notification.jira.account.<id>.secure_password`

* `xpack.notification.pagerduty.account.<id>.service_api_key`, instead use
`xpack.notification.pagerduty.account.<id>.secure_service_api_key`

* `xpack.notification.slack.account.<id>.url`, instead use
`xpack.notification.slack.account.<id>.secure_url`

### Mappings changes

#### Changed default `geo_shape` indexing strategy

`geo_shape` types now default to using a vector indexing approach based on Lucene’s new
`LatLonShape` field type. This indexes shapes as a triangular mesh instead of decomposing
them into individual grid cells. To index using legacy prefix trees the `tree` parameter
must be explicitly set to one of `quadtree` or `geohash`. Note that these strategies are
now deprecated and will be removed in a future version.

The impact of changing the default indexing strategy is as follows:

* `CONTAINS` queries are not yet supported

* `geo_shape` query does not support querying by `MULTIPOINT` type

* `LINESTRING` and `MULTILINESTRING` queries do not yet support `WITHIN` relations

**IMPORTANT NOTE**: If you are using any of the features listed above, newly created indexes
with default `geo_shape` type (e.g., templates) might no longer work. It is recommended
to update the `geo_shape` field mapping to explicitly define the `tree` parameter to one of
`geohash` or `quadtree`. This will ensure newly created indexes are feature compatible with
previously created indexes.

#### deprecated `geo_shape` parameters

The following type parameters are deprecated for the `geo_shape` field type: `tree`,
`precision`, `tree_levels`, `distance_error_pct`, `points_only`, and `strategy`. They
will be removed in a future version.