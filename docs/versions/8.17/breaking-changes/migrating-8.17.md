**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 8.17

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.17.

See also [*What’s new in 8.17*](release-highlights.html) and [Release notes](es-release-notes.html).

### Breaking changes

There are no breaking changes in Elasticsearch 8.17.

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.17
and will be removed in a future version.
While this won’t have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.17.

To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Mapping deprecations

Deprecate `_source.mode` in mappings

**Details**

Configuring `_source.mode` in mappings is deprecated and will be removed in future versions. Use `index.mapping.source.mode` index setting instead.

**Impact**

Use `index.mapping.source.mode` index setting instead

#### REST API deprecations

The format of non-detailed error responses is changing in v9

**Details**

When an error occurs when processing a request, Elasticsearch returns information on that error in the REST response.
If `http:detailed_errors.enabled: false` is specified in node settings with the v8 REST API and below,
the format of this response changes significantly.
Starting with the v9 REST API, the JSON structure of responses with errors when the `http.detailed_errors.enabled: false` option is set
will be the same as when detailed errors are enabled (which is the default).
To keep using the existing format for non-detailed error responses, use the v8 REST API.

**Impact**

If you have set `http.detailed_errors.enabled: false` (the default is `true`)
the structure of JSON when any exceptions occur will change with the v9 REST API.
To keep using the existing format, use the v8 REST API.