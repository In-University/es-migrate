# ES6 vs ES9 index mapping — known differences

`scripts/mapping-es6.json` and `scripts/mapping-es9.json` describe the same
40-odd fields on `bench-es6` and `bench-es9`. The differences between them
are deliberate and version-driven, not drift — this doc is the place to
check before changing either file.

## 1. Mapping-type wrapper

- **ES6**: `mappings._doc.properties.*` — ES 6.x still supports (a single)
  mapping type per index, and this repo's mapping uses `_doc` as that type
  name.
- **ES9**: `mappings.properties.*` — mapping types were removed entirely in
  ES7+; there is no type level at all, just `properties` directly under
  `mappings`.

This is why the two JSON files nest one level differently even though the
field list underneath is identical. `reindex_remote.sh` and
`generate_es6.py` already account for this (ES6 requests go through the
`_doc` type where required, ES9 requests don't).

## 2. Date format: Joda-Time (ES6) vs java.time (ES9)

ES 6.x parses/formats `date` fields using **Joda-Time** pattern syntax; ES7+
switched to Java's **`java.time`** (`DateTimeFormatter`) syntax. The two
pattern languages mostly overlap but are not identical (e.g. some pattern
letters changed meaning or were dropped across the switch).

Every `date` field in both mappings (`created_at`, `updated_at`,
`published_at`) is declared as plain `"type": "date"` with no explicit
`format` — so both clusters fall back to the built-in default,
`strict_date_optional_time||epoch_millis`, which is stable and behaves
identically on both versions. This is called out explicitly, not because
there's a problem today, but because it stops being true the moment anyone
adds a custom `format` string to one of these fields without checking it
against both parsers first.

## 3. No document fields were added for the rollback path

Deliberately: the rollback delta sync does not depend on any mapping change.
`scripts/rollback_sync.sh` carries creates/updates across using the existing
`updated_at` field. Hard deletes on ES9 are handled by a separate mechanism —
`scripts/reconcile_deletes.sh` diffs the two indices' live `_id` sets and
deletes the difference from ES6 — that needs no document field at all (a
soft-delete flag like `is_deleted` was considered and rejected specifically
because adding a field wasn't an option; see
[ES9 → ES6 rollback design](superpowers/specs/2026-07-21-es9-es6-rollback-design.md)
for the full reasoning).

The one thing this feature *does* add is **index metadata**, not a document
field, and never written to ES6:

| Key | Purpose |
|---|---|
| `_meta.cutover_at` | ISO-8601 timestamp written by `scripts/reindex_remote.sh` right after a successful ES6 → ES9 reindex. The rollback delta sync reads it via `GET bench-es9/_mapping` as the lower bound for `updated_at`. |

## 4. What's identical

Every other field — `id`, `sku`, `title`, `description`, `category`,
`sub_category`, `brand`, `status`, `country_code`, `currency`, `tags`,
`price`, `discount`, `rating`, `views`, `stock`, `sold_count`, `weight_kg`,
`width_cm`, `height_cm`, `depth_cm`, `is_active`, `is_featured`, `in_stock`,
`client_ip`, `location`, `seller_id`, `seller_name`, `warehouse_code`,
`supplier_id`, `barcode`, `color`, `size`, `material`, `rank`, `score`,
`reviews.*` — has the same type on both clusters. `number_of_shards`,
`number_of_replicas`, and `refresh_interval` in `settings` also match.
