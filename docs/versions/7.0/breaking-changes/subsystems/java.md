### Java API changes

//NOTE: The notable-breaking-changes tagged regions are re-used in the
//Installation and Upgrade Guide

//tag::notable-breaking-changes[]

// end::notable-breaking-changes[]

#### `isShardsAcked` deprecated in `6.2` has been removed

`isShardsAcked` has been replaced by `isShardsAcknowledged` in
`CreateIndexResponse`, `RolloverResponse` and
`CreateIndexClusterStateUpdateResponse`.

#### `prepareExecute` removed from the client api

The `prepareExecute` method which created a request builder has been
removed from the client api. Instead, construct a builder for the
appropriate request directly.

#### Some Aggregation classes have moved packages

* All classes present in `org.elasticsearch.search.aggregations.metrics.*` packages
were moved to a single `org.elasticsearch.search.aggregations.metrics` package.

* All classes present in `org.elasticsearch.search.aggregations.pipeline.*` packages
were moved to a single `org.elasticsearch.search.aggregations.pipeline` package.  In
addition, `org.elasticsearch.search.aggregations.pipeline.PipelineAggregationBuilders`
was moved to `org.elasticsearch.search.aggregations.PipelineAggregationBuilders`

#### `Retry.withBackoff` methods with `Settings` removed

The variants of `Retry.withBackoff` that included `Settings` have been removed
because `Settings` is no longer needed.

#### Deprecated method `Client#termVector` removed

The client method `termVector`, deprecated in 2.0, has been removed. The method
`termVectors` (plural) should be used instead.

#### Deprecated constructor `AbstractLifecycleComponent(Settings settings)` removed

The constructor `AbstractLifecycleComponent(Settings settings)`, deprecated in 6.7
has been removed. The parameterless constructor should be used instead.

#### Changes to Geometry classes

Geometry classes used to represent geo values in SQL have been moved from the
`org.elasticsearch.geo.geometry` package to the `org.elasticsearch.geometry`
package and the order of the constructor parameters has changed from `lat`, `lon`
to `lon`, `lat`.