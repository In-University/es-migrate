## Migrating to 8.5

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.5.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

### Breaking changes

The following changes in Elasticsearch 8.5 might affect your applications and prevent
them from operating normally. Before upgrading to 8.5, review these changes and
take the described steps to mitigate the impact.

#### REST API changes

.The bulk API now rejects requests containing unrecognized actions
[%collapsible]
====
*Details* +
Requests to the bulk API comprise a sequence of items, each of which starts with
a JSON object describing the item. This object includes the type of action to
perform with the item which should be one of `create`, `update`, `index`, or
`delete`. Earlier versions of Elasticsearch had a bug that caused them to ignore items
with an unrecognized type, skipping the next line in the request, but this
lenient behaviour meant that there is no way for the client to associate the
items in the response with the items in the request, and in some cases it would
cause the remainder of the request to be parsed incorrectly.

From version 8.5 onwards, requests to the bulk API must comprise only items
with recognized types. Elasticsearch will reject requests containing any items with an
unrecognized type with a `400 Bad Request` error response.

We consider this change to be a bugfix but list it here as a breaking change
since it may affect the behaviour of applications which rely on being able to
send unrecognized actions to Elasticsearch.

*Impact* +
Ensure your application only sends items with type `create`, `update`, `index`
or `delete` to the bulk API.
====

### Deprecations

The following functionality has been deprecated in Elasticsearch 8.5
and will be removed in a future version.
While this won't have an immediate impact on your applications,
we strongly encourage you to take the described steps to update your code
after upgrading to 8.5.

To find out if you are using any deprecated functionality,
enable [deprecation logging](#deprecation-logging).

#### Plugin API deprecations

Plugins that extend the NetworkPlugin interface are deprecated.
[%collapsible]
====
*Details* +
Plugins may override funcionality that controls how nodes connect
with other nodes over TCP/IP. These plugins extend the NetworkPlugin
interface. In the next major release, these plugins will fail
to install.

*Impact* +
Discontinue using any plugins which extend NetworkPlugin. You can
see if any plugins use deprecated functionality by checking
the Elasticsearch deprecation log.
====

.Extending DiscoveryPlugin to override join validators or election strategies is deprecated
[%collapsible]
====
*Details* +
Plugins that extend DiscoveryPlugin may override getJoinValidator and
getElectionStrategies. These methods are implementation details of the
clustering mechanism within Elasticsearch. They should not be overriden.
In the next major release, plugins overriding getJoinValidator or
getElectionStrategies will fail to install.

*Impact* +
Discontinue using any plugins that override getJoinValidator or
getElectionStrategies in DiscoveryPlugin. You can see if any plugins
use deprecated functionality by checking the Elasticsearch deprecation log.
====