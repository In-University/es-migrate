# Audit Configuration JSON Schema Reference

This reference documents the complete JSON configuration structure accepted by `audit_delta_sync.py`.

## Top-Level Array Element

Each JSON configuration file contains an array of route definition objects:

| Field Name | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `base_path` | string | Yes | Primary resource URI prefix (e.g. `/api/v1/billing/invoices`). |
| `es_index` | string | No | Target Elasticsearch index name. If omitted, derived from `base_path`. |
| `id_field` | string | No | Entity primary key field name in ES document (e.g. `invoice_id`, `user_id`, `id`). Default: `id`. |
| `headers` | object | No | Custom HTTP headers sent with every request (e.g. `Authorization`). |
| `cookies` | object | No | Custom HTTP cookies sent with every request. |
| `steps` | array | Yes | Ordered array of audit step definitions. |

---

## Step Definition Object

| Field Name | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | string | Yes | Step identifier (`CREATE`, `UPDATE`, `PATCH`, `DELETE`). |
| `method` | string | Yes | HTTP verb (`POST`, `PUT`, `PATCH`, `DELETE`). |
| `path` | string | Yes | Request path relative to backend URL. Supports `{id}` placeholder. |
| `payload` | object | No | JSON request body payload sent to REST API endpoint. |
| `es_check` | object | No | Key-value pairs expected to exist in Elasticsearch document `_source`. |

---

## Example Payload Schema

```json
[
  {
    "base_path": "/api/v1/billing/invoices",
    "es_index": "billing_invoices",
    "id_field": "invoice_id",
    "steps": [
      {
        "name": "CREATE",
        "method": "POST",
        "path": "/api/v1/billing/invoices",
        "payload": {
          "invoice_id": "INV-2026-001",
          "amount": 150.0,
          "status": "ACTIVE"
        },
        "es_check": {
          "status": "ACTIVE",
          "amount": 150.0
        }
      },
      {
        "name": "UPDATE",
        "method": "PUT",
        "path": "/api/v1/billing/invoices/{id}",
        "payload": {
          "amount": 300.0,
          "status": "ACTIVE"
        },
        "es_check": {
          "amount": 300.0
        }
      },
      {
        "name": "PATCH",
        "method": "PATCH",
        "path": "/api/v1/billing/invoices/{id}",
        "payload": {
          "status": "INACTIVE"
        },
        "es_check": {
          "status": "INACTIVE"
        }
      },
      {
        "name": "DELETE",
        "method": "DELETE",
        "path": "/api/v1/billing/invoices/{id}"
      }
    ]
  }
]
```
