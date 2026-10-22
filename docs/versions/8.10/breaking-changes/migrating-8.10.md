**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 8.10

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.10.

See also [*What’s new in 8.17*](release-highlights.html) and [Release notes](es-release-notes.html).

### Breaking changes

The following changes in Elasticsearch 8.10 might affect your applications
and prevent them from operating normally.
Before upgrading to 8.10, review these changes and take the described steps
to mitigate the impact.

There are no notable breaking changes in Elasticsearch 8.10.
But there are some less critical breaking changes.

#### Cluster and node setting changes

Remove the unused executor builder for vector tile plugin

**Details**

The threadpool called `vectortile` is a left over from the original development of the vector tile search end point and it is used nowhere. It can still be a breaking change if it is configured on the elasticsearch yml file, for example by changing the threadpool size `thread_pool.vectortile.size=8`'

**Impact**

In the case the threadpool appears on the yaml file, Elasticsearch will not start until those lines are removed.

#### Java API changes

Change pre-configured and cached analyzer components to use IndexVersion instead of Version

**Details**

This PR changes the types used to obtain pre-configured components from Version to IndexVersion,
with corresponding changes to method names.

Prior to 8.10, there is a one-to-one mapping between node version and index version, with corresponding constants
in the IndexVersion class.
Starting in 8.10, IndexVersion is versioned independently of node version, and will be a simple incrementing number.
For more information on how to use IndexVersion and other version types, please see the contributing guide.

**Impact**

Analysis components now take IndexVersion instead of Version

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.10
and will be removed in a future version.
While this won’t have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.10.

To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Authorization deprecations

Mark `apm_user` for removal in a future major release

**Details**

The `apm_user` role has been deprecated and will be removed in a future major release. Users should migrate to `editor` and `viewer` roles

**Impact**

Users will have to migrate to `editor` and `viewer` roles