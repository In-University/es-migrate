**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 7.0

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.0.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

* [Aggregations changes](breaking-changes-7.0.html#breaking_70_aggregations_changes)

* [Cluster changes](breaking-changes-7.0.html#breaking_70_cluster_changes)

* [Discovery changes](breaking-changes-7.0.html#breaking_70_discovery_changes)

* [Indices changes](breaking-changes-7.0.html#breaking_70_indices_changes)

* [API changes](breaking-changes-7.0.html#breaking_70_ingest_changes)

* [Mapping changes](breaking-changes-7.0.html#breaking_70_mappings_changes)

* [ML changes](breaking-changes-7.0.html#breaking_70_ml_changes)

* [Search and Query DSL changes](breaking-changes-7.0.html#breaking_70_search_changes)

* [Suggesters changes](breaking-changes-7.0.html#breaking_70_suggesters_changes)

* [Packaging changes](breaking-changes-7.0.html#breaking_70_packaging_changes)

* [Plugins changes](breaking-changes-7.0.html#breaking_70_plugins_changes)

* [Analysis changes](breaking-changes-7.0.html#breaking_70_analysis_changes)

* [API changes](breaking-changes-7.0.html#breaking_70_api_changes)

* [Java API changes](breaking-changes-7.0.html#breaking_70_java_changes)

* [Settings changes](breaking-changes-7.0.html#breaking_70_settings_changes)

* [Scripting changes](breaking-changes-7.0.html#breaking_70_scripting_changes)

* [Snapshot stats changes](breaking-changes-7.0.html#breaking_70_snapshotstats_changes)

* [High-level REST client changes](breaking-changes-7.0.html#breaking_70_restclient_changes)

* [Low-level REST client changes](breaking-changes-7.0.html#breaking_70_low_level_restclient_changes)

* [Logging changes](breaking-changes-7.0.html#breaking_70_logging_changes)

* [Node start up](breaking-changes-7.0.html#breaking_70_node_changes)

* [Replacing Joda-Time with java time](breaking-changes-7.0.html#breaking_70_java_time_changes)

### Indices created before 7.0

Elasticsearch 7.0 can read indices created in version 6.0 or above.  An
Elasticsearch 7.0 node will not start in the presence of indices created in a
version of Elasticsearch before 6.0.

Reindex indices from Elasticsearch 5.x or before

Indices created in Elasticsearch 5.x or before will need to be reindexed with
Elasticsearch 6.x in order to be readable by Elasticsearch 7.x.

### Aggregations changes

#### Deprecated `global_ordinals_hash` and `global_ordinals_low_cardinality` execution hints for terms aggregations have been removed

These `execution_hint` are removed and should be replaced by `global_ordinals`.

#### `search.max_buckets` in the cluster setting

The dynamic cluster setting named `search.max_buckets` now defaults
to 10,000 (instead of unlimited in the previous version).
Requests that try to return more than the limit will fail with an exception.

#### `missing` option of the `composite` aggregation has been removed

The `missing` option of the `composite` aggregation, deprecated in 6.x,
has been removed. `missing_bucket` should be used instead.

#### Replaced `params._agg` with `state` context variable in scripted metric aggregations

The object used to share aggregation state between the scripts in a Scripted Metric
Aggregation is now a variable called `state` available in the script context, rather than
being provided via the `params` object as `params._agg`.

#### Make metric aggregation script parameters `reduce_script` and `combine_script` mandatory

The metric aggregation has been changed to require these two script parameters to ensure users are
explicitly defining how their data is processed.

#### `percentiles` and `percentile_ranks` now return `null` instead of `NaN`

The `percentiles` and `percentile_ranks` aggregations used to return `NaN` in
the response if they were applied to an empty set of values. Because `NaN` is
not officially supported by JSON, it has been replaced with `null`.

#### `stats` and `extended_stats` now return 0 instead of `null` for zero docs

When the `stats` and `extended_stats` aggregations collected zero docs (`doc_count: 0`),
their value would be `null`.  This was in contrast with the `sum` aggregation which
would return `0`.  The `stats` and `extended_stats` aggs are now consistent with
`sum` and also return zero.

### Analysis changes

#### Limiting the number of tokens produced by _analyze

To safeguard against out of memory errors, the number of tokens that can be produced
using the `_analyze` endpoint has been limited to 10000. This default limit can be changed
for a particular index with the index setting `index.analyze.max_token_count`.

#### Limiting the length of an analyzed text during highlighting

Highlighting a text that was indexed without offsets or term vectors,
requires analysis of this text in memory real time during the search request.
For large texts this analysis may take substantial amount of time and memory.
To protect against this, the maximum number of characters that will be analyzed has been
limited to 1000000. This default limit can be changed
for a particular index with the index setting `index.highlight.max_analyzed_offset`.

#### `delimited_payload_filter` renaming

The `delimited_payload_filter` was deprecated and renamed to `delimited_payload` in 6.2.
Using it in indices created before 7.0 will issue deprecation warnings. Using the old
name in new indices created in 7.0 will throw an error. Use the new name `delimited_payload`
instead.

#### `standard` filter has been removed

The `standard` token filter has been removed because it doesn’t change anything in the stream.

#### Deprecated standard_html_strip analyzer

The `standard_html_strip` analyzer has been deprecated, and should be replaced
with a combination of the `standard` tokenizer and `html_strip` char_filter.
Indexes created using this analyzer will still be readable in elasticsearch 7.0,
but it will not be possible to create new indexes using it.

#### The deprecated `nGram` and `edgeNGram` token filter cannot be used on new indices

The `nGram` and `edgeNGram` token filter names have been deprecated in an earlier 6.x version.
Indexes created using these token filters will still be readable in elasticsearch 7.0 but indexing
documents using those filter names will issue a deprecation warning. Using the deprecated names on
new indices starting with version 7.0.0 will be prohibited and throw an error when indexing
or analyzing documents. Both names should be replaced by `ngram` or `edge_ngram` respectively.

#### Limit to the difference between max_size and min_size in NGramTokenFilter and NGramTokenizer

To safeguard against creating too many index terms, the difference between `max_gram` and
`min_gram` in `NGramTokenFilter` and `NGramTokenizer` has been limited to 1. This default
limit can be changed with the index setting `index.max_ngram_diff`. Note that if the limit is
exceeded a error is thrown only for new indices. For existing pre-7.0 indices, a deprecation
warning is logged.

#### Limit to the difference between max_shingle_size and min_shingle_size in ShingleTokenFilter

To safeguard against creating too many tokens, the difference between `max_shingle_size` and
`min_shingle_size` in `ShingleTokenFilter` has been limited to 3. This default
limit can be changed with the index setting `index.max_shingle_diff`. Note that if the limit is
exceeded a error is thrown only for new indices. For existing pre-7.0 indices, a deprecation
warning is logged.

### Cluster changes

#### `:` is no longer allowed in cluster name

Due to cross-cluster search using `:` to separate a cluster and index name,
cluster names may no longer contain `:`.

#### New default for `wait_for_active_shards` parameter of the open index command

The default value for the `wait_for_active_shards` parameter of the open index API
is changed from 0 to 1, which means that the command will now by default wait for all
primary shards of the opened index to be allocated.

#### Shard preferences `_primary`, `_primary_first`, `_replica`, and `_replica_first` are removed

These shard preferences are removed in favour of the `_prefer_nodes` and `_only_nodes` preferences.

#### Cluster-wide shard soft limit

Clusters now have soft limits on the total number of open shards in the cluster
based on the number of nodes and the `cluster.max_shards_per_node` cluster
setting, to prevent accidental operations that would destabilize the cluster.
More information can be found in the [documentation for that setting](misc-cluster.html).

### Discovery changes

#### Cluster bootstrapping is required if discovery is configured

The first time a cluster is started, `cluster.initial_master_nodes` must be set
to perform cluster bootstrapping. It should contain the names of the
master-eligible nodes in the initial cluster and be defined on every
master-eligible node in the cluster. See [the discovery
settings summary](important-settings.html#discovery-settings) for an example, and the
[cluster bootstrapping reference
documentation](modules-discovery-bootstrap-cluster.html) describes this setting in more detail.

The `discovery.zen.minimum_master_nodes` setting is permitted, but ignored, on
7.x nodes.

#### Removing master-eligible nodes sometimes requires voting exclusions

If you wish to remove half or more of the master-eligible nodes from a cluster,
you must first exclude the affected nodes from the voting configuration using
the [voting config exclusions API](modules-discovery-adding-removing-nodes.html).
If you remove fewer than half of the master-eligible nodes at the same time,
voting exclusions are not required.  If you remove only master-ineligible nodes
such as data-only nodes or coordinating-only nodes, voting exclusions are not
required. Likewise, if you add nodes to the cluster, voting exclusions are not
required.

#### Discovery configuration is required in production

Production deployments of Elasticsearch now require at least one of the
following settings to be specified in the `elasticsearch.yml` configuration
file:

* `discovery.seed_hosts`

* `discovery.seed_providers`

* `cluster.initial_master_nodes`

* `discovery.zen.ping.unicast.hosts`

* `discovery.zen.hosts_provider`

The first three settings in this list are only available in versions 7.0 and
above. If you are preparing to upgrade from an earlier version, you must set
`discovery.zen.ping.unicast.hosts` or `discovery.zen.hosts_provider`.

#### New name for `no_master_block` setting

The `discovery.zen.no_master_block` setting is now known as
`cluster.no_master_block`. Any value set for `discovery.zen.no_master_block` is
now ignored. You should remove this setting and, if needed, set
`cluster.no_master_block` appropriately after the upgrade.

#### Reduced default timeouts for fault detection

By default the [cluster fault detection](cluster-fault-detection.html) subsystem
now considers a node to be faulty if it fails to respond to 3 consecutive
pings, each of which times out after 10 seconds. Thus a node that is
unresponsive for longer than 30 seconds is liable to be removed from the
cluster. Previously the default timeout for each ping was 30 seconds, so that
an unresponsive node might be kept in the cluster for over 90 seconds.

#### Master-ineligible nodes are ignored by discovery

In earlier versions it was possible to use master-ineligible nodes during the
discovery process, either as seed nodes or to transfer discovery gossip
indirectly between the master-eligible nodes. Clusters that relied on
master-ineligible nodes like this were fragile and unable to automatically
recover from some kinds of failure. Discovery now involves only the
master-eligible nodes in the cluster so that it is not possible to rely on
master-ineligible nodes like this. You should configure
[`discovery.seed_hosts` or another seed
hosts provider](modules-discovery-hosts-providers.html) to provide the addresses of all the master-eligible nodes in
your cluster.

### API changes

#### Ingest configuration exception information is now transmitted in metadata field

Previously, some ingest configuration exception information about ingest processors
was sent to the client in the HTTP headers, which is inconsistent with how
exceptions are conveyed in other parts of Elasticsearch.

Configuration exception information is now conveyed as a field in the response
body.

#### Ingest plugin special handling has been removed

There was some special handling for installing and removing the `ingest-geoip` and
`ingest-user-agent` plugins after they were converted to modules. This special handling
was done to minimize breaking users in a minor release, and would exit with a status code
zero to avoid breaking automation.

This special handling has now been removed.

### Indices changes

#### Index creation no longer defaults to five shards

Previous versions of Elasticsearch defaulted to creating five shards per index.
Starting with 7.0.0, the default is now one shard per index.

#### `:` is no longer allowed in index name

Due to cross-cluster search using `:` to separate a cluster and index name,
index names may no longer contain `:`.

#### `index.unassigned.node_left.delayed_timeout` may no longer be negative

Negative values were interpreted as zero in earlier versions but are no
longer accepted.

#### `_flush` and `_force_merge` will no longer refresh

In previous versions issuing a `_flush` or `_force_merge` (with `flush=true`)
had the undocumented side-effect of refreshing the index which made new documents
visible to searches and non-realtime GET operations. From now on these operations
don’t have this side-effect anymore. To make documents visible an explicit `_refresh`
call is needed unless the index is refreshed by the internal scheduler.

#### Document distribution changes

Indices created with version `7.0.0` onwards will have an automatic `index.number_of_routing_shards`
value set. This might change how documents are distributed across shards depending on how many
shards the index has. In order to maintain the exact same distribution as a pre `7.0.0` index, the
`index.number_of_routing_shards` must be set to the `index.number_of_shards` at index creation time.
Note: if the number of routing shards equals the number of shards `_split` operations are not supported.

#### Skipped background refresh on search idle shards

Shards belonging to an index that does not have an explicit
`index.refresh_interval` configured will  no longer refresh in the background
once the shard becomes "search idle", ie the shard hasn’t seen any search
traffic for `index.search.idle.after` seconds (defaults to `30s`). Searches
that access a search idle shard will be "parked" until the next refresh
happens.  Indexing requests with `wait_for_refresh` will also trigger
a background refresh.

#### Remove deprecated url parameters for Clear Indices Cache API

The following previously deprecated url parameter have been removed:

* `filter` - use `query` instead

* `filter_cache` - use `query` instead

* `request_cache` - use `request` instead

* `field_data` - use `fielddata` instead

#### `network.breaker.inflight_requests.overhead` increased to 2

Previously the in flight requests circuit breaker considered only the raw byte representation.
By bumping the value of `network.breaker.inflight_requests.overhead` from 1 to 2, this circuit
breaker considers now also the memory overhead of representing the request as a structured object.

#### Parent circuit breaker changes

The parent circuit breaker defines a new setting `indices.breaker.total.use_real_memory` which is
`true` by default. This means that the parent circuit breaker will trip based on currently used
heap memory instead of only considering the reserved memory by child circuit breakers. When this
setting is `true`, the default parent breaker limit also changes from 70% to 95% of the JVM heap size.
The previous behavior can be restored by setting `indices.breaker.total.use_real_memory` to `false`.

#### Field data circuit breaker changes

As doc values have been enabled by default in earlier versions of Elasticsearch,
there is less need for fielddata. Therefore, the default value of the setting
`indices.breaker.fielddata.limit` has been lowered from 60% to 40% of the JVM
heap size.

#### `fix` value for `index.shard.check_on_startup` is removed

Deprecated option value `fix` for setting `index.shard.check_on_startup` is not supported.

#### `elasticsearch-translog` is removed

Use the `elasticsearch-shard` tool to remove corrupted translog data.

### Mapping changes

#### The `_all` metadata field is removed

The `_all` field deprecated in 6 have now been removed.

#### The `_uid` metadata field is removed

This field used to index a composite key formed of the `_type` and the `_id`.
Now that indices cannot have multiple types, this has been removed in favour
of `_id`.

#### The `_default_` mapping is no longer allowed

The `_default_` mapping has been deprecated in 6.0 and is now no longer allowed
in 7.0. Trying to configure a `_default_` mapping on 7.x indices will result in
an error.

If an index template contains a `_default_` mapping, it will fail to create new
indices. To resolve this issue, the `_default_` mapping should be removed from
the template. Note that in 7.x, the [get template API](indices-get-template.html)
does not show the `_default_` mapping by default, even when it is defined in
the mapping. To see all mappings in the template, the `include_type_name`
parameter must be supplied:

```
GET /_template/my_template?include_type_name
```

For more details on the `include_type_name` parameter and other types-related
API changes, please see [*Removal of mapping types*](removal-of-types.html).

#### `index_options` for numeric fields has been removed

The `index_options` field for numeric  fields has been deprecated in 6 and has now been removed.

#### Limiting the number of `nested` json objects

To safeguard against out of memory errors, the number of nested json objects within a single
document across all fields has been limited to 10000. This default limit can be changed with
the index setting `index.mapping.nested_objects.limit`.

#### The `update_all_types` option has been removed

This option is useless now that all indices have at most one type.

#### The `classic` similarity has been removed

The `classic` similarity relied on coordination factors for scoring to be good
in presence of stopwords in the query. This feature has been removed from
Lucene, which means that the `classic` similarity now produces scores of lower
quality. It is advised to switch to `BM25` instead, which is widely accepted
as a better alternative.

#### Similarities fail when unsupported options are provided

An error will now be thrown when unknown configuration options are provided
to similarities. Such unknown parameters were ignored before.

#### Changed default `geo_shape` indexing strategy

`geo_shape` types now default to using a vector indexing approach based on Lucene’s new
`LatLonShape` field type. This indexes shapes as a triangular mesh instead of decomposing
them into individual grid cells. To index using legacy prefix trees the `tree` parameter
must be explicitly set to one of `quadtree` or `geohash`. Note that these strategies are
now deprecated and will be removed in a future version.

IMPORTANT NOTE: If using timed index creation from templates, the `geo_shape` mapping
should also be changed in the template to explicitly define `tree` to one of `geohash`
or `quadtree`. This will ensure compatibility with previously created indexes.

#### Deprecated `geo_shape` parameters

The following type parameters are deprecated for the `geo_shape` field type: `tree`,
`precision`, `tree_levels`, `distance_error_pct`, `points_only`, and `strategy`. They
will be removed in a future version.

#### Limiting the number of completion contexts

The maximum allowed number of completion contexts in a mapping will be limited
to 10 in the next major version. Completion fields that define more than 10
contexts in a mapping will log a deprecation warning in this version.

#### `include_type_name` now defaults to `false`

The default for `include_type_name` is now `false` for all APIs that accept
the parameter.

### ML changes

#### Types in Datafeed config are no longer valid

Types have been removed from the datafeed config and are no longer
valid parameters.

### Search and Query DSL changes

#### Off-heap terms index

The terms dictionary is the part of the inverted index that records all terms
that occur within a segment in sorted order. In order to provide fast retrieval,
terms dictionaries come with a small terms index that allows for efficient
random access by term. Until now this terms index had always been loaded
on-heap.

As of 7.0, the terms index is loaded on-heap for fields that only have unique
values such as `_id` fields, and off-heap otherwise - likely most other fields.
This is expected to reduce memory requirements but might slow down search
requests if both below conditions are met:

* The size of the data directory on each node is significantly larger than the
amount of memory that is available to the filesystem cache.

* The number of matches of the query is not several orders of magnitude greater
than the number of terms that the query tries to match, either explicitly via
`term` or `terms` queries, or implicitly via multi-term queries such as
`prefix`, `wildcard` or `fuzzy` queries.

This change affects both existing indices created with Elasticsearch 6.x and new
indices created with Elasticsearch 7.x.

#### Changes to queries

* The default value for `transpositions` parameter of `fuzzy` query
has been changed to `true`.

* The `query_string` options `use_dismax`, `split_on_whitespace`,
`all_fields`, `locale`, `auto_generate_phrase_query` and
`lowercase_expanded_terms` deprecated in 6.x have been removed.

* Purely negative queries (only MUST_NOT clauses) now return a score of `0`
rather than `1`.

* The boundary specified using geohashes in the `geo_bounding_box` query
now include entire geohash cell, instead of just geohash center.

* Attempts to generate multi-term phrase queries against non-text fields
with a custom analyzer will now throw an exception.

* An `envelope` crossing the dateline in a `geo_shape` query is now processed
correctly when specified using REST API instead of having its left and
right corners flipped.

* Attempts to set `boost` on inner span queries will now throw a parsing exception.

#### Adaptive replica selection enabled by default

Adaptive replica selection has been enabled by default. If you wish to return to
the older round robin of search requests, you can use the
`cluster.routing.use_adaptive_replica_selection` setting:

```
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.use_adaptive_replica_selection": false
  }
}
```

#### Search API returns `400` for invalid requests

The Search API returns `400 - Bad request` while it would previously return
`500 - Internal Server Error` in the following cases of invalid request:

* the result window is too large

* sort is used in  combination with rescore

* the rescore window is too large

* the number of slices is too large

* keep alive for scroll is too large

* number of filters in the adjacency matrix aggregation is too large

* script compilation errors

#### Scroll queries cannot use the `request_cache` anymore

Setting `request_cache:true` on a query that creates a scroll (`scroll=1m`)
has been deprecated in 6 and will now return a `400 - Bad request`.
Scroll queries are not meant to be cached.

#### Scroll queries cannot use `rescore` anymore

Including a rescore clause on a query that creates a scroll (`scroll=1m`) has
been deprecated in 6.5 and will now return a `400 - Bad request`.  Allowing
rescore on scroll queries would break the scroll sort.  In the 6.x line, the
rescore clause was silently ignored (for scroll queries), and it was allowed in
the 5.x line.

#### Term Suggesters supported distance algorithms

The following string distance algorithms were given additional names in 6.2 and
their existing names were deprecated. The deprecated names have now been
removed.

* `levenstein` - replaced by `levenshtein`

* `jarowinkler` - replaced by `jaro_winkler`

#### `popular` mode for Suggesters

The `popular` mode for Suggesters (`term` and `phrase`) now uses the doc frequency
(instead of the sum of the doc frequency) of the input terms to compute the frequency
threshold for candidate suggestions.

#### Limiting the number of terms that can be used in a Terms Query request

Executing a Terms Query with a lot of terms may degrade the cluster performance,
as each additional term demands extra processing and memory.
To safeguard against this, the maximum number of terms that can be used in a
Terms Query request has been limited to 65536. This default maximum can be changed
for a particular index with the index setting `index.max_terms_count`.

#### Limiting the length of regex that can be used in a Regexp Query request

Executing a Regexp Query with a long regex string may degrade search performance.
To safeguard against this, the maximum length of regex that can be used in a
Regexp Query request has been limited to 1000. This default maximum can be changed
for a particular index with the index setting `index.max_regex_length`.

#### Limiting the number of auto-expanded fields

Executing queries that use automatic expansion of fields (e.g. `query_string`, `simple_query_string`
or `multi_match`) can have performance issues for indices with a large numbers of fields.
To safeguard against this, a default limit of 1024 fields has been introduced for
queries using the "all fields" mode (`"default_field": "*"`) or other fieldname
expansions (e.g. `"foo*"`). If needed, you can change this limit using the
[`indices.query.bool.max_clause_count`](search-settings.html#indices-query-bool-max-clause-count)
static cluster setting.

#### Invalid `_search` request body

Search requests with extra content after the main object will no longer be accepted
by the `_search` endpoint. A parsing exception will be thrown instead.

#### Doc-value fields default format

The format of doc-value fields is changing to be the same as what could be
obtained in 6.x with the special `use_field_mapping` format. This is mostly a
change for date fields, which are now formatted based on the format that is
configured in the mappings by default. This behavior can be changed by
specifying a [`format`](search-request-body.html#request-body-search-docvalue-fields) within the doc-value
field.

#### Context Completion Suggester

The ability to query and index context enabled suggestions without context,
deprecated in 6.x, has been removed. Context enabled suggestion queries
without contexts have to visit every suggestion, which degrades the search performance
considerably.

For geo context the value of the `path` parameter is now validated against the mapping,
and the context is only accepted if `path` points to a field with `geo_point` type.

#### Semantics changed for `max_concurrent_shard_requests`

`max_concurrent_shard_requests` used to limit the total number of concurrent shard
requests a single high level search request can execute. In 7.0 this changed to be the
max number of concurrent shard requests per node. The default is now `5`.

#### `max_score` set to `null` when scores are not tracked

`max_score` used to be set to `0` whenever scores are not tracked. `null` is now used
instead which is a more appropriate value for a scenario where scores are not available.

#### Negative boosts are not allowed

Setting a negative `boost` for a query or a field, deprecated in 6x, is not allowed in this version.
To deboost a specific query or field you can use a `boost` comprise between 0 and 1.

#### Negative scores are not allowed in Function Score Query

Negative scores in the Function Score Query are deprecated in 6.x, and are
not allowed in this version. If a negative score is produced as a result
of computation (e.g. in `script_score` or `field_value_factor` functions),
an error will be thrown.

#### The filter context has been removed

The `filter` context has been removed from Elasticsearch’s query builders,
the distinction between queries and filters is now decided in Lucene depending
on whether queries need to access score or not. As a result `bool` queries with
`should` clauses that don’t need to access the score will no longer set their
`minimum_should_match` to 1. This behavior has been deprecated in the previous
major version.

#### `hits.total` is now an object in the search response

The total hits that match the search request is now returned as an object
with a `value` and a `relation`. `value` indicates the number of hits that
match and `relation` indicates whether the value is accurate (`eq`) or a lower bound
(`gte`):

```
{
  "hits": {
    "total": {
      "value": 1000,
      "relation": "eq"
    },
    ...
  }
}
```

The `total` object in the response indicates that the query matches exactly 1000
documents ("eq"). The `value` is always accurate (`"relation": "eq"`) when
`track_total_hits` is set to true in the request.
You can also retrieve `hits.total` as a number in the rest response by adding
`rest_total_hits_as_int=true` in the request parameter of the search request.
This parameter has been added to ease the transition to the new format and
will be removed in the next major version (8.0).

#### `hits.total` is omitted in the response if `track_total_hits` is disabled (false)

If `track_total_hits` is set to `false` in the search request the search response
will set `hits.total` to null and the object will not be displayed in the rest
layer. You can add `rest_total_hits_as_int=true` in the search request parameters
to get the old format back (`"total": -1`).

#### `track_total_hits` defaults to 10,000

By default search request will count the total hits accurately up to `10,000`
documents. If the total number of hits that match the query is greater than this
 value, the response will indicate that the returned value is a lower bound:

```
{
  "_shards": ...
  "timed_out": false,
  "took": 100,
  "hits": {
    "max_score": 1.0,
    "total": {
      "value": 10000,    
      "relation": "gte"  
    },
    "hits": ...
  }
}
```

|  | There are at least 10000 documents that match the query |
| --- | --- |
|  | This is a lower bound ( "gte" ). |

You can force the count to always be accurate by setting `track_total_hits`
to true explicitly in the search request.

#### Limitations on Similarities

Lucene 8 introduced more constraints on similarities, in particular:

* scores must not be negative,

* scores must not decrease when term freq increases,

* scores must not increase when norm (interpreted as an unsigned long) increases.

#### Weights in Function Score must be positive

Negative `weight` parameters in the `function_score` are no longer allowed.

#### Query string and Simple query string limit expansion of fields to 1024

The number of automatically expanded fields for the "all fields"
mode (`"default_field": "*"`) for the `query_string` and `simple_query_string`
queries is now 1024 fields.

### Suggesters changes

#### Registration of suggesters in plugins has changed

Plugins must now explicitly indicate the type of suggestion that they produce.

#### Phrase suggester now multiples alpha

Previously, the laplace smoothing used by the phrase suggester added `alpha`,
when it should instead multiply.  This behavior has been changed and will
affect suggester scores.

### Packaging changes

#### systemd service file is no longer configuration

The systemd service file `/usr/lib/systemd/system/elasticsearch.service`
was previously marked as a configuration file in rpm and deb packages.
Overrides to the systemd elasticsearch service should be made
in `/etc/systemd/system/elasticsearch.service.d/override.conf`.

#### tar package no longer includes windows specific files

The tar package previously included files in the `bin` directory meant only
for windows. These files have been removed. Use the `zip` package instead.

#### Ubuntu 14.04 is no longer supported

Ubuntu 14.04 will reach end-of-life on April 30, 2019. As such, we are no longer
supporting Ubuntu 14.04.

#### CLI secret prompting is no longer supported

The ability to use `${prompt.secret}` and `${prompt.text}` to collect secrets
from the CLI at server start is no longer supported.  Secure settings have replaced
the need for these prompts.

### Plugins changes

#### Azure Repository plugin

* The legacy azure settings which where starting with `cloud.azure.storage.` prefix have been removed.
This includes `account`, `key`, `default` and `timeout`.
You need to use settings which are starting with `azure.client.` prefix instead.

* Global timeout setting `cloud.azure.storage.timeout` has been removed.
You must set it per azure client instead. Like `azure.client.default.timeout: 10s` for example.

See [Azure Repository settings](/guide/en/elasticsearch/plugins/7.17/repository-azure-repository-settings.html#repository-azure-repository-settings).

#### Google Cloud Storage Repository plugin

* The repository settings `application_name`, `connect_timeout` and `read_timeout` have been removed and
must now be specified in the client settings instead.

See [Google Cloud Storage Client Settings](/guide/en/elasticsearch/plugins/7.17/repository-gcs-client.html#repository-gcs-client).

#### S3 Repository Plugin

* The plugin now uses the path style access pattern for all requests.
In previous versions it was automatically determining whether to use virtual hosted style or path style
access.

#### Analysis Plugin changes

* The misspelled helper method `requriesAnalysisSettings(AnalyzerProvider<T> provider)` has been
renamed to `requiresAnalysisSettings`

#### File-based discovery plugin

* This plugin has been removed since its functionality is now part of
Elasticsearch and requires no plugin. The location of the hosts file has moved
from `$ES_PATH_CONF/file-discovery/unicast_hosts.txt` to
`$ES_PATH_CONF/unicast_hosts.txt`. See [the
file-based hosts provider documentation](modules-discovery-hosts-providers.html#file-based-hosts-provider) for further information.

#### Security Extensions

As a consequence of the [change to Realm settings](breaking-changes-7.0.html#include-realm-type-in-setting),
the `getRealmSettings` method has been removed from the `SecurityExtension` class,
and the `settings` method on `RealmConfig` now returns the node’s (global) settings.
Custom security extensions should register their settings by implementing the standard
`Plugin.getSettings` method, and can retrieve them from `RealmConfig.settings()` or
using one of the `RealmConfig.getSetting` methods.
Each realm setting should be defined as an `AffixSetting` as shown in the example below:

```
Setting.AffixSetting<String> MY_SETTING = Setting.affixKeySetting(
  "xpack.security.authc.realms." + MY_REALM_TYPE + ".", "my_setting",
  key -> Setting.simpleString(key, properties)
);
```

The `RealmSettings.simpleString` method can be used as a convenience for the above.

#### Tribe node removed

Tribe node functionality has been removed in favor of
[Cross Cluster Search](modules-cross-cluster-search.html).

#### Discovery implementations are no longer pluggable

* The method `DiscoveryPlugin#getDiscoveryTypes()` was removed, so that plugins
can no longer provide their own discovery implementations.

#### Watcher *hipchat* action removed

Hipchat has been deprecated and shut down as a service. The `hipchat` action for
watches has been removed.

### API changes

#### Internal Versioning is no longer supported for optimistic concurrency control

Elasticsearch maintains a numeric version field for each document it stores. That field
is incremented by one with every change to the document. Until 7.0.0 the API allowed using
that field for optimistic concurrency control, i.e., making a write operation conditional
on the current document version. Sadly, that approach is flawed because the value of the
version doesn’t always uniquely represent a change to the document. If a primary fails
while handling a write operation, it may expose a version that will then be reused by the
new primary.

Due to that issue, internal versioning can no longer be used and is replaced by a new
method based on [sequence numbers](optimistic-concurrency-control.html). To switch
to the new method, follow these steps:

* Perform a [rolling upgrade](rolling-upgrades.html) to 6.8.

* [Reindex](reindex-upgrade.html) any indices created before 6.0. This ensures
documents in those indices have sequence numbers.

To get the Elasticsearch version in which an index was created, use the
[get index API](indices-get-index.html) with the `human` parameter:

**API Example**

```
GET /*?human
```

The response returns a `settings.index.version.created_string` property for
each index:

```
{
  "my-index-000001": {
    ...
    "settings": {
      "index": {
        "creation_date_string": "2099-01-01T00:00:00.000Z",
        "routing": {
          "allocation": {
            "include": {
              "_tier_preference": "data_content"
            }
          }
        },
        "number_of_shards": "1",
        "provided_name": "my-index-000001",
        "creation_date": "4070908800",
        "number_of_replicas": "1",
        "uuid": "c89-MHh8RwKwS1r7Turg2g",
        "version": {
          "created_string": "5.5.0",           
          "created": "5050099"
        }
      }
    }
  }
}
```

|  | This index was created in Elasticsearch 5.5.0. |
| --- | --- |

* Update your application or workflow to use
[sequence numbers](optimistic-concurrency-control.html) for concurrency control.

* Perform a rolling upgrade to 7.17.29.

The `external` versioning type is still fully supported.

#### Camel case and underscore parameters deprecated in 6.x have been removed

A number of duplicate parameters deprecated in 6.x have been removed from
Bulk request, Multi Get request, Term Vectors request, and More Like This Query
requests.

The following camel case parameters have been removed:

* `opType`

* `versionType`, `_versionType`

The following parameters starting with underscore have been removed:

* `_parent`

* `_retry_on_conflict`

* `_routing`

* `_version`

* `_version_type`

Instead of these removed parameters, use their non camel case equivalents without
starting underscore, e.g. use `version_type` instead of `_version_type` or `versionType`.

#### Thread pool info

In previous versions of Elasticsearch, the thread pool info returned in the
[nodes info API](cluster-nodes-info.html) returned `min` and `max` values reflecting
the configured minimum and maximum number of threads that could be in each
thread pool. The trouble with this representation is that it does not align with
the configuration parameters used to configure thread pools. For
[scaling thread pools](modules-threadpool.html), the minimum number of threads is
configured by a parameter called `core` and the maximum number of threads is
configured by a parameter called `max`. For [fixed thread
pools](modules-threadpool.html), there is only one configuration parameter along these lines and that
parameter is called `size`, reflecting the fixed number of threads in the
pool. This discrepancy between the API and the configuration parameters has been
rectified. Now, the API will report `core` and `max` for scaling thread pools,
and `size` for fixed thread pools.

Similarly, in the cat thread pool API the existing `size` output has been
renamed to `pool_size` which reflects the number of threads currently in the
pool; the shortcut for this value has been changed from `s` to `psz`.  The `min`
output has been renamed to `core` with a shortcut of `cr`, the shortcut for
`max` has been changed to `mx`, and the `size` output with a shortcut of `sz`
has been reused to report the configured number of threads in the pool.  This
aligns the output of the API with the configuration values for thread
pools. Note that `core` and `max` will be populated for scaling thread pools,
and `size` will be populated for fixed thread pools.

#### The parameter `fields` deprecated in 6.x has been removed from Bulk request

and Update request. The Update API returns `400 - Bad request` if request contains
unknown parameters (instead of ignored in the previous version).

#### PUT Document with Version error message changed when document is missing

If you attempt to `PUT` a document with versioning (e.g. `PUT /test/_doc/1?version=4`)
but the document does not exist, a cryptic message is returned:

```
version conflict, current version [-1] is different than the one provided [4]
```

Now if the document is missing a more helpful message is returned:

```
document does not exist (expected version [4])
```

Although exceptions messages are liable to change and not generally subject to
backwards compatibility, the nature of this message might mean clients are relying
on parsing the version numbers and so the format change might impact some users.

#### Remove support for `suggest` metric/index metric in indices stats and nodes stats APIs

Previously, `suggest` stats were folded into `search` stats. Support for the
`suggest` metric on the indices stats and nodes stats APIs remained for
backwards compatibility. Backwards support for the `suggest` metric was
deprecated in 6.3.0 and now removed in 7.0.0.

#### Field capabilities request format

In the past, `fields` could be provided either as a parameter, or as part of the request
body. Specifying `fields` in the request body as opposed to a parameter was deprecated
in 6.4.0, and is now unsupported in 7.0.0.

#### `copy_settings` is deprecated on shrink and split APIs

Versions of Elasticsearch prior to 6.4.0 did not copy index settings on shrink
and split operations. Starting with Elasticsearch 7.0.0, the default behavior
will be for such settings to be copied on such operations. To enable users in
6.4.0 to transition in 6.4.0 to the default behavior in 7.0.0, the
`copy_settings` parameter was added on the REST layer. As this behavior will be
the only behavior in 8.0.0, this parameter is deprecated in 7.0.0 for removal in
8.0.0.

#### The deprecated stored script contexts have now been removed

When putting stored scripts, support for storing them with the deprecated `template` context or without a context is
now removed. Scripts must be stored using the `script` context as mentioned in the documentation.

#### Removed Get Aliases API limitations when security features are enabled

The behavior and response codes of the get aliases API no longer vary
depending on whether security features are enabled. Previously a
404 - NOT FOUND (IndexNotFoundException) could be returned in case the
current user was not authorized for any alias. An empty response with
status 200 - OK is now returned instead at all times.

#### Put User API response no longer has `user` object

The Put User API response was changed in 6.5.0 to add the `created` field
outside of the user object where it previously had been. In 7.0.0 the user
object has been removed in favor of the top level `created` field.

#### Source filtering url parameters `_source_include` and `_source_exclude` have been removed

The deprecated in 6.x url parameters are now removed. Use `_source_includes` and `_source_excludes` instead.

#### Multi Search Request metadata validation

MultiSearchRequests issued through `_msearch` now validate all keys in the metadata section. Previously unknown keys were ignored
while now an exception is thrown.

#### Deprecated graph endpoints removed

The deprecated graph endpoints (those with `/_graph/_explore`) have been
removed.

#### Deprecated `_termvector` endpoint removed

The `_termvector` endpoint was deprecated in 2.0 and has now been removed.
The endpoint `_termvectors` (plural) should be used instead.

#### When security features are enabled, index monitoring APIs over restricted indices are not authorized implicitly anymore

Restricted indices (currently only `.security-6` and `.security`) are special internal
indices that require setting the `allow_restricted_indices` flag on every index
permission that covers them. If this flag is `false` (default) the permission
will not cover these and actions against them will not be authorized.
However, the monitoring APIs were the only exception to this rule. This exception
has been forfeited and index monitoring privileges have to be granted explicitly,
using the `allow_restricted_indices` flag on the permission (as any other index
privilege).

#### Removed support for `GET` on the `_cache/clear` API

The `_cache/clear` API no longer supports the `GET` HTTP verb. It must be called
with `POST`.

#### Cluster state size metrics removed from Cluster State API Response

The `compressed_size` / `compressed_size_in_bytes` fields were removed from
the Cluster State API response.  The calculation of the size was expensive and had
dubious value, so the field was removed from the response.

#### Migration Assistance API has been removed

The Migration Assistance API has been functionally replaced by the
Deprecation Info API, and the Migration Upgrade API is not used for the
transition from ES 6.x to 7.x, and does not need to be kept around to
repair indices that were not properly upgraded before upgrading the
cluster, as was the case in 6.

#### Changes to thread pool naming in Node and Cat APIs

The `thread_pool` information returned from the Nodes and Cat APIs has been
standardized to use the same terminology as the thread pool configurations.
This means the response will align with the configuration instead of being
the same across all the thread pools, regardless of type.

#### Return 200 when cluster has valid read-only blocks

If the cluster was configured with `no_master_block: write` and lost its master,
it would return a `503` status code from a main request (`GET /`) even though
there are viable read-only nodes available.  The cluster now returns 200 status
in this situation.

#### Clearing indices cache is now POST-only

Clearing the cache indices could previously be done via GET and POST. As GET should
only support read only non state-changing operations, this is no longer allowed.
Only POST can be used to clear the cache.

### Java API changes

#### `isShardsAcked` deprecated in `6.2` has been removed

`isShardsAcked` has been replaced by `isShardsAcknowledged` in
`CreateIndexResponse`, `RolloverResponse` and
`CreateIndexClusterStateUpdateResponse`.

#### `prepareExecute` removed from the client api

The `prepareExecute` method which created a request builder has been
removed from the client api. Instead, construct a builder for the
appropriate request directly.

#### Some Aggregation classes have moved packages

* All classes present in `org.elasticsearch.search.aggregations.metrics.*` packages
were moved to a single `org.elasticsearch.search.aggregations.metrics` package.

* All classes present in `org.elasticsearch.search.aggregations.pipeline.*` packages
were moved to a single `org.elasticsearch.search.aggregations.pipeline` package.  In
addition, `org.elasticsearch.search.aggregations.pipeline.PipelineAggregationBuilders`
was moved to `org.elasticsearch.search.aggregations.PipelineAggregationBuilders`

#### `Retry.withBackoff` methods with `Settings` removed

The variants of `Retry.withBackoff` that included `Settings` have been removed
because `Settings` is no longer needed.

#### Deprecated method `Client#termVector` removed

The client method `termVector`, deprecated in 2.0, has been removed. The method
`termVectors` (plural) should be used instead.

#### Deprecated constructor `AbstractLifecycleComponent(Settings settings)` removed

The constructor `AbstractLifecycleComponent(Settings settings)`, deprecated in 6.7
has been removed. The parameterless constructor should be used instead.

#### Changes to Geometry classes

Geometry classes used to represent geo values in SQL have been moved from the
`org.elasticsearch.geo.geometry` package to the `org.elasticsearch.geometry`
package and the order of the constructor parameters has changed from `lat`, `lon`
to `lon`, `lat`.

### Settings changes

#### The default for `node.name` is now the hostname

`node.name` now defaults to the hostname at the time when Elasticsearch
is started. Previously the default node name was the first eight characters
of the node id. It can still be configured explicitly in `elasticsearch.yml`.

#### Percolator

* The deprecated `index.percolator.map_unmapped_fields_as_string` setting has been removed in favour of
the `index.percolator.map_unmapped_fields_as_text` setting.

#### Index thread pool

* Internally, single-document index/delete/update requests are executed as bulk
requests with a single-document payload. This means that these requests are
executed on the bulk thread pool. As such, the indexing thread pool is no
longer needed and has been removed. As such, the  settings
`thread_pool.index.size` and `thread_pool.index.queue_size` have been removed.

#### Write thread pool fallback

* The bulk thread pool was replaced by the write thread pool in 6.3.0. However,
for backwards compatibility reasons the name `bulk` was still usable as fallback
settings `thread_pool.bulk.size` and `thread_pool.bulk.queue_size` for
`thread_pool.write.size` and `thread_pool.write.queue_size`, respectively, and
the system property `es.thread_pool.write.use_bulk_as_display_name` was
available to keep the display output in APIs as `bulk` instead of `write`.
These fallback settings and this system property have been removed.

#### Disabling memory-mapping

* The setting `node.store.allow_mmapfs` has been renamed to `node.store.allow_mmap`.

#### Http enabled setting removed

* The setting `http.enabled` previously allowed disabling binding to HTTP, only allowing
use of the transport client. This setting has been removed, as the transport client
will be removed in the future, thus requiring HTTP to always be enabled.

#### Http pipelining setting removed

* The setting `http.pipelining` previously allowed disabling HTTP pipelining support.
This setting has been removed, as disabling http pipelining support on the server
provided little value. The setting `http.pipelining.max_events` can still be used to
limit the number of pipelined requests in-flight.

#### Cross-cluster search settings renamed

The cross-cluster search remote cluster connection infrastructure is also used
in cross-cluster replication. This means that the setting names
`search.remote.*` used for configuring cross-cluster search belie the fact that
they also apply to other situations where a connection to a remote cluster as
used.  Therefore, these settings have been renamed from `search.remote.*` to
`cluster.remote.*`. For backwards compatibility purposes, we will fallback to
`search.remote.*` if `cluster.remote.*` is not set. For any such settings stored
in the cluster state, or set on dynamic settings updates, we will automatically
upgrade the setting from `search.remote.*` to `cluster.remote.*`. The fallback
settings will be removed in 8.0.0.

#### Audit logfile local node info

The following settings have been removed:

* `xpack.security.audit.logfile.prefix.emit_node_host_address`, instead use
`xpack.security.audit.logfile.emit_node_host_address`

* `xpack.security.audit.logfile.prefix.emit_node_host_name`, instead use
`xpack.security.audit.logfile.emit_node_host_name`

* `xpack.security.audit.logfile.prefix.emit_node_name`, instead use
`xpack.security.audit.logfile.emit_node_name`

The new settings have the same meaning as the removed ones, but the `prefix`
name component is no longer meaningful as logfile audit entries are structured
JSON documents and are not prefixed by anything.
Moreover, `xpack.security.audit.logfile.emit_node_name` has changed its default
from `true` to `false`. All other settings mentioned before, have kept their
default value of `false`.

#### Security realms settings

The settings for all security realms must now include the realm type as part
of the setting name, and the explicit `type` setting has been removed.

A realm that was previous configured as:

```
xpack.security.authc.realms:
  ldap1:
    type: ldap
    order: 1
    url: "ldaps://ldap.example.com/"
```

Must be migrated to:

```
xpack.security.authc.realms:
  ldap.ldap1:
    order: 1
    url: "ldaps://ldap.example.com/"
```

Any realm specific secure settings that have been stored in the elasticsearch
keystore (such as ldap bind passwords, or passwords for ssl keys) must be updated
in a similar way.

#### TLS/SSL settings

The default TLS/SSL settings, which were prefixed by `xpack.ssl`, have been removed.
The removal of these default settings also removes the ability for a component to
fallback to a default configuration when using TLS. Each component (realm, transport, http,
http client, etc) must now be configured with their own settings for TLS if it is being
used.

#### TLS v1.0 disabled

TLS version 1.0 is now disabled by default as it suffers from
[known security issues](https://www.owasp.org/index.php/Transport_Layer_Protection_Cheat_Sheet#Rule_-_Only_Support_Strong_Protocols).
The default protocols are now TLSv1.3 (if supported), TLSv1.2 and TLSv1.1.

You can enable TLS v1.0 by configuring the relevant `ssl.supported_protocols`
setting to include `"TLSv1"`.
Depending on your local configuration and the TLS protocols that are in use
on your network, you may need to enable TLS v1.0 support in any or all of the
following places:

`xpack.security.http.ssl.supported_protocols`

For incoming HTTP connections to Elasticsearch’s HTTP (Rest) interface.
If there are clients that connect to Elasticsearch and do not support newer TLS versions,
you must update this setting.

`xpack.http.ssl.supported_protocols`

For outgoing HTTP connections from Watcher.
If you have watches that connect to external HTTP servers and do not support
newer TLS versions, you must update this setting.

`xpack.security.authc.realms.ldap.{name}.ssl.supported_protocols`

For outgoing LDAP connections from Elasticsearch security features.
If you have an LDAP realm enabled and the LDAP directory to which that realm
connects does not support newer TLS versions, you must update this setting.

`xpack.security.authc.realms.active_directory.{name}.ssl.supported_protocols`

For outgoing Active Directory (LDAP) connections from Elasticsearch security features.
If you have an AD realm enabled and the directory server to which that realm
connects does not support newer TLS versions, you must update this setting.

`xpack.security.authc.realms.saml.{name}.ssl.supported_protocols`

For outgoing HTTP connections to retrieve SAML metadata.
If you have a SAML realm enabled and the realm is configured to retrieve
metadata over HTTPS (that is, `idp.metadata.path` is a URL starting with
`https://`) and the web server which hosts the metadata does not support newer
TLS versions, you must update this setting.

`xpack.security.authc.realms.oidc.{name}.ssl.supported_protocols`

For outgoing HTTP connections to an OpenId Connect Provider.
If you have an OpenId Connect ("oidc") realm enabled and the realm is configured
to connect to a remote OpenID Connect Provider which does not support newer TLS
versions, you must update this setting.

`xpack.monitoring.exporters.{name}.ssl.supported_protocols`

For remote monitoring data.
If your monitoring data is exported to a remote monitoring cluster and that
cluster is configured to only support TLSv1, you must update this setting.

`reindex.ssl.supported_protocols`

For reindex from remote.
If you reindex data from a remote Elasticsearch cluster which has SSL enabled on the
`http` interface and that cluster is configured to only support TLSv1, you must
update this setting.

`xpack.security.transport.ssl.supported_protocols`

For incoming connections between Elasticsearch nodes. If you have specialized network
equipment which inspects TLS packets between your nodes, and that equipment
enforces TLSv1 you must update this setting.

The following is an example that enables TLS v1.0 for incoming HTTP connections:

```
xpack.security.http.ssl.supported_protocols: [ "TLSv1.3", "TLSv1.2", "TLSv1.1", "TLSv1" ]
```

#### Security on Trial Licenses

On trial licenses, `xpack.security.enabled` defaults to `false`.

In prior versions, a trial license would automatically enable security if either

* `xpack.security.transport.enabled` was `true`; *or*

* the trial license was generated on a version of X-Pack from 6.2 or earlier.

This behaviour has been now removed, so security is only enabled if:

* `xpack.security.enabled` is `true`; *or*

* `xpack.security.enabled` is not set, and a gold or platinum license is installed.

#### Watcher notifications account settings

The following settings have been removed in favor of the secure variants.
The [secure settings](secure-settings.html) have to be defined inside each cluster
node’s keystore, i.e., they are not to be specified via the cluster settings API.

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

#### Audit index output type removed

All the settings under the `xpack.security.audit.index` namespace have been
removed. In addition, the `xpack.security.audit.outputs` setting has been
removed as well.

These settings enabled and configured the audit index output type. This output
type has been removed because it was unreliable in certain scenarios and this
could have lead to dropping audit events while the operations on the system
were allowed to continue as usual. The recommended replacement is the
use of the `logfile` audit output type and using other components from the
Elastic Stack to handle the indexing part.

#### Ingest User Agent processor defaults uses `ecs` output format

[ECS](https://github.com/elastic/ecs) format is now the default.
The `ecs` setting for the user agent ingest processor now defaults to true.

#### Remove `action.master.force_local`

The `action.master.force_local` setting was an undocumented setting, used
internally by the tribe node to force reads to local cluster state (instead of
forwarding to a master, which tribe nodes did not have).  Since the tribe
node was removed, this setting was removed too.

#### Enforce cluster-wide shard limit

The cluster-wide shard limit is now enforced and not optional. The limit can
still be adjusted as desired using the cluster settings API.

#### HTTP Max content length setting is no longer parsed leniently

Previously, `http.max_content_length` would reset to `100mb` if the setting was
greater than `Integer.MAX_VALUE`.  This leniency has been removed.

### Scripting changes

#### getDate() and getDates() removed

Fields of type `long` and `date` had `getDate()` and `getDates()` methods
(for multi valued fields) to get an object with date specific helper methods
for the current doc value. In 5.3.0, `date` fields were changed to expose
this same date object directly when calling `doc["myfield"].value`, and
the getter methods for date objects were deprecated. These methods have
now been removed. Instead, use `.value` on `date` fields, or explicitly
parse `long` fields into a date object using
`Instance.ofEpochMillis(doc["myfield"].value)`.

#### Accessing missing document values will throw an error

`doc['field'].value` will throw an exception if
the document is missing a value for the field `field`.

To check if a document is missing a value, you can use
`doc['field'].size() == 0`.

#### Script errors will return as `400` error codes

Malformed scripts, either in search templates, ingest pipelines or search
requests, return `400 - Bad request` while they would previously return
`500 - Internal Server Error`. This also applies for stored scripts.

#### getValues() removed

The `ScriptDocValues#getValues()` method is deprecated in 6.6 and will
be removed in 7.0. Use `doc["foo"]` in place of `doc["foo"].values`.

### Snapshot stats changes

Snapshot stats details are provided in a new structured way:

* `total` section for all the files that are referenced by the snapshot.

* `incremental` section for those files that actually needed to be copied over as part of the incremental snapshotting.

* In case of a snapshot that’s still in progress, there’s also a `processed` section for files that are in the process of being copied.

#### Deprecated `number_of_files`, `processed_files`, `total_size_in_bytes` and `processed_size_in_bytes` snapshot stats properties have been removed

* Properties `number_of_files` and `total_size_in_bytes` are removed and should be replaced by values of nested object `total`.

* Properties `processed_files` and `processed_size_in_bytes` are removed and should be replaced by values of nested object `processed`.

### High-level REST client changes

#### API methods accepting `Header` argument have been removed

All API methods accepting headers as a `Header` varargs argument, deprecated
since 6.4, have been removed in favour of the newly introduced methods that
accept instead a `RequestOptions` argument. In case you are not specifying any
header, e.g. `client.index(indexRequest)` becomes
`client.index(indexRequest, RequestOptions.DEFAULT)`.
In case you are specifying headers
e.g. `client.index(indexRequest, new Header("name" "value"))` becomes
`client.index(indexRequest, RequestOptions.DEFAULT.toBuilder().addHeader("name", "value").build());`

#### Cluster Health API default to `cluster` level

The Cluster Health API used to default to `shards` level to ease migration
from transport client that doesn’t support the `level` parameter and always
returns information including indices and shards details. The level default
value has been aligned with the Elasticsearch default level: `cluster`.

### Low-level REST client changes

#### Support for `maxRetryTimeout` removed from RestClient

`RestClient` and `RestClientBuilder` no longer support the `maxRetryTimeout`
setting. The setting was removed as its counting mechanism was not accurate
and caused issues while adding little value.

#### Deprecated flavors of performRequest have been removed

We deprecated the flavors of `performRequest` and `performRequestAsync` that
do not take `Request` objects in 6.4.0 in favor of the flavors that take
`Request` objects because those methods can be extended without breaking
backwards compatibility.

#### Removed setHosts

We deprecated `setHosts` in 6.4.0 in favor of `setNodes` because it supports
host metadata used by the `NodeSelector`.

#### Minimum compiler version change

The minimum compiler version on the low-level REST client has been bumped
to JDK 8.

### Logging changes

#### New JSON format log files in `log` directory

Elasticsearch now will produce additional log files in JSON format. They will be stored in `*.json` suffix files.
Following files should be expected now in log directory:
* ${cluster_name}_server.json
* ${cluster_name}_deprecation.json
* ${cluster_name}_index_search_slowlog.json
* ${cluster_name}_index_indexing_slowlog.json
* ${cluster_name}.log
* ${cluster_name}_deprecation.log
* ${cluster_name}_index_search_slowlog.log
* ${cluster_name}_index_indexing_slowlog.log
* ${cluster_name}_audit.json
* gc.log

Note: You can configure which of these files are written by editing `log4j2.properties`.

#### Log files ending with `*.log` deprecated

Log files with the `.log` file extension using the old pattern layout format
are now considered deprecated and the newly added JSON log file format with
the `.json` file extension should be used instead.
Note: GC logs which are written to the file `gc.log` will not be changed.

#### Docker output in JSON format

All Docker console logs are now in JSON format. You can distinguish logs streams with the `type` field.

#### Audit plaintext log file removed, JSON file renamed

Elasticsearch no longer produces the `${cluster_name}_access.log` plaintext
audit log file. The `${cluster_name}_audit.log` files also no longer exist; they
are replaced by `${cluster_name}_audit.json` files. When auditing is enabled,
auditing events are stored in these dedicated JSON log files on each node.

### Node start up

#### Nodes with left-behind data or metadata refuse to start

Repurposing an existing node by changing node.master or node.data to false can leave lingering on-disk metadata and
data around, which will not be accessible by the node’s new role. Beside storing non-accessible data, this can lead
to situations where dangling indices are imported even though the node might not be able to host any shards, leading
to a red cluster health. To avoid this,

* nodes with on-disk shard data and node.data set to false will refuse to start

* nodes with on-disk index/shard data and both node.master and node.data set to false will refuse to start

Beware that such role changes done prior to the 7.0 upgrade could prevent node start up in 7.0.

### Replacing Joda-Time with java time

Since Java 8 there is a dedicated `java.time` package, which is superior to
the Joda-Time library, that has been used so far in Elasticsearch. One of
the biggest advantages is the ability to be able to store dates in a higher
resolution than milliseconds for greater precision. Also this will allow us
to remove the Joda-Time dependency in the future.

The mappings, aggregations and search code switched from Joda-Time to
java time.

#### Joda based date formatters are replaced with java ones

With the release of Elasticsearch 6.7 a backwards compatibility layer was
introduced, that checked if you are using a Joda-Time based formatter, that is
supported differently in java time. A log message was emitted, and you could
create the proper java time based formatter prefixed with an `8`.

With Elasticsearch 7.0 all formatters are now java based, which means you will
get exceptions when using deprecated formatters without checking the
deprecation log in 6.7. In the worst case you may even end up with different
dates.

An example deprecation message looks like this, that is returned, when you
try to use a date formatter that includes a lower case `Y`

```
Use of 'Y' (year-of-era) will change to 'y' in the next major version of
Elasticsearch. Prefix your date format with '8' to use the new specifier.
```

So, instead of using `YYYY.MM.dd` you should use `8yyyy.MM.dd`.

You can find more information about available formatting strings in the
[DateTimeFormatter javadocs](https://docs.oracle.com/javase/8/docs/api/java/time/format/DateTimeFormatter.html).

#### Date formats behavioural change

The `epoch_millis` and `epoch_second` formatters no longer support
scientific notation.

If you are using the century of era formatter in a date (`C`), this will no
longer be supported.

The year-of-era formatting character is a `Y` in Joda-Time, but a lowercase
`y` in java time.

The week-based-year formatting character is a lowercase `x` in Joda-Time,
but an upper-case `Y` in java time.

#### Using time zones in the Java client

Timezones have to be specified as java time based zone objects. This means,
instead of using a `org.joda.time.DateTimeZone` the use of
`java.time.ZoneId` is required.

Examples of possible uses are the `QueryStringQueryBuilder`, the
`RangeQueryBuilder` or the `DateHistogramAggregationBuilder`, each of them
allow for an optional timezone for that part of the search request.

#### Parsing aggregation buckets in the Java client

The date based aggregation buckets in responses used to be of
type `JodaTime`. Due to migrating to java-time, the buckets are now of
type `ZonedDateTime`. As the client is returning untyped objects here, you
may run into class cast exceptions only when running the code, but not at
compile time, ensure you have proper test coverage for this in your
own code.

#### Parsing `GMT0` timezone with JDK8 is not supported

When you are running Elasticsearch 7 with Java 8, you are not able to parse
the timezone `GMT0` properly anymore. The reason for this is a bug in the
JDK, which has not been fixed for JDK8. You can read more in the
[official issue](https://bugs.openjdk.java.net/browse/JDK-8138664)
This bug is fixed in JDK9 and later versions.

#### Scripting with dates should use java time based methods

If dates are used in scripting, a backwards compatibility layer has been added
that emulates the Joda-Time methods, but logs a deprecation message as well
to use the java time methods.

The following methods will be removed in future versions of Elasticsearch
and should be replaced.

* `getDayOfWeek()` will be an enum instead of an int, if you need to use
an int, use `getDayOfWeekEnum().getValue()`

* `getMillis()` should be replaced with `toInstant().toEpochMilli()`

* `getCenturyOfEra()` should be replaced with `get(ChronoField.YEAR_OF_ERA) / 100`

* `getEra()` should be replaced with `get(ChronoField.ERA)`

* `getHourOfDay()` should be replaced with `getHour()`

* `getMillisOfDay()` should be replaced with `get(ChronoField.MILLI_OF_DAY)`

* `getMillisOfSecond()` should be replaced with `get(ChronoField.MILLI_OF_SECOND)`

* `getMinuteOfDay()` should be replaced with `get(ChronoField.MINUTE_OF_DAY)`

* `getMinuteOfHour()` should be replaced with `getMinute()`

* `getMonthOfYear()` should be replaced with `getMonthValue()`

* `getSecondOfDay()` should be replaced with `get(ChronoField.SECOND_OF_DAY)`

* `getSecondOfMinute()` should be replaced with `getSecond()`

* `getWeekOfWeekyear()` should be replaced with `get(WeekFields.ISO.weekOfWeekBasedYear())`

* `getWeekyear()` should be replaced with `get(WeekFields.ISO.weekBasedYear())`

* `getYearOfCentury()` should be replaced with `get(ChronoField.YEAR_OF_ERA) % 100`

* `getYearOfEra()` should be replaced with `get(ChronoField.YEAR_OF_ERA)`

* `toString(String)` should be replaced with a `DateTimeFormatter`

* `toString(String,Locale)` should be replaced with a `DateTimeFormatter`

#### Negative epoch timestamps are no longer supported

With the switch to java time, support for negative timestamps has been removed.
For dates before 1970, use a date format containing a year.

#### Migration guide

For a detailed migration guide, see [Java time migration guide](migrate-to-java-time.html).