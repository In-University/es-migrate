## Migrating to 8.16

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.16.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

### Breaking changes

The following changes in Elasticsearch 8.16 might affect your applications
and prevent them from operating normally.
Before upgrading to 8.16, review these changes and take the described steps
to mitigate the impact.

#### Analysis changes

.Set lenient to true by default when using updateable synonyms
[%collapsible]
====
*Details* +
When a `synonym` or `synonym_graph` token filter is configured with `updateable: true`, the default `lenient`
value will now be `true`.

*Impact* +
`synonym` or `synonym_graph` token filters configured with `updateable: true` will ignore invalid synonyms by
default. This prevents shard initialization errors on invalid synonyms.
====

#### Mapping changes

.JDK locale database change
[%collapsible]
====
*Details* +
Elasticsearch 8.16 changes the version of the JDK that is included from version 22 to version 23. This changes the locale database that is used by Elasticsearch from the COMPAT database to the CLDR database. This change can cause significant differences to the textual date formats accepted by Elasticsearch, and to calculated week-dates.

If you run Elasticsearch 8.16 on JDK version 22 or below, it will use the COMPAT locale database to match the behavior of 8.15. However, starting with Elasticsearch 9.0, Elasticsearch will use the CLDR database regardless of JDK version it is run on.

*Impact* +
This affects you if you use custom date formats using textual or week-date field specifiers. If you use date fields or calculated week-dates that change between the COMPAT and CLDR databases, then this change will cause Elasticsearch to reject previously valid date fields as invalid data. You might need to modify your ingest or output integration code to account for the differences between these two JDK versions.

Starting in version 8.15.2, Elasticsearch will log deprecation warnings if you are using date format specifiers that might change on upgrading to JDK 23. These warnings are visible in Kibana.

For detailed guidance, refer to [Differences in locale information between JDK versions](#custom-date-format-locales) and the [Elastic blog](https://ela.st/jdk-23-locales).
====

#### ES|QL changes

.ESQL: Entirely remove META FUNCTIONS
[%collapsible]
====
*Details* +
Removes an undocumented syntax from ESQL: META FUNCTION. This was never
reliable or really useful. Consult the documentation instead.

*Impact* +
Removes an undocumented syntax from ESQL: META FUNCTION
====

#### REST API changes

.Reworking RRF retriever to be evaluated during rewrite phase
[%collapsible]
====
*Details* +
In this release (8.16), we have introduced major changes to the retrievers framework 
and how they can be evaluated, focusing mainly on compound retrievers 
like `rrf` and `text_similarity_reranker`, which allowed us to support full 
composability (i.e. any retriever can be nested under any compound retriever), 
as well as supporting additional search features like collapsing, explaining, 
aggregations, and highlighting.

To ensure consistency, and given that this rework is not available until 8.16, 
`rrf` and `text_similarity_reranker`  retriever queries would now  
throw an exception in a mixed cluster scenario, where there are nodes 
both in current or later (i.e. >= 8.16) and previous ( <= 8.15) versions.

As part of the rework, we have also removed the `_rank` property from 
the responses of an `rrf` retriever.

*Impact* +
- Users will not be able to use the `rrf` and `text_similarity_reranker` retrievers in a mixed cluster scenario
with previous releases (i.e. prior to 8.16), and the request will throw an `IllegalArgumentException`.
- `_rank` has now been removed from the output of the `rrf` retrievers so trying to directly parse the field
will throw an exception
====

.Update data stream lifecycle telemetry to track global retention
[%collapsible]
====
*Details* +
In this release we introduced global retention settings that fulfil the following criteria:

- a data stream managed by the data stream lifecycle,
- a data stream that is not an internal data stream.

As a result, we defined different types of retention:

- **data retention**: the retention configured on data stream level by the data stream user or owner
- **default global retention:** the retention configured by an admin on a cluster level and applied to any
data stream that doesn't have data retention and fulfils the criteria.
- **max global retention:** the retention configured by an admin to guard against having long retention periods.
Any data stream that fulfills the criteria will adhere to the data retention unless it exceeds the max retention,
in which case the max global retention applies.
- **effective retention:** the retention that applies on the data stream that fulfill the criteria at a given moment
in time. It takes into consideration all the retention above and resolves it to the retention that will take effect.

Considering the above changes, having a field named `retention` in the usage API was confusing. For this reason, we
renamed it to `data_retention` and added telemetry about the other configurations too.

*Impact* +
Users that use the field `data_lifecycle.retention` should use the `data_lifecycle.data_retention`
====

#### Ingest changes

.Ingest enrich.cache_size name inconsistency
[%collapsible]
====
*Details* +
The setting `enrich.cache_size` was temporarily renamed to `enrich.cache.size` in `8.16.0` and `8.16.1`.
The preferred resolution is upgrading to `8.16.2` or higher. If that is not possible, temporarily rename the setting to `enrich.cache.size` until you are able to upgrade to `8.16.2` or higher. The temporary name is deprecated and will be removed in a future version.

*Impact* +
If your cluster has `enrich.cache_size` configured prior to upgrading to `8.16.0` or `8.16.1` you may see errors that prevent the upgrade from proceeding. 
====

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.16
and will be removed in a future version.
While this won't have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.16.

To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

#### Analysis deprecations

.Deprecate dutch_kp and lovins stemmer as they are removed in Lucene 10
[%collapsible]
====
*Details* +
kp, dutch_kp, dutchKp and lovins stemmers are deprecated and will be removed.

*Impact* +
These stemmers will be removed and will be no longer supported.
====

.deprecate `edge_ngram` side parameter
[%collapsible]
====
*Details* +
edge_ngram will no longer accept the side parameter.

*Impact* +
Users will need to update any usage of edge_ngram token filter that utilizes `side`. If the `back` value was used, they can achieve the same behavior by using the `reverse` token filter.
====

#### CRUD deprecations

.Deprecate dot-prefixed indices and composable template index patterns
[%collapsible]
====
*Details* +
Indices beginning with a dot '.' are reserved for system and internal indices, and should not be used by and end-user. Additionally, composable index templates that contain patterns for dot-prefixed indices should also be avoided, as these patterns are meant for internal use only. In a future Elasticsearch version, creation of these dot-prefixed indices will no longer be allowed.

*Impact* +
Requests performing an action that would create an index beginning with a dot (indexing a document, manual creation, reindex), or creating an index template with index patterns beginning with a dot, will contain a deprecation header warning about dot-prefixed indices in the response.
====

#### REST API deprecations

.Adding deprecation warnings for rrf using rank and `sub_searches`
[%collapsible]
====
*Details* +
Search API parameter `sub_searches` will no longer be a supported and will be removed in future releases. Similarly, `rrf` can only be used through the specified `retriever` and no longer though the `rank` parameter

*Impact* +
Requests specifying rrf through `rank` and/or `sub_searches` elements will be disallowed in a future version. Users should instead utilize the new `retriever` parameter.
====

.Deprecate legacy params from range query
[%collapsible]
====
*Details* +
Range query will not longer accept `to`, `from`, `include_lower`, and `include_upper` parameters.

*Impact* +
Instead use `gt`, `gte`, `lt` and `lte` parameters.
====