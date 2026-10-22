### Mapping changes

//NOTE: The notable-breaking-changes tagged regions are re-used in the
//Installation and Upgrade Guide

//tag::notable-breaking-changes[]

// end::notable-breaking-changes[]

#### The `_all` metadata field is removed

The `_all` field deprecated in 6 have now been removed.

#### The `_uid` metadata field is removed

This field used to index a composite key formed of the `_type` and the `_id`.
Now that indices cannot have multiple types, this has been removed in favour
of `_id`.

//tag::notable-breaking-changes[]
#### The `_default_` mapping is no longer allowed

The `_default_` mapping has been deprecated in 6.0 and is now no longer allowed
in 7.0. Trying to configure a `_default_` mapping on 7.x indices will result in
an error.

If an index template contains a `_default_` mapping, it will fail to create new
indices. To resolve this issue, the `_default_` mapping should be removed from
the template. Note that in 7.x, the [get template API](#indices-get-template)
does not show the `_default_` mapping by default, even when it is defined in
the mapping. To see all mappings in the template, the `include_type_name`
parameter must be supplied:

```
GET /_template/my_template?include_type_name
```

For more details on the `include_type_name` parameter and other types-related
API changes, please see [removal-of-types](#removal-of-types).
//end::notable-breaking-changes[]

#### `index_options` for numeric fields has been removed

The `index_options` field for numeric  fields has been deprecated in 6 and has now been removed.

#### Limiting the number of `nested` json objects

To safeguard against out of memory errors, the number of nested json objects within a single
document across all fields has been limited to 10000. This default limit can be changed with
the index setting `index.mapping.nested_objects.limit`.

#### The `update_all_types` option has been removed

This option is useless now that all indices have at most one type.

#### The `classic` similarity has been removed

The `classic` similarity relied on coordination factors for scoring to be good
in presence of stopwords in the query. This feature has been removed from
Lucene, which means that the `classic` similarity now produces scores of lower
quality. It is advised to switch to `BM25` instead, which is widely accepted
as a better alternative.

#### Similarities fail when unsupported options are provided

An error will now be thrown when unknown configuration options are provided
to similarities. Such unknown parameters were ignored before.

#### Changed default `geo_shape` indexing strategy

`geo_shape` types now default to using a vector indexing approach based on Lucene's new
`LatLonShape` field type. This indexes shapes as a triangular mesh instead of decomposing
them into individual grid cells. To index using legacy prefix trees the `tree` parameter
must be explicitly set to one of `quadtree` or `geohash`. Note that these strategies are
now deprecated and will be removed in a future version.

IMPORTANT NOTE: If using timed index creation from templates, the `geo_shape` mapping
should also be changed in the template to explicitly define `tree` to one of `geohash`
or `quadtree`. This will ensure compatibility with previously created indexes.

#### Deprecated `geo_shape` parameters

The following type parameters are deprecated for the `geo_shape` field type: `tree`,
`precision`, `tree_levels`, `distance_error_pct`, `points_only`, and `strategy`. They
will be removed in a future version.

#### Limiting the number of completion contexts

The maximum allowed number of completion contexts in a mapping will be limited
to 10 in the next major version. Completion fields that define more than 10
contexts in a mapping will log a deprecation warning in this version.

#### `include_type_name` now defaults to `false`
The default for `include_type_name` is now `false` for all APIs that accept
the parameter.