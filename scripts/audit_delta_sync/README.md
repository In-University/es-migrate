# Mass-Scale REST API & Elasticsearch Delta Sync Auditor

Bo cong cu Elasticsearch Delta Sync Auditor dung de kiem thu tinh tuan thu Delta Sync va kiem tra du lieu document trong Elasticsearch cho cac he thong Doanh nghiep lon.

---

## Strict Elasticsearch Document Search Strategy (No Direct GET /_doc Fallback)

Auditor thuc hien kiem tra du lieu trong Elasticsearch DUY NHAT qua phuong thuc **Elasticsearch Search API** voi `bool.must` term query theo truong Primary Key (`id_field`):

- **Endpoint**: `POST <es_url>/<es_index>/_search`
- **Request Body**:
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "<id_field>": "<entity_id>"
          }
        }
      ]
    }
  }
}
```

*Ghi chu: Hoan toan KHONG su dung fallback `GET /<es_index>/_doc/<entity_id>`.*

---

## Direct File & Directory Configuration Support

Tham so `--config` ho tro ca 2 dinh dang:
1. Chi dinh truc tiep 1 file JSON duy nhat: `--config ./configs/billing/invoices.json`
2. Chi dinh thu muc (quet de quy tat ca file `*.json`): `--config ./configs`

Example:
```bash
python audit_delta_sync.py \
  --target-url https://api.staging.yourcompany.com \
  --es-url https://es.staging.yourcompany.com:9200 \
  --config ./configs/billing/invoices.json
```

---

## Config Priority Tiers

1. CLI Flags (`--es-pass`, `--es-user`, `--target-url`, `--config`, etc.)
2. Environment Variables (`ES_PASS`, `ES_USER`, `TARGET_URL`, `AUDIT_CONFIG_PATH`, etc.)
3. In-Code Defaults / Embedded URL Auth (`http://user:pass@host:port`)

| CLI Flag | Env Variable | Default |
| :--- | :--- | :--- |
| `--target-url` | `TARGET_URL` | `http://127.0.0.1:8899` |
| `--es-url` | `ES_URL` | `http://127.0.0.1:8899` |
| `--es-user` | `ES_USER` | `""` |
| `--es-pass` | `ES_PASS` | `""` |
| `--cookie` | `AUDIT_COOKIE` / `COOKIE` | `""` |
| `--config` | `AUDIT_CONFIG_PATH` / `CONFIG_PATH` | `configs` |
| `--workers` | `AUDIT_WORKERS` | `20` |
| `--auth-token` | `AUTH_TOKEN` | `""` |
