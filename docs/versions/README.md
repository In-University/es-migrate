# Elasticsearch Official Documentation Archive: 6.8 through 9.2.3

This directory contains the complete, unedited, verbatim documentation and changelogs for Elasticsearch versions 6.8 through 9.2.3, directly crawled and parsed from official Elastic sources:
- Official GitHub repository: `elastic/elasticsearch` (Asciidoc, Markdown, YAML changelog bundles, and plugin/module source code)
- Official Elastic Guide: `elastic.co/guide` and `docs.elastic.co` (Rendered HTML and documentation)

## Directory Structure by Version

```
docs/versions/
├── 6.8/                     # Elasticsearch 6.8 series (6.8.0 to 6.8.23)
├── 7.0/ ... 7.17/           # All Elasticsearch 7.x minor releases (7.0 to 7.17)
├── 8.0/ ... 8.19/           # All Elasticsearch 8.x minor releases (8.0 to 8.19)
├── 9.0/                     # Elasticsearch 9.0 (including 9.0.0 through 9.0.8)
├── 9.1/                     # Elasticsearch 9.1 (including 9.1.0 through 9.1.10)
├── 9.2/                     # Elasticsearch 9.2 (including 9.2.0, 9.2.1, 9.2.2, 9.2.3)
├── INGEST_ATTACHMENT_SCHEMA_EVOLUTION.md  # Exhaustive 28-field property breakdown & strict mapping fix
├── DYNAMIC_MAPPING_AND_STRICT_GUIDE.md    # Mapping types, strict dynamic mapping, date format changes
└── README.md
```

## Within Each Version Directory
- `release-notes/`: Complete minor and patch release notes verbatim.
- `breaking-changes/`: All breaking changes, deprecation removals, and migration notices.
- `migration-guide/`: Official step-by-step upgrade instructions.
- `whats-new/`: Feature highlights and additions.
- `plugins-and-modules/`: Full documentation and changelogs for all plugins and modules, specifically including `ingest-attachment` documentation, source code, and exact property enum definitions.
- `mappings/`: Dynamic mapping, strict mapping behavior, type removal, and schema rules.
