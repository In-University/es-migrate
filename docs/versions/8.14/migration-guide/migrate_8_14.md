## Migrating to 8.14

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.14.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

coming::[8.14.0]

### Breaking changes

The following changes in Elasticsearch 8.14 might affect your applications
and prevent them from operating normally.
Before upgrading to 8.14, review these changes and take the described steps
to mitigate the impact.

There are no notable breaking changes in Elasticsearch 8.14.
But there are some less critical breaking changes.

#### REST API changes

.Prevent DLS/FLS if `replication` is assigned
[%collapsible]
====
*Details* +
For cross-cluster API keys, Elasticsearch no longer allows specifying document-level security (DLS) or field-level security (FLS) in the `search` field, if `replication` is also specified. Elasticsearch likewise blocks the use of any existing cross-cluster API keys that meet this condition.

*Impact* +
Remove any document-level security (DLS) or field-level security (FLS) definitions from the `search` field for cross-cluster API keys that also have a `replication` field, or create two separate cross-cluster API keys, one for search and one for replication.
====

#### Stricter Document Level Security (DLS)

.Document Level Security (DLS) applies stricter checks for the validate query API and for terms aggregations when min_doc_count is set to 0.

[%collapsible]
====
*Details* +
When Document Level Security (DLS) is applied to terms aggregations and min_doc_count is set to 0, stricter security rules apply.

When Document Level Security (DLS) is applied to the validate query API with the rewrite parameter, stricter security rules apply.

*Impact* +
If needed, test workflows with DLS enabled to ensure that the stricter security rules do not impact your application.
====

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.14
and will be removed in a future version.
While this won't have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.14.

To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

#### Mapping deprecations

.Deprecate allowing `fields` in scenarios where it is ignored
[%collapsible]
====
*Details* +
The following mapped types have always ignored `fields` when using multi-fields. This deprecation makes this clearer and we will completely disallow `fields` for these mapped types in the future.

*Impact* +
In the future, `join`, `aggregate_metric_double`, and `constant_keyword`, will all disallow supplying `fields` as a parameter in the mapping.
====