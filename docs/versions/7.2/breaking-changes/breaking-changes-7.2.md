**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 7.2

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.2.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

* [Discovery changes](breaking-changes-7.2.html#breaking_72_discovery_changes)

* [Index lifecycle management (ILM) deprecations](breaking-changes-7.2.html#breaking_72_ilm_deprecations)

* [Ingest pipeline changes](breaking-changes-7.2.html#breaking_72_ingest_changes)

### Discovery changes

#### Only a single port may be given for each seed host.

In earlier versions you could include a range of ports in entries in the
`discovery.seed_hosts` list, but Elasticsearch used only the first port in the range and
unexpectedly ignored the rest.  For instance if you set `discovery.seed_hosts:
"10.11.12.13:9300-9310"` then Elasticsearch would only use `10.11.12.13:9300` for
discovery. Seed host addresses containing port ranges are now rejected.

### Index lifecycle management (ILM) deprecations

#### An ILM poll interval of less than one second is deprecated.

Setting `indices.lifecycle.poll_interval` to less than one second (`1s`) is now
deprecated. If the `indices.lifecycle.poll_interval` cluster setting is too low,
it can cause excessive load on a cluster.

To avoid deprecation warnings, use a setting value of `1s` or greater.

### Ingest pipeline changes

#### The `user_agent` ingest processor’s `ecs` parameter is deprecated.

The `ecs` parameter for the `user_agent` ingest processor is deprecated and will
be removed in 8.0. In 8.x, the `user_agent` ingest processor will only return
[Elastic Common Schema (ECS)](/guide/en/ecs/1.12) fields.

To avoid deprecation warnings, remove the parameter from your ingest pipelines.