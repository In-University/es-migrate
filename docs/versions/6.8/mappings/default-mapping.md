### `_default_` mapping

deprecated[6.0.0,See [removal-of-types](#removal-of-types)]

The default mapping, which will be used as the base mapping for a new
mapping type, can be customised by adding a mapping type with the name
`_default_` to an index, either when
[creating the index](#indices-create-index) or later on with the
[PUT mapping](#indices-put-mapping) API.

The documentation for this feature has been removed as it no longer makes
sense in 6.x where there can be only a single type per index.