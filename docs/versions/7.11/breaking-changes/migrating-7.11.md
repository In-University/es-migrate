**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 7.11

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.11.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

* [Machine learning changes](migrating-7.11.html#breaking_711_ml_changes)

* [REST API changes](migrating-7.11.html#breaking_711_rest_changes)

* [Search changes](migrating-7.11.html#breaking_711_search_changes)

* [Transform changes](migrating-7.11.html#breaking_711_transform_changes)

* [Transport deprecations](migrating-7.11.html#breaking_711_transport_deprecations)

### Breaking changes

The following changes in Elasticsearch 7.11 might affect your applications
and prevent them from operating normally.
Before upgrading to 7.11, review these changes and take the described steps
to mitigate the impact.

Breaking changes introduced in minor versions are
normally limited to security and bug fixes.
Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

### Machine learning changes

The trained models API parameter `for_export` is now renamed to `exclude_generated`.

**Details**

The [get trained models API](/guide/en/elasticsearch/reference/7.17/get-trained-models.html) no longer accepts `for_export`.
Use `exclude_generated` instead.

#### REST API changes

REST APIs that do not use a request body now return an error if a body is provided.

**Details**

Several Elasticsearch REST APIs do not use a request body. In previous versions, you
could provide a request body when calling these APIs, and Elasticsearch would ignore the
body. These APIs now return an error if you provide a request body, even if
empty.

**Impact**

Update your application or workflow to avoid sending unneeded request bodies
in REST API requests.

#### Search changes

Keyword fields with a custom normalizer will use the normalized form when highlighting.

**Details**

Highlighters now use the same framework to load their values as the
`fields` section of a search response.  This means that normalization
will be applied to the values of a keyword field; for example, a
field configured with a lowercase normalizer will return highlighted
snippets in lower case.

Internal fields used for text search acceleration are hidden.

**Details**

Text fields can add internal subfields using extra analysis to speed
up prefix and phrase searches. Previously these were exposed to
the field caps API and were available for searching directly. However,
they did not implement all query types and could return bad results
or throw errors if used via the query DSL. These subfields are now
internal only and cannot be invoked as searchable fields in queries.

The significant text aggregation now throws an error if applied to a numeric field.

**Details**

The significant text aggregation could previously be applied to a fields that
were defined as numeric, which made little sense and would always return an
empty result. Given that applying a text-specific aggregation to a non-text
field is almost certainly a mistake, this has now been changed to throw an
error.

#### Transform changes

Transforms now write `group_by` dates as strings.

**Details**

Transforms now write dates used in a `group_by` as formatted ISO strings instead
of `epoch_millis` values. Previously constructed transforms will still use
`epoch_millis` values. You can configure and change the output format in the
settings of the transform.

### Deprecations

The following functionality has been deprecated in Elasticsearch 7.10
and will be removed in 8.0
While this won’t have an immediate impact on your applications,
we strongly encourage you take the described steps to update your code
after upgrading to 7.10.

Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Transport deprecations

The `es.unsafely_permit_handshake_from_incompatible_builds` system property is deprecated.

**Details**

The `es.unsafely_permit_handshake_from_incompatible_builds` system property is
now deprecated.

Elasticsearch verifies that communicating pairs of nodes of the same version are running
the same build and using the same wire format. You can bypass this check by
setting `es.unsafely_permit_handshake_from_incompatible_builds` to `true`.
Skipping this check is unsafe and not recommended.

**Impact**

To avoid deprecation warnings, discontinue use of the system property. Instead
ensure that all nodes of the same version are running the same build.