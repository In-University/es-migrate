**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 6.5

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 6.5.

* [Logging changes](breaking-changes-6.5.html#breaking_65_logging_changes)

* [Search changes](breaking-changes-6.5.html#breaking_65_search_changes)

* [SQL plugin changes](breaking-changes-6.5.html#breaking_65_sql_changes)

* [Client changes](breaking-changes-6.5.html#breaking_65_client_changes)

* [Security changes](breaking-changes-6.5.html#breaking_65_security_changes)

See also [Release Highlights](release-highlights.html) and [Release Notes](es-release-notes.html).

### Logging changes

#### %node_name in logging pattern

To make the node name appear consistently in Elasticsearch’s logs and to clean
up much of the internal logging code we’ve removed the node name from the
"marker" in the logging configuration. If you do not customize your logging
configuration file then there is nothing for you to do. If you **do** customize
your logging configuration properties then you should replace `%marker` with
`[%node_name]%marker `, including the trailing space. If you do not do so
Elasticsearch will log a warning on startup and log with the new pattern. It
will not change the logging configuration files though. You should make this
change before 7.0 because in 7.0 Elasticsearch will no longer automatically
add the node name to the logging configuration if it isn’t already present.

### Search changes

#### Scroll

Using `rescore` with a scroll query now raises a deprecation warning and
ignores the parameter.  In earlier 6.x releases, rescore on scroll queries was
silently ignored.  In 7.0 and later, we will return a `400 - Bad Request` with
a validation error.

### SQL plugin changes

#### Grouping by columns with missing values will create an additional group

An additional group will be present in the result of requests containing a
`GROUP BY` for a column that has missing values in the returned documents.
The records with missing values in the grouped by column will be collectively
considered a single bucket.

### Client changes

#### Deprecate Retry.withBackoff methods that take Settings

`Settings` is no longer required by `Retry` so the `withBackoff` methods that
take `Settings` are now deprecated and there are new versions of those methods
that do not require `Settings`.

### Security changes

#### Custom role providers interface change

Custom role providers previously accepted an `ActionListener` with a response
type of `Set<RoleDescriptor>`, but in 6.5.0 the role provider requires an
`ActionListener` with a response type of `RoleRetrievalResult`. The
`RoleRetrievalResult` object accepts a `Set<RoleDescriptor>` if the provider
was successful; if the provider was not successful the `RoleRetrievalResult`
should be populated with the error.

### Settings changes

#### Audit logfile local node info

In 6.5.0 a new format for the logfile auditing has been introduced.
The new file format prints audit entries as JSON documents.
Entries in the previous format contained positional fields.
These fields are no longer positional in the new format, as they are part of the
structured log entry (the JSON document).
Consequently, the following settings, which toggled some of the prefix
positional fields, have been renamed ("prefix" was spliced out):

* `xpack.security.audit.logfile.prefix.emit_node_host_address` to
`xpack.security.audit.logfile.emit_node_host_address`

* `xpack.security.audit.logfile.prefix.emit_node_host_name` to
`xpack.security.audit.logfile.emit_node_host_name`

* `xpack.security.audit.logfile.prefix.emit_node_name` to
`xpack.security.audit.logfile.emit_node_name`

In 7.0.0 the `prefix` variant will be removed.