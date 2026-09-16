# Python Core Multi-Index Elasticsearch Suite

Bộ công cụ Python Script (`simulate_multi_index.py`, `verify_multi_index.py`) dùng để mô phỏng dữ liệu (C/U/D), đối soát kiểm chứng đột biến dữ liệu chuyên sâu qua Elasticsearch REST API.

---

## 📁 Thư mục Script (`python/`)

- **`generate_configs.py`**: Tự động quét toàn bộ alias -> concrete indices từ Elasticsearch cluster, lấy mẫu 1 document ngẫu nhiên từ mỗi index và sinh file cấu hình `configs/<index>.json` chuẩn (đảm bảo luôn có `"upgrade_modified_at": "{{timestamp}}"` trong cả `create` và `update`).
- **`simulate_multi_index.py`**: Mô phỏng đột biến dữ liệu (+ Create, ~ Update, - Delete) trên nhiều index. Tự động đọc cấu hình từng index từ thư mục `configs/`. Bắt buộc mỗi index phải có file cấu hình riêng (không dùng fallback, không dùng default template).
- **`verify_multi_index.py`**: Kiểm tra đối soát chi tiết field-by-field, kiểm tra tính toàn vẹn của body tài liệu dựa trên file `report.ndjson`. Sử dụng Elasticsearch `_mget` bulk API để verify tốc độ cao ngay cả với lượng dữ liệu cực lớn.
- **`configs/`**: Thư mục chứa các file JSON cấu hình template cho từng index (ví dụ: `bench-es9.json`, `ecommerce_products.json`, `ecommerce_orders.json`).

---

## ⚙️ Biến Môi trường & Tham số Cấu hình

| Biến Môi trường | Mô tả | Mặc định |
| :--- | :--- | :--- |
| `ES_URL` | URL kết nối tới Elasticsearch cluster | `http://localhost:9200` |
| `ES_USER` | Username xác thực Basic Auth | `elastic` |
| `ES_PASS` | Password xác thực Basic Auth | `""` |
| `INDICES` | Danh sách index mục tiêu (phân cách bằng dấu phẩy) | Tự động lấy tất cả index có file cấu hình |
| `CONFIG_DIR` | Thư mục chứa file cấu hình của các index (hỗ trợ `--config-dir`) | `configs/` |
| `REPORT_FILE` | Đường dẫn lưu báo cáo đột biến NDJSON streaming | `report.ndjson` |
| `VERIFY_LIMIT` | Giới hạn số record verify mỗi index (`0` = kiểm tra toàn bộ) | `0` (Kiểm tra tất cả) |
| `MUTATE_PCT` | Tỷ lệ % số lượng document sẽ bị đột biến | `0.10` (10%) |
| `CREATE_RATIO` | Tỷ lệ Create trong tổng lượt đột biến | `0.50` (50%) |
| `DELETE_RATIO` | Tỷ lệ Delete trong tổng lượt đột biến | `0.20` (20%) |
| `TOTAL_MUTATIONS` | Cố định số lượng record đột biến/index (ghi đè `MUTATE_PCT`) | `"auto"` |

---

## 🚀 Hướng dẫn Sử dụng Quick Start

### 1. Tự động sinh file cấu hình mẫu từ Cluster
```bash
python scripts/simulate_multi_index/python/generate_configs.py
```

### 2. Thực thi Mô phỏng Đột biến dữ liệu (Python)
```bash
python scripts/simulate_multi_index/python/simulate_multi_index.py
```

### 3. Thực thi Đối soát Kiểm tra Dữ liệu (Python)
```bash
python scripts/simulate_multi_index/python/verify_multi_index.py
```
