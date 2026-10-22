#### Command line tool changes

TIP: {ess-skip-section}

.The `elasticsearch-migrate` tool has been removed.
[%collapsible]
====
*Details* +
The `elasticsearch-migrate` tool provided a way to convert file
realm users and roles into the native realm. It has been deprecated
since Elasticsearch 7.2.0. Users and roles should now be created in the native
realm directly.

*Impact* +
Discontinue use of the `elasticsearch-migrate` tool. Attempts to use the
`elasticsearch-migrate` tool will result in an error.
====