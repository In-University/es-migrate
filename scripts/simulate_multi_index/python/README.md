# Python Core Multi-Index Elasticsearch Suite

Bộ công cụ Python Script (`simulate_multi_index.py`, `verify_multi_index.py`) dùng để mô phỏng dữ liệu (C/U/D), đối soát kiểm chứng đột biến dữ liệu chuyên sâu qua Elasticsearch REST API.

---

## 📁 Thư mục Script (`python/`)

- **`simulate_multi_index.py`**: Mô phỏng đột biến dữ liệu (+ Create, ~ Update, - Delete) trên nhiều index cùng lúc.
- **`verify_multi_index.py`**: Kiểm tra đối soát chi tiết field-by-field dựa trên file `report.json`.
- **`sample_templates.json`**: File mẫu chứa cấu hình payload cho các index.

---

## ⚙️ Biến Môi trường & Tham số Cấu hình

| Biến Môi trường | Mô tả | Mặc định |
| :--- | :--- | :--- |
| `ES_URL` | URL kết nối tới Elasticsearch cluster | `http://localhost:9200` (hỗ trợ `ES9_URL`, `ES6_URL`) |
| `ES_USER` | Username xác thực Basic Auth | `elastic` |
| `ES_PASS` / `ES_PW` | Password xác thực Basic Auth | `""` |
| `INDICES` | Danh sách index mục tiêu (phân cách bằng dấu phẩy) | Tự động đọc từ template |
| `SAMPLE_FILE` | Đường dẫn tới **File JSON** hoặc **Thư mục** chứa template | `sample_templates.json` |
| `REPORT_FILE` | Đường dẫn lưu báo cáo báo đột biến JSON | `report.json` |
| `MUTATE_PCT` | Tỷ lệ % số lượng document sẽ bị đột biến | `0.10` (10%) |
| `CREATE_RATIO` | Tỷ lệ Create trong tổng lượt đột biến | `0.30` (30%) |
| `UPDATE_RATIO` | Tỷ lệ Update trong tổng lượt đột biến | `0.60` (60%) |
| `DELETE_RATIO` | Tỷ lệ Delete trong tổng lượt đột biến | `0.10` (10%) |
| `TOTAL_MUTATIONS` | Cố định số lượng record đột biến/index (ghi đè `MUTATE_PCT`) | `""` (Tự động tính) |

---

## 🚀 Hướng dẫn Sử dụng Quick Start

### 1. Thực thi Mô phỏng Đột biến dữ liệu (Python)
```bash
python scripts/simulate_multi_index/python/simulate_multi_index.py
```

### 2. Thực thi Đối soát Kiểm tra Dữ liệu (Python)
```bash
python scripts/simulate_multi_index/python/verify_multi_index.py
```
