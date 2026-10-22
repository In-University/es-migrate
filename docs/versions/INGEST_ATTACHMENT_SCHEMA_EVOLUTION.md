# Ingest Attachment Processor: Schema Evolution & Strict Mapping Field Catalog

## Overview & Background

In Elasticsearch, the attachment processor (`ingest-attachment` plugin in ES 5.x–7.x, built-in module in ES 8.x–9.x, formerly `mapper-attachments` in ES 2.x) extracts content and metadata from binary attachments (PDF, DOCX, PPT, XLSX, images, etc.) using Apache Tika.

### Why Strict Dynamic Mapping Fails During Upgrades
When an Elasticsearch index is configured with `"dynamic": "strict"`, Elasticsearch will reject any document that introduces a field not explicitly declared in the index mapping:
```json
{
  "error": {
    "root_cause": [{
      "type": "strict_dynamic_mapping_exception",
      "reason": "mapping set to strict, dynamic introduction of [modified] is not allowed"
    }],
    "type": "strict_dynamic_mapping_exception",
    "reason": "mapping set to strict, dynamic introduction of [modified] is not allowed"
  },
  "status": 400
}
```

In **Elasticsearch 6.8 and all 7.x versions**, `AttachmentProcessor` extracted a fixed set of **8 properties**:
1. `content` (text)
2. `title` (text)
3. `author` (text)
4. `keywords` (text)
5. `date` (date)
6. `content_type` (text / keyword)
7. `content_length` (long)
8. `language` (keyword / text)

Starting in **Elasticsearch 8.0.0 and continuing through 9.2.3+**, Elastic upgraded Apache Tika and expanded `AttachmentProcessor.Property` enum to support **28 properties** (adding 20 new metadata fields).
By default, if an ingest pipeline does not specify the `"properties"` array in its configuration, **Elasticsearch extracts ALL 28 properties**. If an indexed document contains any metadata for these fields (such as `modified`, `format`, `creator_tool`, etc.), Elasticsearch attempts to write them into the target object. In a strict index mapping where only the legacy 8 fields were defined, **indexing immediately throws `strict_dynamic_mapping_exception` and fails**.

---

## Verbatim Java Enum: Property Comparison Across Versions

### ES 6.8 & 7.x (`plugins/ingest-attachment/.../AttachmentProcessor.java`)
```java
enum Property {
    CONTENT,
    TITLE,
    AUTHOR,
    KEYWORDS,
    DATE,
    CONTENT_TYPE,
    CONTENT_LENGTH,
    LANGUAGE;

    public static Property parse(String value) {
        return valueOf(value.toUpperCase(Locale.ROOT));
    }

    public String toLowerCase() {
        return this.toString().toLowerCase(Locale.ROOT);
    }
}
```

### ES 8.0 through ES 9.2.3+ (`modules/ingest-attachment/.../AttachmentProcessor.java`)
```java
enum Property {
    CONTENT,
    TITLE,
    AUTHOR,
    KEYWORDS,
    DATE,
    CONTENT_TYPE,
    CONTENT_LENGTH,
    LANGUAGE,
    MODIFIED,
    FORMAT,
    IDENTIFIER,
    CONTRIBUTOR,
    COVERAGE,
    MODIFIER,
    CREATOR_TOOL,
    PUBLISHER,
    RELATION,
    RIGHTS,
    SOURCE,
    TYPE,
    DESCRIPTION,
    PRINT_DATE,
    METADATA_DATE,
    LATITUDE,
    LONGITUDE,
    ALTITUDE,
    RATING,
    COMMENTS;

    public static Property parse(String value) {
        return valueOf(value.toUpperCase(Locale.ROOT));
    }

    public String toLowerCase() {
        return this.toString().toLowerCase(Locale.ROOT);
    }
}
```

---

## Complete Verbatim Property Catalog (All 28 Fields)

| # | Property Name | ES Mapping Type | Apache Tika Metadata Key | Introduced In | Description |
|---|---------------|-----------------|--------------------------|---------------|-------------|
| 1 | `content` | `text` | N/A (Extracted Text Body) | ES 5.0 (Legacy) | Extracted text content of the attachment. |
| 2 | `title` | `text` | `TikaCoreProperties.TITLE` | ES 5.0 (Legacy) | Document title. |
| 3 | `author` | `text` | `TikaCoreProperties.CREATOR` | ES 5.0 (Legacy) | Author / creator of the document. |
| 4 | `keywords` | `text` | `TikaCoreProperties.KEYWORDS` | ES 5.0 (Legacy) | Comma/space separated document keywords. |
| 5 | `date` | `date` | `TikaCoreProperties.CREATED` | ES 5.0 (Legacy) | Document creation date. |
| 6 | `content_type` | `keyword` / `text` | `HttpHeaders.CONTENT_TYPE` | ES 5.0 (Legacy) | MIME content type (e.g. `application/pdf`). |
| 7 | `content_length`| `long` | `HttpHeaders.CONTENT_LENGTH` | ES 5.0 (Legacy) | Size of attachment in bytes. |
| 8 | `language` | `keyword` | `TikaCoreProperties.LANGUAGE` | ES 5.0 (Legacy) | Detected language code (e.g. `en`, `de`). |
| 9 | `modified` | `date` | `TikaCoreProperties.MODIFIED` | **ES 8.0.0** | Document modification timestamp. |
| 10 | `format` | `keyword` / `text` | `TikaCoreProperties.FORMAT` | **ES 8.0.0** | Format identifier. |
| 11 | `identifier` | `keyword` / `text` | `TikaCoreProperties.IDENTIFIER` | **ES 8.0.0** | Resource identifier / URI / ISBN / UUID. |
| 12 | `contributor` | `text` | `TikaCoreProperties.CONTRIBUTOR` | **ES 8.0.0** | Contributors to the resource. |
| 13 | `coverage` | `text` | `TikaCoreProperties.COVERAGE` | **ES 8.0.0** | Spatial or temporal topic of the resource. |
| 14 | `modifier` | `text` | `TikaCoreProperties.MODIFIER` | **ES 8.0.0** | Name of user who last modified the document. |
| 15 | `creator_tool` | `keyword` / `text` | `TikaCoreProperties.CREATOR_TOOL` | **ES 8.0.0** | Tool used to create the document (e.g. `Word`, `LaTeX`). |
| 16 | `publisher` | `text` | `TikaCoreProperties.PUBLISHER` | **ES 8.0.0** | Entity responsible for making resource available. |
| 17 | `relation` | `keyword` / `text` | `TikaCoreProperties.RELATION` | **ES 8.0.0** | Related resources. |
| 18 | `rights` | `keyword` / `text` | `TikaCoreProperties.RIGHTS` | **ES 8.0.0** | Copyright and IP rights information. |
| 19 | `source` | `text` | `TikaCoreProperties.SOURCE` | **ES 8.0.0** | Reference to resource from which document is derived. |
| 20 | `type` | `keyword` / `text` | `TikaCoreProperties.TYPE` | **ES 8.0.0** | Nature or genre of resource. |
| 21 | `description` | `text` | `TikaCoreProperties.DESCRIPTION` | **ES 8.0.0** | Abstract or free-text account of resource. |
| 22 | `print_date` | `date` | `TikaCoreProperties.PRINT_DATE` | **ES 8.0.0** | Date the document was printed. |
| 23 | `metadata_date` | `date` | `TikaCoreProperties.METADATA_DATE` | **ES 8.0.0** | Date metadata was last updated. |
| 24 | `latitude` | `double` | `TikaCoreProperties.LATITUDE` | **ES 8.0.0** | Geographic latitude metadata (e.g. EXIF in images/PDFs). |
| 25 | `longitude` | `double` | `TikaCoreProperties.LONGITUDE` | **ES 8.0.0** | Geographic longitude metadata. |
| 26 | `altitude` | `double` | `TikaCoreProperties.ALTITUDE` | **ES 8.0.0** | Altitude metadata. |
| 27 | `rating` | `double` | `TikaCoreProperties.RATING` | **ES 8.0.0** | User rating metadata. |
| 28 | `comments` | `text` | `TikaCoreProperties.COMMENTS` | **ES 8.0.0** | User or system comments embedded in document. |

---

## Production Mitigation & Remediation Strategies

### Strategy A: Whitelist Legacy Properties in Ingest Pipeline (No Mapping Change Needed)
If you cannot alter strict index mappings, you MUST restrict the attachment processor to only extract legacy fields:
```json
PUT _ingest/pipeline/attachment_pipeline
{
  "description": "Extract attachment with legacy property whitelist to prevent strict dynamic mapping failure",
  "processors": [
    {
      "attachment": {
        "field": "data",
        "target_field": "attachment",
        "properties": [
          "content",
          "title",
          "author",
          "keywords",
          "date",
          "content_type",
          "content_length",
          "language"
        ]
      }
    }
  ]
}
```

### Strategy B: Complete Strict Index Mapping Definition (ES8 / ES9)
If using `dynamic: "strict"`, define all 28 potential attachment properties in the index mapping:
```json
PUT bench-es9
{
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "data": { "type": "binary" },
      "attachment": {
        "properties": {
          "content": { "type": "text" },
          "title": { "type": "text" },
          "author": { "type": "text" },
          "keywords": { "type": "text" },
          "date": { "type": "date" },
          "content_type": { "type": "keyword" },
          "content_length": { "type": "long" },
          "language": { "type": "keyword" },
          "modified": { "type": "date" },
          "format": { "type": "keyword" },
          "identifier": { "type": "keyword" },
          "contributor": { "type": "text" },
          "coverage": { "type": "text" },
          "modifier": { "type": "text" },
          "creator_tool": { "type": "keyword" },
          "publisher": { "type": "text" },
          "relation": { "type": "keyword" },
          "rights": { "type": "keyword" },
          "source": { "type": "text" },
          "type": { "type": "keyword" },
          "description": { "type": "text" },
          "print_date": { "type": "date" },
          "metadata_date": { "type": "date" },
          "latitude": { "type": "double" },
          "longitude": { "type": "double" },
          "altitude": { "type": "double" },
          "rating": { "type": "double" },
          "comments": { "type": "text" }
        }
      }
    }
  }
}
```
