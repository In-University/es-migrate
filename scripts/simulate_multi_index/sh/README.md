# Pure Shell (Bash) Multi-Index Elasticsearch Suite

Bộ công cụ Pure Bash Shell Script (100% `bash`, `curl`, `jq`) dùng để mô phỏng dữ liệu (C/U/D), đối soát kiểm chứng đột biến, và clone index phục vụ quá trình nâng cấp Elasticsearch.

Các script trong thư mục này được tối ưu hóa cho môi trường Runner/CI-CD (như Jenkins, Linux Git Bash) không phụ thuộc vào Python.

---

## 📁 Thư mục Script (`sh/`)

- **`simulate_multi_index.sh`**: Mô phỏng tạo mới (+ Create), cập nhật (~ Update), và xóa (- Delete) dữ liệu trên nhiều index cùng lúc.
- **`verify_multi_index.sh`**: Tự động kiểm tra đối soát trực tiếp với Elasticsearch cluster dựa trên file `report.json`.
- **`clone_upgrade_indices.sh`**: Tự động tìm tất cả concrete index đang gắn Alias và clone sang index mới có đuôi `_upgrade` (Hỗ trợ Native ES7+/ES9 `_clone` và High-Performance ES6 fallback).

---

## ⚙️ Biến Môi trường & Tham số Cấu hình

Tất cả các script ưu tiên sử dụng biến môi trường:

| Biến Môi trường | Mô tả | Mặc định |
| :--- | :--- | :--- |
| `ES_URL` | URL kết nối tới Elasticsearch cluster | `http://localhost:9200` (hỗ trợ `ES9_URL`, `ES6_URL`) |
| `ES_USER` | Username xác thực Basic Auth | `elastic` |
| `ES_PASS` / `ES_PW` | Password xác thực Basic Auth | `""` |
| `INDICES` | Danh sách index mục tiêu (phân cách bằng dấu phẩy) | Tự động đọc từ template |
| `SAMPLE_FILE` | Đường dẫn tới **File JSON** hoặc **Thư mục** chứa template | `../sample_templates.json` |
| `REPORT_FILE` | Đường dẫn lưu báo cáo báo đột biến JSON | `report.json` |
| `MUTATE_PCT` | Tỷ lệ % số lượng document sẽ bị đột biến | `0.10` (10%) |
| `CREATE_RATIO` | Tỷ lệ Create trong tổng lượt đột biến | `0.30` (30%) |
| `UPDATE_RATIO` | Tỷ lệ Update trong tổng lượt đột biến | `0.60` (60%) |
| `DELETE_RATIO` | Tỷ lệ Delete trong tổng lượt đột biến | `0.10` (10%) |
| `TOTAL_MUTATIONS` | Cố định số lượng record đột biến/index (ghi đè `MUTATE_PCT`) | `""` (Tự động tính) |
| `SUFFIX` | Hậu tố cho script clone index | `_upgrade` |

---

## 🗂️ Khả năng Đọc File & Quét Thư mục (`SAMPLE_FILE`)

Script hỗ trợ linh hoạt cả file đơn lẻ lẫn quét toàn bộ thư mục:

1. **File Đơn lẻ**: `SAMPLE_FILE=sample_templates.json`
2. **Quét Thư mục (Folder Scanning)**: `SAMPLE_FILE=scripts/audit_delta_sync/configs/`
   *(Tự động tìm kiếm các file `.json` đệ quy và hợp nhất cả 2 cấu trúc JSON: dạng dict `{"index": {...}}` và dạng mảng `[{"es_index": "...", "create_payload": {...}}]`)*.

---

## 🏷️ Cú pháp Placeholder trong Template

Sử dụng các placeholder đơn giản, thân thiện với Shell:

- `{{SEQ}}` / `{{seq}}`: Số thứ tự tự tăng (ví dụ `101`).
- `{{ID}}` / `{{id}}`: Mã Document ID (`doc-101`).
- `{{TIMESTAMP}}` / `{{NOW}}`: ISO-8601 UTC Timestamp (`YYYY-MM-DDTHH:MM:SSZ`).

Mọi document khởi tạo đều tự động được gán timestamp `modified_at` nếu chưa có.

---

## 🚀 Hướng dẫn Sử dụng Quick Start

### 1. Thực thi Mô phỏng Đột biến dữ liệu (Pure Shell)
```bash
# Mô phỏng dữ liệu với template từ thư mục configs
SAMPLE_FILE=scripts/audit_delta_sync/configs/ MUTATE_PCT=0.15 bash scripts/simulate_multi_index/sh/simulate_multi_index.sh
```

### 2. Thực thi Đối soát Kiểm tra Dữ liệu (Pure Shell)
```bash
# Kiểm tra đối soát với ES cluster dựa theo report.json vừa tạo
REPORT_FILE=scripts/simulate_multi_index/sh/report.json bash scripts/simulate_multi_index/sh/verify_multi_index.sh
```

### 3. Clone Alias Concrete Index thêm đuôi `_upgrade`
```bash
# Clone toàn bộ index đang gắn alias sang <index>_upgrade
ES_URL=http://localhost:9200 ES_USER=elastic ES_PASS=secret bash scripts/simulate_multi_index/sh/clone_upgrade_indices.sh
```
