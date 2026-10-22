## Migrating to 7.17

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.17.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

### Breaking changes

The following changes in Elasticsearch 7.17 might affect your applications
and prevent them from operating normally.
Before upgrading to 7.17, review these changes and take the described steps
to mitigate the impact.

// NOTE: The notable-breaking-changes tagged regions are re-used in the
// Installation and Upgrade Guide
// tag::notable-breaking-changes[]
#### Packaging changes

.The Windows MSI installer package is no longer available.
[%collapsible]
====
*Details* +
We no longer release Windows MSI installer packages for Elasticsearch. These packages
were previously released in beta and didn't receive widespread adoption.

*Impact* +
To install Elasticsearch on Windows, use the {ref}/zip-windows.html[`.zip` archive
package] instead.
====
// end::notable-breaking-changes[]

### Deprecations

The following functionality has been deprecated in Elasticsearch 7.17
and will be removed in 8.0.
While this won't have an immediate impact on your applications,
we strongly encourage you take the described steps to update your code
after upgrading to 7.17.

NOTE: Significant changes in behavior are deprecated in a minor release and
the old behavior is supported until the next major release.
To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

// tag::notable-breaking-changes[]
#### Cluster and node setting deprecations

.Deprecation for truststores with no trust entries
[%collapsible]
====
*Details* +
The use of SSL truststores that do not contain any trusted entries has been deprecated.
The various `*.ssl.truststore.path` settings (for example
`xpack.security.transport.ssl.truststore.path` or `xpack.http.ssl.truststore.path`) can
be used to configure a set of "trust anchors" for SSL certificate verification. In Elasticsearch
version 7 and earlier, it was permitted to configure a truststore that did not contain
any trust anchors (that is, it was empty, or it contained "private key" entries only).
In Elasticsearch version 8 and above, a `truststore.path` without any trusted certificate entries
is no longer accepted, and will cause an error. This configuration is now deprecated in
Elasticsearch version 7.17

*Impact* +
To avoid deprecation warnings, remove any SSL truststores that do not
contain any trusted entries.
====

.Deprecation for DLS settings
[%collapsible]
====
*Details* +
Two settings available in the latest versions of 7.17 are not available in the next major version.
Newer versions of 7.17 default to stricter Document Level Security (DLS) rules and the follow
settings can be used to disable those stricter DLS rules:
`xpack.security.dls.force_terms_aggs_to_exclude_deleted_docs.enabled` and
`xpack.security.dls.error_when_validate_query_with_rewrite.enabled`.
Newer versions, of next major version of Elasticsearch, also default to the stricter DLS rules but don't allow
usage of the less strict rules.

*Impact* +
To avoid deprecation warnings, remove these settings from elasticsearch.yml.
====

#### Mapping deprecations

.Camel case date formats are deprecated.
[%collapsible]
====
*Details* +
The use of camel case patterns on date formats is deprecated and will be removed
in Elasticsearch 8.0.0.

The corresponding snake case pattern should be used instead.

*Impact* +
To avoid deprecation warnings, discontinue use of the camel case pattern.
====
// end::notable-breaking-changes[]