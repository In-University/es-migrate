# Dynamic & Strict Index Mapping Evolution: ES 6.8 through 9.2.3

## 1. Mapping Type Removal (`_doc`)
- **ES 6.x**: Indices support a single type per index. Requests commonly specify the type (e.g. `bench-es6/_doc/1` or `bench-es6/doc/1`). Mappings are nested under `{"mappings": {"_doc": {"properties": {...}}}}`.
- **ES 7.x**: Mapping types are deprecated. `_doc` is retained solely as an endpoint path convention (`POST index/_doc`), but mapping types are removed from the schema (`{"mappings": {"properties": {...}}}`).
- **ES 8.x & ES 9.x**: Mapping types are completely eliminated. Any request specifying a type name other than `_doc` fails. Mappings must declare `properties` directly under `mappings`.

## 2. Dynamic Mapping Modes (`dynamic`)
The `dynamic` setting controls whether new fields can be added dynamically when encountered in indexed documents:
- `true`: (Default) Dynamically detect field type and add field to index mapping.
- `false`: Silently ignore new fields. New fields are stored in `_source` but not indexed or searchable.
- `strict`: Throw `strict_dynamic_mapping_exception` and reject document indexing if unknown fields appear.
- `runtime`: (Introduced in ES 7.11, default in some workloads in ES 8+) Dynamically create runtime fields instead of indexing new fields.

## 3. Date Parsing & Formats: Joda-Time vs Java Time (`java.time`)
- **ES 6.x**: Parsed using Joda-Time pattern formatters.
- **ES 7.0+**: Replaced Joda-Time with standard `java.time.format.DateTimeFormatter`.
- In standard migrations, default `strict_date_optional_time||epoch_millis` remains compatible, but custom pattern syntax with symbols like `y`, `Y`, `d`, `D` must be audited carefully.

## 4. Strict Mapping Checklist for Ingest Pipelines
When running ingest pipelines that enrich or extract documents:
1. Every processor output field (`target_field`) must be explicitly declared in index properties.
2. Ingest Attachment Processor: Extracts up to 28 fields in ES 8+/9+ compared to 8 fields in ES 6/7. Ensure mapping declares all 28 or set explicit `"properties": [...]` whitelist.
3. System metadata fields (`modified_at`, `cutover_at`, etc.): Ensure custom pipeline fields are mapped or stripped before indexing.
