#### Logging changes

.Elasticsearch JSON logs now comply with ECS.
[%collapsible]
====
*Details* +
Elasticsearch's {ref}/logging.html[JSON logs] now comply with the
{ecs-ref}/index.html[Elastic Common Schema (ECS)]. Previously, Elasticsearch's JSON logs
used a custom schema.

*Impact* +
If your application parses Elasticsearch's JSON logs, update it to support the new ECS
format.
====

.Elasticsearch no longer emits deprecation logs or slow logs in plaintext.
[%collapsible]
====
*Details* +
Elasticsearch no longer emits a plaintext version of the following logs:

* Deprecation logs
* Indexing slow logs
* Search slow logs

These logs are now only available in JSON.

Server logs are still available in both a JSON and plaintext format.

*Impact* +
If your application parses Elasticsearch's plaintext logs, update it to use the new ECS
JSON logs.
====

.Audit logs are rolled-over and archived by size.
[%collapsible]
====
*Details* +
In addition to the existing daily rollover, the security audit logs are
now rolled-over by disk size limit as well. Moreover, the rolled-over logs
are also gzip compressed.

*Impact* +
The names of rolled over audit log files (but not the name of the current log)
have changed.
If you've set up automated tools to consume these files, you must configure them
to use the new names and to possibly account for `gzip` archives instead of
plain text. The Docker build of Elasticsearch is not affected because it logs on `stdout`,
where rollover is not performed.
====