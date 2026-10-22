**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Migrating to 8.9

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.9.

See also [*What’s new in 8.17*](release-highlights.html) and [Release notes](es-release-notes.html).

### Breaking changes

The following changes in Elasticsearch 8.9 might affect your applications
and prevent them from operating normally.
Before upgrading to 8.9, review these changes and take the described steps
to mitigate the impact.

#### REST API changes

Switch TDigestState to use `HybridDigest` by default

**Details**

The default implementation for TDigest in percentile calculations switches to a new internal implementation offering superior performance (2x-10x speedup), at a very small accuracy penalty for very large sample populations.

**Impact**

This change leads to generating slightly different results in percentile calculations. If the highest possible accuracy is desired, or it’s crucial to produce exactly the same results as in previous versions, one can either set `execution_hint` to `high_accuracy` in the `tdigest` spec of a given percentile calculation, or set `search.aggs.tdigest_execution_hint` to `high_accuracy` in cluster settings to apply to all percentile queries.