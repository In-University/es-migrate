**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 6.0

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 6.0.

### Indices created before 6.0

Elasticsearch 6.0 can read indices created in version 5.0 or above.  An
Elasticsearch 6.0 node will not start in the presence of indices created in a
version of Elasticsearch before 5.0.

Reindex indices from Elasticsearch 2.x or before

Indices created in Elasticsearch 2.x or before will need to be reindexed with
Elasticsearch 5.x in order to be readable by Elasticsearch 6.x.

Multiple mapping types are not supported in indices created in 6.0

The ability to have multiple mapping types per index has been removed in 6.0.
New indices will be restricted to a single type. This is the first step in the
plan to remove mapping types altogether.  Indices created in 5.x will continue
to support multiple mapping types.

See [*Removal of mapping types*](removal-of-types.html) for more information.

### Also see:

* [Aggregations changes](breaking-changes-6.0.html#breaking_60_aggregations_changes)

* [Cat API changes](breaking-changes-6.0.html#breaking_60_cat_changes)

* [Clients changes](breaking-changes-6.0.html#breaking_60_clients_changes)

* [Cluster changes](breaking-changes-6.0.html#breaking_60_cluster_changes)

* [Document API changes](breaking-changes-6.0.html#breaking_60_docs_changes)

* [Indices changes](breaking-changes-6.0.html#breaking_60_indices_changes)

* [Ingest changes](breaking-changes-6.0.html#breaking_60_ingest_changes)

* [Java API changes](breaking-changes-6.0.html#breaking_60_java_changes)

* [Mapping changes](breaking-changes-6.0.html#breaking_60_mappings_changes)

* [Packaging changes](breaking-changes-6.0.html#breaking_60_packaging_changes)

* [Percolator changes](breaking-changes-6.0.html#breaking_60_percolator_changes)

* [Plugins changes](breaking-changes-6.0.html#breaking_60_plugins_changes)

* [Reindex changes](breaking-changes-6.0.html#breaking_60_reindex_changes)

* [REST changes](breaking-changes-6.0.html#breaking_60_rest_changes)

* [Stats and info changes](breaking-changes-6.0.html#breaking_60_stats_changes)

* [Search and Query DSL changes](breaking-changes-6.0.html#breaking_60_search_changes)

* [Settings changes](breaking-changes-6.0.html#breaking_60_settings_changes)

* [Scripting changes](breaking-changes-6.0.html#breaking_60_scripting_changes)

### Aggregations changes

#### Deprecated `pattern` element of include/exclude for terms aggregations has been removed

The `include` and `exclude` options of `terms` aggregations used to accept a
sub `pattern` object which has been removed. The pattern should now be directly
put as a value of the `include` and `exclude` fields. For instance, the below
`terms` aggregation:

```
POST /twitter/_search?size=0
{
    "aggs" : {
        "top_users" : {
            "terms" : {
                "field" : "user",
                "include": {
                  "pattern": "foo.*"
                },
                "exclude": {
                  "pattern": ".*bar"
                }
            }
        }
    }
}
```

should be replaced with:

```
POST /twitter/_search?size=0
{
    "aggs" : {
        "top_users" : {
            "terms" : {
                "field" : "user",
                "include": "foo.*",
                "exclude": ".*bar"
            }
        }
    }
}
```

#### Numeric `to` and `from` parameters in `date_range` aggregation are interpreted according to `format` now

Numeric `to` and `from` parameters in `date_range` aggregations used to always be interpreted as `epoch_millis`,
making other numeric formats like `epoch_seconds` unusable for numeric input values.
Now we interpret these parameters according to the `format` of the target field.
If the `format` in the mappings is not compatible with the numeric input value, a compatible
`format` (e.g. `epoch_millis`, `epoch_second`) must be specified in the `date_range` aggregation, otherwise an error is thrown.

#### `global_ordinals_hash` and `global_ordinals_low_cardinality` are deprecated in the `terms` aggregation

The execution hints `global_ordinals_hash` and `global_ordinals_low_cardinality` are deprecated and should be replaced
by `global_ordinals` which now internally choose whether it should remap global ordinals to dense ordinals or directly use the
segment ordinals.

#### `missing` is deprecated in the `composite` aggregation

The `missing` option of the `composite` aggregation is deprecated, `missing_bucket`
should be used instead.

### Analysis changes

#### Synonym Token Filter

In 6.0, Synonym Token Filter tokenizes synonyms with whatever
tokenizer and token filters appear before it in the chain.

The `tokenizer` and `ignore_case` parameters are deprecated
and will be ignored when used in new indices.  These parameters
will continue to function as before when used in indices
created in 5.x.

#### Limiting the length of an analyzed text during highlighting

Highlighting a text that was indexed without offsets or term vectors,
requires analysis of this text in memory real time during the search request.
For large texts this analysis may take substantial amount of time and memory.
To protect against this, the maximum number of characters that to be analyzed will be
limited to 1000000 in the next major Elastic version. For this version, by default the limit
is not set. A deprecation warning will be issued when an analyzed text exceeds 1000000.
 The limit can be set for a particular index with the index setting
`index.highlight.max_analyzed_offset`.

#### `standard` filter has been deprecated

The `standard` token filter has been deprecated because it doesn’t change anything in
the stream. It will be removed in the next major version.

#### Deprecated standard_html_strip analyzer

The `standard_html_strip` analyzer has been deprecated, and should be replaced
with a combination of the `standard` tokenizer and `html_strip` char_filter.
Indexes created using this analyzer will still be readable in elasticsearch 7.0,
but it will not be possible to create new indexes using it.

#### Limit to the difference between max_size and min_size in NGramTokenFilter and NGramTokenizer

To safeguard against creating too many index terms, the difference between
max_ngram and min_ngram in NGramTokenFilter and NGramTokenizer has been
limited to 1. This default limit can be changed with the index setting
index.max_ngram_diff. Note that if the limit is exceeded a deprecation
warning is logged.

#### Limit to the difference between max_size and min_size in ShingleTokenFilter

To safeguard against creating too many tokens, the difference between
max_shingle_size and min_shingle_size in ShingleTokenFilter has been
limited to 3. This default limit can be changed with the index setting
index.max_shingle_diff. Note that if the limit is exceeded a deprecation
warning will be logged.

### Cat API changes

#### Unbounded queue size in cat thread pool

Previously if a queue size backing a thread pool was unbounded, the cat thread pool API would output an empty string in
the queue_size column. This has been changed to now output -1 so that the output is always present and always numeric.

### Clients changes

#### Java High Level REST Client

Starting from version 5.6.0 a new Java client has been released: the Java High Level REST Client.
This official high-level client (named like this to differentiate it from the existing low-level client) for
Elasticsearch can be used to execute search, index, delete, update and bulk operations using the same Core
Java classes as the `TransportClient` uses.

This Java High Level REST Client is designed to replace the `TransportClient` in a near future.

### Cluster changes

#### Cluster name no longer allowed in path.data

Previously the cluster name could be used in the `path.data` setting with a
warning. This is now no longer allowed. For instance, in the previous version
this was valid:

```
# Assuming path.data is /tmp/mydata
# No longer supported:
$ tree /tmp/mydata
/tmp/mydata
├── <cluster_name>
│   └── nodes
│       └── 0
│           └── <etc>

# Should be changed to:
$ tree /tmp/mydata
/tmp/mydata
├── nodes
│   └── 0
│       └── <etc>
```

### Document API changes

#### version type `force` removed

Document modification operations may no longer specify the `version_type` of
`force` to override any previous version checks.

#### [Upserts](docs-update.html#upserts) no longer support versions

Adding a `version` to an upsert request is no longer supported.

#### `created` field removed in the Index API

The `created` field has been removed in the Index API as in the `index` and
`create` bulk operations. `operation` field should be used instead.

#### `found` field removed in the Delete API

The `found` field has been removed in the Delete API as in the `delete` bulk
operations. `operation` field should be used instead.

### Geo changes

#### Deprecated `ShapeBuilders` helper class

The `ShapeBuilders` class containing static methods to create shape specific builders
(e.g., `ShapeBuilders.newPoint`) has been deprecated. One must now use the builder’s
constructor instead (e.g., `new MultiPointBuilder()).

#### Deprecated `ShapeBuilder.parse` static method

The `ShapeBuilder.parse` method has been deprecated. Use `ShapeParser.parse` instead.

### Indices changes

#### Index templates use `index_patterns` instead of `template`

Previously templates expressed the indices that they should match using a glob
style pattern in the `template` field. They should now use the `index_patterns`
field instead. As the name implies you can define multiple glob style patterns
in an array but for convenience defining a single pattern as a bare string is
also supported. So both of these examples are valid:

```
PUT _template/template_1
{
  "index_patterns": ["te*", "bar*"],
  "settings": {
    "number_of_shards": 1
  }
}
PUT _template/template_2
{
  "index_patterns": "te*",
  "settings": {
    "number_of_shards": 1
  }
}
```

#### Shadow Replicas have been removed

Shadow replicas don’t see enough usage, and have been removed. This includes the
following settings:

* `index.shared_filesystem`

* `index.shadow_replicas`

* `node.add_lock_id_to_custom_path`

#### Open/Close index API allows wildcard expressions that match no indices by default

The default value of the `allow_no_indices` option for the Open/Close index API
has been changed from `false` to `true` so it is aligned with the behaviour of the
Delete index API. As a result, Open/Close index API don’t return an error by
default when a provided wildcard expression doesn’t match any closed/open index.

#### Delete a document

Delete a document from non-existing index has been modified to not create the index.
However if an external versioning is used the index will be created and the document
will be marked for deletion.

#### Indices aliases api resolves indices expressions only against indices

The index parameter in the update-aliases, put-alias, and delete-alias APIs no
longer accepts alias names. Instead, it accepts only index names (or wildcards
which will expand to matching indices).

#### Delete index api resolves indices expressions only against indices

The index parameter in the delete index API no longer accepts alias names.
Instead, it accepts only index names (or wildcards which will expand to
matching indices).

#### Support for `+` has been removed in index expressions

Omitting the `+` has the same effect as specifying it, hence support for `+`
has been removed in index expressions.

#### Translog retention

Translog files are now kept for up to 12 hours (by default), with a maximum size of `512mb` (default), and
are no longer deleted on `flush`. This is to increase the chance of doing an operation based recovery when
bringing up replicas up to speed.

### Ingest changes

#### Timestamp meta-data field type has changed

The type of the "timestamp" meta-data field has changed from `java.lang.String` to `java.util.Date`.

#### The format of the string-formatted ingest.timestamp field has changed

Previously, since Elasticsearch 5.4.0, you needed to use `ingest.new_date_format` to have the
`ingest.timestamp` metadata field be formatted in such a way that ES can coerce it to a field
of type `date` without further transformation. This is not necessary anymore and this setting was
removed. You can now simply set a field to `{{ingest.timestamp}}` in a pipeline, and have that
field be of type `date` without any mapping errors.

### Java API changes

#### `setSource` methods require XContentType

Previously the `setSource` methods and other methods that accepted byte/string representations of
an object source did not require the XContentType to be specified. The auto-detection of the content
type is no longer used, so these methods now require the XContentType as an additional argument when
providing the source in bytes or as a string.

#### `DeleteByQueryRequest` requires an explicitly set query

In previous versions of Elasticsearch, delete by query requests without an explicit query
were accepted, match_all was used as the default query and all documents were deleted
as a result. From version 6.0.0, a `DeleteByQueryRequest` requires an explicit query be set.

#### `InternalStats` and `Stats` getCountAsString() method removed

The `count` value in the stats aggregation represents a doc count that shouldn’t require a formatted
version. This method was deprecated in 5.4 in favour of just using
`String.valueOf(getCount())` if needed

#### `ActionRequestBuilder#execute` returns `ActionFuture` rather than `ListenableActionFuture`

When sending a request through the request builders e.g. client.prepareSearch().execute(), it used to
be possible to call `addListener` against the returned `ListenableActionFuture`. With this change an
`ActionFuture` is returned instead, which is consistent with what the `Client` methods return, hence
it is not possible to associate the future with listeners. The `execute` method that accept a listener
as an argument can be used instead.

#### `Terms.Order` and `Histogram.Order` classes replace by `BucketOrder`

The `terms`, `histogram`, and `date_histogram` aggregation code has been refactored to use common
code for ordering buckets. The `BucketOrder` class must be used instead of `Terms.Order` and
`Histogram.Order`. The `static` methods in the `BucketOrder` class must be called instead of directly
accessing internal order instances, e.g. `BucketOrder.count(boolean)` and `BucketOrder.aggregation(String, boolean)`.
Use `BucketOrder.key(boolean)` to order the `terms` aggregation buckets by `_term`.

#### `getTookInMillis()` removed in `BulkResponse`, `SearchResponse` and `TermVectorsResponse`

In `BulkResponse`, `SearchResponse` and `TermVectorsResponse` `getTookInMillis()` method
has been removed in favor of `getTook` method. `getTookInMillis()` is easily replaced by
`getTook().getMillis()`.

#### `GetField` and `SearchHitField` replaced by `DocumentField`

As `GetField` and `SearchHitField` have the same members, they have been unified into
`DocumentField`.

#### Some Aggregation classes have moved packages

The classes for the variants of the range aggregation (geo_distance, date and ip) were moved into the `org.elasticsearch.search.aggregations.bucket.range`
package.

The `org.elasticsearch.search.aggregations.bucket.terms.support` package was removed and the classes were moved to
`org.elasticsearch.search.aggregations.bucket.terms`.

The filter aggregation classes were moved to `org.elasticsearch.search.aggregations.bucket.filter`

#### Constructor for `PercentileRanksAggregationBuilder` has changed

It is now required to include the desired ranks as a non-null, non-empty array of doubles to the builder’s constructor,
rather than configuring them via a setter on the builder. The setter method `values()` has correspondingly
been removed.

### Mapping changes

#### Coercion of boolean fields

Previously, Elasticsearch recognized the strings `true`, `false`, `on`, `off`, `yes`, `no`, `0`, `1` as booleans. Elasticsearch 6.0
recognizes only the strings `true` and `false` as booleans and will throw an error otherwise. For backwards compatibility purposes, during the 6.x
series the previous coercion rules will continue to work on pre-6.0 indices. This means that you do not need to change affected existing
mappings immediately. However, it is not possible to create new indices from existing index templates that violate the strict `boolean`
coercion rules.

#### The `_all` meta field is now disabled by default

On new mappings, the `_all` meta field that contains a copy of the text from
each field is now disabled by default. The `query_string` and
`simple_query_string` queries that previously used `_all` to search will now
check if `_all` is enabled/disabled and switch to executing the query across all
fields if `_all` is disabled. `_all` can no longer be configured for indices
created with Elasticsearch version 6.0 or later.

#### The `include_in_all` mapping parameter is now disallowed

Since the `_all` field is now disabled by default and cannot be configured for
indices created with Elasticsearch 6.0 or later, the `include_in_all` setting is
now disallowed for these indices' mappings.

#### Unrecognized `match_mapping_type` options not silently ignored

Previously Elasticsearch would silently ignore any dynamic templates that
included a `match_mapping_type` type that was unrecognized. An exception is now
thrown on an unrecognized type.

#### Validation of `locale` on date fields

The `locale` option of `date` fields previously allowed almost any string values,
and unrecognized values would simply be ignored. Unrecognized values are now
rejected on indices created with Elasticsearch 6.0 or newer.

### Packaging changes

#### Configuring custom user and group for package is no longer allowed

Previously someone could configure the `$ES_USER` and `$ES_GROUP` variables to
change which user and group Elasticsearch was run as. This is no longer
possible, the DEB and RPM packages now exclusively use the user and group
`elasticsearch`. If a custom user or group is needed then a provisioning system
should use the tarball distribution instead of the provided RPM and DEB
packages.

#### `path.conf` is no longer a configurable setting

Previous versions of Elasticsearch enabled setting `path.conf` as a
setting. This was rather convoluted as it meant that you could start
Elasticsearch with a config file that specified via `path.conf` that
Elasticsearch should use another config file. Instead, to configure a custom
config directory, use the [`ES_PATH_CONF` environment variable](settings.html#config-files-location).

#### `CONF_DIR` is no longer supported

Previous versions of Elasticsearch enabled using the `CONF_DIR` environment
variable to specify a custom configuration directory for some configuration
files and some scripts (it was used inconsistently). Starting in Elasticsearch
6.0.0, the usage of this environment variable has been superceded by
`ES_PATH_CONF`, and this new environment variable is consistently used for all
configuration files and scripts.

#### Default path settings are removed

Previous versions of Elasticsearch enabled setting `default.path.data` and
`default.path.logs` to set the default data path and default logs path if they
were not otherwise set in the configuration file. These settings have been
removed and now data paths and log paths can be configured via settings
only. Related, this means that the environment variables `DATA_DIR` and
`LOG_DIR` no longer have any effect as these were used to set
`default.path.data` and `default.path.logs` in the packaging scripts.

Additionally, this means that if you were using the package distributions (i.e.,
you have installed Elasticsearch from the RPM or the DEB distributions), you had
not previously explicitly configured `path.data` or `path.logs`, and you carry
over your `elasticsearch.yml` file from 5.x, then you will need to add settings
for `path.data` and `path.logs`. To use the defaults that you were implicitly
using previously, you should add these lines to your `elasticsearch.yml`:

```
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
```

(If you already had explicit values for either of these settings, you should of
course preserve those). If you do not do this, Elasticsearch will refuse to
start.

#### 32-bit is no longer maintained

We previously attempted to ensure that Elasticsearch could be started on 32-bit
JVM (although a bootstrap check prevented using a 32-bit JVM in production). We
are no longer maintaining this attempt.

#### `-server` flag no longer filtered in the Windows service

Related to the previous change that 32-bit is no longer supported, the default
`jvm.options` file that ships with Elasticsearch no longer includes the
`-server` flag. Previously, the installation of the Windows service would filter
the `-server` flag because it is not compatible with the service. Since the
default `jvm.options` file no longer includes `-server`, the filtering of this
flag was removed from the installation of the Windows service. This means that
if you have a `jvm.options` file that includes this flag you will need to remove
it.

#### `ES_JVM_OPTIONS` is no longer supported

The environment variable `ES_JVM_OPTIONS` that enabled a custom location for the
`jvm.options` file has been removed in favor of using the environment variable
`ES_PATH_CONF`. This environment variable is already used in the packaging to
support relocating the configuration files so this change merely aligns the
other configuration files with the location of the `jvm.options` file.

#### `ES_INCLUDE` is no longer supported

The environment variable `ES_INCLUDE` could previously be used to establish the
environment used to start Elasticsearch (and various supporting scripts). This
legacy feature could be useful when there were several environment variables
useful for configuring JVM options; this functionality had previously been
replaced by [Setting JVM options](jvm-options.html). Therefore, `ES_INCLUDE` has been removed.

#### Logging configuration

Previously Elasticsearch exposed a single system property (`es.logs`) that
included the absolute path to the configured logs directory, and the prefix of
the filenames used for the various logging files (the main log file, the
deprecation log, and the slow logs). This property has been replaced in favor of
three properties:

* `es.logs.base_path`: the absolute path to the configured logs directory

* `es.logs.cluster_name`: the default prefix of the filenames used for the
various logging files

* `es.logs.node_name`: exposed if `node.name` is configured for inclusion in
the filenames of the various logging files (if you prefer)

### Percolator changes

#### Deprecated percolator and mpercolate apis have been removed

Instead the `percolate` query should be used via either the search or msearch apis.

#### The percolator.map_unmapped_fields_as_string setting has been deprecated

The `percolator.map_unmapped_fields_as_text` setting should be used instead.

### Plugins changes

#### Mapper attachments plugin

* The mapper attachments plugin has been deprecated in elasticsearch 5.0 and is now removed.
You can use [ingest attachment plugin](/guide/en/elasticsearch/plugins/6.8/ingest-attachment.html) instead.

#### S3 Repository plugin

* The bucket an s3 repository is configured with will no longer be created automatically.
It must exist before the s3 repository is created.

* Support for specifying s3 credentials through environment variables and
system properties has been removed. Use the `elasticsearch-keystore` tool
to securely store the credentials.

* Specifying region has been removed. This includes the settings `cloud.aws.region`,
`cloud.aws.s3.region`, `repositories.s3.region`, and specifying
region inside the repository settings. Instead, specify the full endpoint if a custom
s3 location is needed, or rely on the default behavior which automatically locates
the region of the configured bucket.

* Specifying s3 signer type has been removed, including `cloud.aws.signer` and `cloud.aws.s3.signer`.

* Global repositories settings have been removed. This includes `repositories.s3.bucket`,
`repositories.s3.server_side_encryption`, `repositories.s3.buffer_size`,
`repositories.s3.max_retries`, `repositories.s3.use_throttle_retries`,
`repositories.s3.chunk_size`, `repositories.s3.compress`, `repositories.s3.storage_class`,
`repositories.s3.canned_acl`, `repositories.s3.base_path`, and
`repositories.s3.path_style_access`. Instead, these settings should be set directly in the
 settings per repository.
 See [S3 Repository settings](/guide/en/elasticsearch/plugins/6.8/repository-s3-repository.html).

* Shared client settings have been removed. This includes  `cloud.aws.access_key`,
 `cloud.aws.secret_key`, `cloud.aws.protocol`, `cloud.aws.proxy.host`,
 `cloud.aws.proxy.port`, `cloud.aws.proxy.username`, `cloud.aws.proxy.password`,
 `cloud.aws.signer`, `cloud.aws.read_timeout`, `cloud.aws.s3.access_key`,
 `cloud.aws.s3.secret_key`, `cloud.aws.s3.protocol`, `cloud.aws.s3.proxy.host`,
 `cloud.aws.s3.proxy.port`, `cloud.aws.s3.proxy.username`, `cloud.aws.s3.proxy.password`,
 `cloud.aws.s3.signer`, `cloud.aws.s3.read_timeout`, `repositories.s3.access_key`,
 `repositories.s3.secret_key`, `repositories.s3.endpoint` and `repositories.s3.protocol`.
Instead, use the new named client settings under `s3.client.CLIENT_NAME.*`.

* The `path_style_access` setting has been removed. The repository will use the appropriate path style access based on the configured endpoint.

#### Azure Repository plugin

* The container an azure repository is configured with will no longer be created automatically.
It must exist before the azure repository is created.

* Global repositories settings you are able to set in elasticsearch config file under `repositories.azure`
name space have been removed. This includes `repositories.azure.account`, `repositories.azure.container`,
`repositories.azure.base_path`, `repositories.azure.location_mode`, `repositories.azure.chunk_size` and
`repositories.azure.compress`.
You must set those settings per repository instead. Respectively `account`, `container`, `base_path`,
`location_mode`, `chunk_size` and `compress`.
See [Azure Repository settings](/guide/en/elasticsearch/plugins/6.8/repository-azure-repository-settings.html#repository-azure-repository-settings).

#### GCS Repository plugin

* The `service_account` setting has been removed. A service account json credential file must now be
specified in the [elasticsearch keystore](secure-settings.html).

#### EC2 Discovery plugin

* Specifying ec2 signer type has been removed, including `cloud.aws.signer` and `cloud.aws.ec2.signer`.

* The region setting has been removed. This includes the settings `cloud.aws.region`
and `cloud.aws.ec2.region`. Instead, specify the full endpoint.

* All `cloud.aws.*` and `cloud.aws.ec2.*` settings have been removed. Use `discovery.ec2.*` settings instead.

#### Ignoring hidden folders

Previous versions of Elasticsearch would skip hidden files and directories when
scanning the plugins folder. This leniency has been removed.

#### ICU Analysis plugin

The icu4j library has been upgraded to 59.1,
Indices created in the previous major version will need to be reindexed
in order to return correct (and correctly ordered) results,
and to take advantage of new characters.

#### Plugins should not construct `Environment` instances from `Settings`

Previously, plugins could construct an `Environment` instance from `Settings` to
discover the path to plugin-specific config files. This will no longer work in
all situations as the `Settings` object does not carry the necessary information
for the config path to be set correctly. Instead, plugins that need to know the
config path should have a single constructor that accepts a pair of `Settings`
and `Path` instances, and construct an `Environment` using the corresponding
constructor on `Environment`.

### Reindex changes

#### `size` parameter

The `size` parameter can no longer be explicitly set to `-1`. If all documents are required then the `size` parameter should not be set.

### REST changes

#### Unquoted JSON

In previous versions of Elasticsearch, JSON documents were allowed to contain unquoted field names.
This feature was removed in the 5.x series, but a backwards-compatibility layer was added via the
system property `elasticsearch.json.allow_unquoted_field_names`. This backwards-compatibility layer
has been removed in Elasticsearch 6.0.0.

#### Duplicate Keys in JSON, CBOR, Yaml and Smile

In previous versions of Elasticsearch, documents were allowed to contain duplicate keys. Elasticsearch 6.0.0
 enforces that all keys are unique. This applies to all content types: JSON, CBOR, Yaml and Smile.

#### Content-Type Auto-detection

In previous versions of Elasticsearch, having a proper Content-Type for the data in a request was not enforced.
Elasticsearch 6.0.0 enforces that all requests with a body must have a supported Content-Type and this type will
be used when parsing the data.

When using the `source` query string parameter, the `source_content_type` parameter must also be specified with
the media type of the source.

#### Boolean API parameters

All REST APIs parameters (both request parameters and JSON body) support providing boolean "false" as the
value `false` and boolean "true" as the value `true`. All other values will raise an error.

#### Analyze API changes

The deprecated request parameters and plain text in request body has been removed. Define parameters in request body.

#### Support custom normalizer in Analyze API

Analyze API can analyze normalizer and custom normalizer.
In previous versions of Elasticsearch, Analyze API is requiring a `tokenizer` or `analyzer` parameter.
In Elasticsearch 6.0.0, Analyze API can analyze a text as a keyword field with custom normalizer
or if `char_filter`/`filter` is set and `tokenizer`/`analyzer` is not set.

#### `timestamp` and `ttl` in index requests

`timestamp` and `ttl` are not accepted anymore as parameters of index/update
requests.

#### Refresh requests with one or more shard failures return HTTP 500 response instead of 200

Refresh requests that are broadcast to multiple shards that can have one or more
shards fail during the request now return a 500 response instead of a 200
response in the event there is at least one failure.

#### Delete by Query API requires an explicit query

In previous versions of Elasticsearch, delete by query requests without an explicit query
were accepted, match_all was used as the default query and all documents were deleted
as a result. From version 6.0.0, delete by query requests require an explicit query.

#### DELETE document calls now implicitly create the type

Running `DELETE index/type/id` now implicitly creates `type` with a default
mapping if it did not exist yet.

#### Indices information APIs

Previously it was possible to execute `GET /_aliases,_mappings` or `GET
/myindex/_settings,_alias` by separating multiple types of requests with commas
in order to retrieve multiple types of information about one or more indices.
This comma-separation for retrieving multiple pieces of information has been
removed. `GET /_all` can be used to retrieve all aliases, settings, and
mappings for all indices.

In order to retrieve only the mapping for an index use:
`GET /myindex/_mapping` (or `_alias` for a list of aliases, or `_settings` for the settings).

#### Requests to existing endpoints with incorrect HTTP verb now return 405 responses

Issuing a request to an endpoint that exists, but with an incorrect HTTP verb
(such as a `POST` request to `/myindex/_settings`) now returns an HTTP 405
response instead of a 404. An `Allow` header is added to the 405 responses
containing the allowed verbs. For example:

```
$ curl -v -XPOST 'localhost:9200/my_index/_settings'
*   Trying 127.0.0.1...
* TCP_NODELAY set
* Connected to localhost (127.0.0.1) port 9200 (#0)
> POST /my_index/_settings HTTP/1.1
> Host: localhost:9200
> User-Agent: curl/7.51.0
> Accept: */*
>
< HTTP/1.1 405 Method Not Allowed
< Allow: PUT,GET
< content-type: application/json; charset=UTF-8
< content-length: 134
<
{
  "error" : "Incorrect HTTP method for uri [/my_index/_settings] and method [POST], allowed: [PUT, GET]",
  "status" : 405
}
* Curl_http_done: called premature == 0
* Connection #0 to host localhost left intact
```

#### Disallow using `_cache` and `_cache_key`

The `_cache` and `_cache_key` options in queries have been deprecated since version 2.0.0 and
have been ignored since then, issuing a deprecation warning. These options have now been completely
removed, so using them now will throw an error.

#### IndexClosedException to return 400 status code

An `IndexClosedException` is returned whenever an api that doesn’t support
closed indices (e.g. search) is called passing closed indices as parameters
and `ignore_unavailable` is set to `false`. The response status code returned
in such case changed from `403` to `400`

### Scripting changes

#### Groovy, JavaScript, and Python languages removed

The Groovy, JavaScript, and Python scripting languages were deprecated in
elasticsearch 5.0 and have now been removed. Use painless instead.

#### Native scripts removed

Native scripts have been removed. Instead,
[implement a `ScriptEngine`](modules-scripting-engine.html).

#### Date fields now return dates

`doc.some_date_field.value` now returns `ReadableDateTime`s instead of
milliseconds since epoch as a `long`. The same is true for
`doc.some_date_field[some_number]`. Use `doc.some_date_field.value.millis` to
fetch the milliseconds since epoch if you need it.

#### Removed access to index internal via the `_index` variable

The `_index` variable has been removed. If you used it for advanced scoring, consider writing a `Similarity` plugin.

#### Script Settings

All of the existing scripting security settings have been removed.  Instead
they are replaced with `script.allowed_types` and `script.allowed_contexts`.

#### `lang` can no longer be specified when using a stored script as part of a request

The `lang` variable can no longer be specified as part of a request that uses a stored
script otherwise an error will occur.  Note that a request using a stored script is
different from a request that puts a stored script.  The language of the script has
already been stored as part of the cluster state and an `id` is sufficient to access
all of the information necessary to execute a stored script.

#### 'lang` can no longer be used when putting, getting, or deleting a stored script

Stored scripts can no longer have the `lang` parameter specified as part of the url
when performing PUT, GET, and DELETE actions on the `_scripts/` path.  All stored
scripts must have a unique `id` as the namespace is only `id` now and no longer `lang`
and `id`.

#### Stored search template apis removed

The PUT, GET and DELETE `_search/template` apis have been removed. Store search templates with the stored scripts apis instead.

For example, previously one might have stored a search template with the following:

```
PUT /_search/template/custom_template
{
  "query": {
    "match": {
      "f1": "{{f1}}"
    }
  }
}
```

And instead one would now use the following:

```
PUT /_scripts/custom_template
{
  "script": {
    "lang": "mustache",
    "source": {
      "query": {
        "match": {
          "f1": "{{f1}}"
        }
      }
    }
  }
}
```

### Search and Query DSL changes

#### Changes to queries

* The `collect_payloads` parameter of the `span_near` query has been removed. Payloads will be
loaded when needed.

* Queries on boolean fields now strictly parse boolean-like values. This means
only the strings `"true"` and `"false"` will be parsed into their boolean
counterparts. Other strings will cause an error to be thrown.

* The `in` query (a synonym for the `terms` query) has been removed

* The `geo_bbox` query (a synonym for the `geo_bounding_box` query) has been removed

* The `mlt` query (a synonym for the `more_like_this` query) has been removed.

* The deprecated `like_text`, `ids` and `docs` parameters (all synonyms for `like`) of the `more_like_this` query have
been removed. Also the deprecated `min_word_len` (a synonym for `min_word_length`) and `max_word_len`
(a synonym for `max_word_length`) have been removed.

* The `fuzzy_match` and `match_fuzzy` query (synonyma for the `match` query) have been removed

* The `terms` query now always returns scores equal to `1` and is not subject to
`indices.query.bool.max_clause_count` anymore.

* The deprecated `indices` query has been removed.

* Support for empty query objects (`{ }`) has been removed from the query DSL.
An error is thrown whenever an empty query object is provided.

* The deprecated `minimum_number_should_match` parameter in the `bool` query has
been removed, use `minimum_should_match` instead.

* The `query_string` query now correctly parses the maximum number of
states allowed when
[determinizing](https://en.wikipedia.org/wiki/Powerset_construction#Complexity)
a regex as `max_determinized_states` instead of the typo
`max_determined_states`.

* The `query_string` query no longer accepts `enable_position_increment`, use
`enable_position_increments` instead.

* For `geo_distance` queries, sorting, and aggregations the `sloppy_arc` option
has been removed from the `distance_type` parameter.

* The `geo_distance_range` query, which was deprecated in 5.0, has been removed.

* The `optimize_bbox` parameter has been removed from `geo_distance` queries.

* An `envelope` crossing the dateline in a `geo_shape `query is now processed
correctly when specified using REST API instead of having its left and
right corners flipped.

* The `ignore_malformed` and `coerce` parameters have been removed from
`geo_bounding_box`, `geo_polygon`, and `geo_distance` queries.

* The `disable_coord` parameter of the `bool` and `common_terms` queries has
been removed. If provided, it will be ignored and issue a deprecation warning.

* The `template` query has been removed. This query was deprecated since 5.0

* The `percolate` query’s `document_type` has been deprecated. From 6.0 and later
it is no longer required to specify the `document_type` parameter.

* The `split_on_whitespace` parameter for the `query_string` query has been removed.
If provided, it will be ignored and issue a deprecation warning.
The `query_string` query now splits on operator only.

* The `use_dis_max` parameter for the `query_string` query has been removed.
If provided, it will be ignored and issue a deprecation warning.
The `tie_breaker` parameter must be used instead.

* The `auto_generate_phrase_queries` parameter for the `query_string` query has been removed,
use an explicit quoted query instead.
If provided, it will be ignored and issue a deprecation warning.

* The `all_fields` parameter for the `query_string` and `simple_query_string` has been removed.
Set `default_field` to *` instead.
If provided, `default_field` will be automatically set to `*`

* The `index` parameter in the terms filter, used to look up terms in a dedicated index is
now mandatory. Previously, the index defaulted to the index the query was executed on. Now this index
must be explicitly set in the request.

* The deprecated `type` and `slop` parameter for the `match` query have been removed. Instead of
setting the `type`, the `match_phrase` or `match_phrase_prefix` should be used. The `slop` removed from
the `match` query but is supported for `match_phrase` and `match_phrase_prefix`.

* The deprecated `phrase_slop` parameter (a synonym for the `slop` parameter) of the `match_phrase` query has been removed.

* The deprecated `query` parameter (a synonym for the `filter` parameter) of the `constant_score` query has been removed.

* The deprecated `phrase_slop` parameter (a synonym for the `slop` parameter) of the `multi_match` query has been removed.

* The deprecated `prefix` parameter (a synonym for the `value` parameter) of the `prefix` query has been removed.

* The deprecated `le` (a synonym for `lte`) and `ge` (a synonym for `gte`) parameter of the `range` query have been removed.

* The deprecated `types` and `_type` synonyms for the `type` parameter of the `ids` query have been removed

* The deprecated multi term rewrite parameters `constant_score_auto`, `constant_score_filter` (synonyms for `constant_score`)
have been removed.

* Setting a negative `weight` in Function Score Query is deprecated.

#### Search shards API

The search shards API no longer accepts the `type` url parameter, which didn’t
have any effect in previous versions.

#### Changes to the Profile API

The `"time"` field showing human readable timing output has been replaced by the `"time_in_nanos"`
field which displays the elapsed time in nanoseconds. The `"time"` field can be turned on by adding
`"?human=true"` to the request url. It will display a rounded, human readable time value.

#### Scoring changes

##### Query normalization

Query normalization has been removed. This means that the TF-IDF similarity no
longer tries to make scores comparable across queries and that boosts are now
integrated into scores as simple multiplicative factors.

Other similarities are not affected as they did not normalize scores and
already integrated boosts into scores as multiplicative factors.

See [`LUCENE-7347`](https://issues.apache.org/jira/browse/LUCENE-7347) for more
information.

##### Coordination factors

Coordination factors have been removed from the scoring formula. This means that
boolean queries no longer score based on the number of matching clauses.
Instead, they always return the sum of the scores of the matching clauses.

As a consequence, use of the TF-IDF similarity is now discouraged as this was
an important component of the quality of the scores that this similarity
produces. BM25 is recommended instead.

See [`LUCENE-7347`](https://issues.apache.org/jira/browse/LUCENE-7347) for more
information.

##### Negative scores are deprecated in Function Score Query

Negative scores in the Function Score Query are deprecated. If a negative
score is produced as a result of computation (e.g. in `script_score` or
`field_value_factor` functions), a deprecation warning will be issued in
this major version, and an error will be thrown in the next major version.

#### Fielddata on `_uid`

Fielddata on `_uid` is deprecated. It is possible to switch to `_id` instead
but the only reason why it has not been deprecated too is because it is used
for the `random_score` function. If you really need access to the id of
documents for sorting, aggregations or search scripts, the recommendation is
to duplicate the id as a field in the document.

#### Highlighters

The `unified` highlighter is the new default choice for highlighter.
The offset strategy for each field is picked internally by this highlighter depending on the
type of the field (`index_options`).
It is still possible to force the highlighter to `fvh` or `plain` types.

The `postings` highlighter has been removed from Lucene and Elasticsearch.
The `unified` highlighter outputs the same highlighting when `index_options` is set
 to `offsets`.

#### `fielddata_fields`

The deprecated `fielddata_fields` have now been removed. `docvalue_fields` should be used instead.

#### `docvalue_fields`

`docvalue_fields` now have a default upper limit of 100 fields that can be requested.
This limit can be overridden by using the `index.max_docvalue_fields_search` index setting.

#### `script_fields`

`script_fields` now have a default upper limit of 32 script fields that can be requested.
This limit can be overridden by using the `index.max_script_fields` index setting.

#### Inner hits

The source inside a hit of inner hits keeps its full path with respect to the entire source.
In prior versions the source field names were relative to the inner hit.

#### Scroll

The `from` parameter can no longer be used in the search request body when initiating a scroll.
The parameter was already ignored in these situations, now in addition an error is thrown.

#### Limit on from/size in top hits and inner hits

The maximum number of results (`from` + `size`) that is allowed to be retrieved
via inner hits and top hits has been limited to 100. The limit can be controlled
via the `index.max_inner_result_window` index setting.

#### Scroll queries that use the request_cache are deprecated

Setting `request_cache:true` on a query that creates a scroll ('scroll=1m`)
 is deprecated and the request will not use the cache internally.
In future versions we will return a `400 - Bad request` instead of just ignoring
the hint.
Scroll queries are not meant to be cached.

#### Limiting the number of terms that can be used in a Terms Query request

Executing a Terms Query with a lot of terms may degrade the cluster performance,
as each additional term demands extra processing and memory.
To safeguard against this, the maximum number of terms that can be used in a
Terms Query request has been limited to 65536. This default maximum can be changed
for a particular index with the index setting `index.max_terms_count`.

#### Invalid `_search` request body

For 6.x and starting in 6.3 a deprecation warning will be printed to warn
against search requests that contain extra tokens after the main object.
These extra tokens were ignored by the query parser before 6.3 but the next
 major version will not accept invalid body anymore.

#### Context suggester without contexts

The ability to query and index context enabled suggestions without contexts
has been deprecated. Context enabled suggestion queries without contexts have
to visit every suggestion, which degrades the search performance considerably.

For geo context the value of the `path` parameter is now validated against the mapping,
and if `path` points to a non `geo_point` field or the field doesn’t exist a deprecation
warning will be issued. In 7.0 it will be required for the `path` to point to a correct
`geo_point` field.

#### Limiting the max number of expansion of span_multi queries

`span_multi` queries will hit too many clauses failure if the number of terms that match the
query exceeds the boolean query limit (defaults to 1024). To avoid an unbounded expansion you
can set the [rewrite method](query-dsl-multi-term-rewrite.html) of the multi term query to `top_terms_*`
rewrite. Or, if you use `span_multi` on `prefix` query only, you can activate the
[`index_prefixes`](index-prefixes.html) field option of the `text` field instead. This will
rewrite any prefix query on the field to a a single term query that matches the indexed prefix.

#### Negative boosts are deprecated

Setting a negative `boost` for a query or a field is deprecated and will throw an error in the next
major version. To deboost a specific query or field you can use a `boost` comprise between 0 and 1.

#### Limit the number of open scroll contexts

The number of scroll contexts allowed per node will be limited to 500 by default in the next major
version. Open scroll contexts are unlimited by default in this version, you can change the dynamic
cluster setting `search.max_open_scroll_context` to force a limit. If the limit is unchanged, a
deprecation warning will be printed if the number of open scroll context is greater than 500 (the
default limit in the next major version).

#### The filter context is deprecated

The `filter` context is deprecated in Elasticsearch’s query builders,
the distinction between queries and filters is decided in Lucene depending
on whether queries need to access score or not. As a result `bool` queries with
`should` clauses that don’t need to access the score will issue a deprecation
warning when they automatically set `minimum_should_match` to 1.
This behavior will be removed in the next major version.

### Settings changes

#### Remove support for elasticsearch.json and elasticsearch.yaml configuration file

The configuration file found in the Elasticsearch config directory could previously have
a `.yml`, `.yaml` or `.json` extension. Only `elasticsearch.yml` is now supported.

#### Duplicate keys in configuration file

In previous versions of Elasticsearch, the configuration file was allowed to
contain duplicate keys. For example:

```
node:
  name: my-node

node
  attr:
    rack: my-rack
```

In Elasticsearch 6.0.0, this is no longer permitted. Instead, this must be
specified in a single key as:

```
node:
  name: my-node
  attr:
    rack: my-rack
```

#### Coercion of boolean settings

Previously, Elasticsearch recognized the strings `true`, `false`, `on`, `off`, `yes`, `no`, `0`, `1` as booleans. Elasticsearch 6.0
recognizes only `true` and `false` as boolean and will throw an error otherwise. For backwards compatibility purposes, during the 6.x series
index settings on pre-6.0 indices will continue to work. Note that this does not apply to node-level settings that are stored
in `elasticsearch.yml`.

#### Snapshot settings

The internal setting `cluster.routing.allocation.snapshot.relocation_enabled` that allowed shards with running snapshots to be reallocated to
different nodes has been removed. Enabling this setting could cause allocation issues if a shard got allocated off a node and then
reallocated back to this node while a snapshot was running.

#### Store throttling settings

Store throttling has been removed. As a consequence, the
`indices.store.throttle.type` and `indices.store.throttle.max_bytes_per_sec`
cluster settings and the `index.store.throttle.type` and
`index.store.throttle.max_bytes_per_sec` index settings are not
recognized anymore.

#### Store settings

The `default` `index.store.type` has been removed. If you were using it, we
advise that you simply remove it from your index settings and Elasticsearch
will use the best `store` implementation for your operating system.

#### Network settings

The blocking TCP client, blocking TCP server, and blocking HTTP server have been removed.
As a consequence, the `network.tcp.blocking_server`, `network.tcp.blocking_client`,
`network.tcp.blocking`,`transport.tcp.blocking_client`, `transport.tcp.blocking_server`,
and `http.tcp.blocking_server` settings are not recognized anymore.

The previously unused settings `transport.netty.max_cumulation_buffer_capacity`,
`transport.netty.max_composite_buffer_components` and
`http.netty.max_cumulation_buffer_capacity` have been removed.

#### Similarity settings

The `base` similarity is now ignored as coords and query normalization have
been removed. If provided, this setting will be ignored and issue a
deprecation warning.

#### Script Settings

All of the existing scripting security settings have been removed.  Instead
they are replaced with `script.allowed_types` and `script.allowed_contexts`.

#### Discovery Settings

The `discovery.type` settings no longer supports the values `gce`, `azure` and `ec2`.
Integration with these platforms should be done by setting the `discovery.zen.hosts_provider` setting to
one of those values.

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

### Stats and info changes

#### Removal of `throttle_time` in the `store` stats

Given that store throttling has been removed, the `store` stats do not report
`throttle_time` anymore.

#### FS stats no longer reports if the disk spins

Elasticsearch has defaulted to assuming that it is running on SSDs since
the 2.x series of Elasticsearch. As such, Elasticsearch no longer needs to
collect information from the operating system as to whether or not the
underlying disks of each data path spin or not. While this functionality was no
longer needed starting in the 2.x series of Elasticsearch, it was maintained in
the filesystem section of the nodes stats APIs. This information has now been
removed.