## Migrating to 8.4

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.4.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

### Breaking changes

There are no breaking changes in Elasticsearch 8.4.

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.4
and will be removed in a future version.
While this won't have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.4.

To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

#### REST API deprecations

.Deprecate the `_knn_search` endpoint
[%collapsible]
====
*Details* +
-| The kNN search API is deprecated in favor of the new 'knn' option inside the search API. The 'knn' option is now the recommended way of running ANN search.

*Impact* +
Users should switch from `_knn_search` to the search `knn` option.
====