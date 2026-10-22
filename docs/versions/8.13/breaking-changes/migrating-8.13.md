**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 8.13

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.13.

See also [*What’s new in 8.17*](release-highlights.html) and [Release notes](es-release-notes.html).

Coming in 8.13.0.

### Breaking changes

There are no breaking changes in 8.13.

### Notable changes

The following are notable, non-breaking updates to be aware of:

* Changes to features that are in Technical Preview.

* Changes to log formats.

* Changes to non-public APIs.

* Behaviour changes that repair critical bugs.

#### Index setting changes

Change `index.look_ahead_time` index setting’s default value from 2 hours to 30 minutes.

**Details**

Lower the `index.look_ahead_time` index setting’s max value from 2 hours to 30 minutes.

**Impact**

Documents with @timestamp of 30 minutes or more in the future will be rejected. Before documents with @timestamp of 2 hours or more in the future were rejected. If the previous behaviour should be kept, then update the `index.look_ahead_time` setting to two hours before performing the upgrade.

Lower the `look_ahead_time` index setting’s max value

**Details**

Lower the `look_ahead_time` index setting’s max value from 7 days to 2 hours.

**Impact**

Any value between 2 hours and 7 days will be as a look ahead time  of 2 hours is defined

#### REST API changes

ESQL: Grammar - FROM METADATA no longer requires []

**Details**

Remove [ ] for METADATA option inside FROM command statements

**Impact**

Previously to return metadata fields, one had to use square brackets: (eg. *FROM index [METADATA _index]*). This is no longer needed: the [ ] are dropped and do not have to be specified, thus simplifying the command above to:'FROM index METADATA _index'.

ES|QL: remove PROJECT keyword from the grammar

**Details**

Removes the PROJECT keyword (an alias for KEEP) from ES|QL grammar

**Impact**

Before this change, users could use PROJECT as an alias for KEEP in ESQL queries, (eg. *FROM idx | PROJECT name, surname*) the parser replaced PROJECT with KEEP, emitted a warning: *PROJECT command is no longer supported, please use KEEP instead* and the query was executed normally. With this change, PROJECT command is no longer recognized by the query parser; queries using PROJECT command now return a parsing exception.

[ESQL] Remove is_nan, is_finite, and `is_infinite`

**Details**

Removes the functions `is_nan`, `is_finite`, and `is_infinite`.

**Impact**

Attempting to use the above functions will now be a planner time error.  These functions are no longer supported.

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.13
and will be removed in a future version.
While this won’t have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.13.

To find out if you are using any deprecated functionality,
enable [deprecation logging](logging.html#deprecation-logging).

#### Cluster and node setting deprecations

Deprecate `client.type`

**Details**

The node setting `client.type` has been ignored since the node client was removed in 8.0. The setting is now deprecated and will be removed in a future release.

**Impact**

Remove the `client.type` setting from `elasticsearch.yml`

#### REST API deprecations

`DesiredNode:` deprecate `node_version` field and make it optional for the current version

**Details**

The desired_node API includes a `node_version` field to perform validation on the new node version required. This kind of check is too broad, and it’s better done by external logic, so it has been removed, making the `node_version` field not necessary. The field will be removed in a later version.

**Impact**

Users should update their usages of `desired_node` to not include the `node_version` field anymore.