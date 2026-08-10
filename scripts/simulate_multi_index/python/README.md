# Multi-Index Elasticsearch Mutation Simulator & Verification Tool

Mô phỏng dữ liệu biến động post-cutover trực tiếp vào Elasticsearch trên **nhiều index** (dựa trên `simulate_es9_mutations.py`) và tự động đối soát verify nội dung từng record dựa trên file `report.json`.

## Cấu trúc Thư mục
```
scripts/simulate_multi_index/
├── sample_templates.json   # Template mẫu document (hoặc trỏ tới thư mục chứa các file .json)
├── simulate_multi_index.py # Script chạy mô phỏng đột biến dữ liệu vào ES
├── verify_multi_index.py   # Script lấy sample record đối soát chi tiết với ES
├── report.json             # File báo cáo đơn giản (kèm sample record payloads)
└── README.md
```

## Tính năng đọc File hoặc Thư mục chứa JSON Templates (`SAMPLE_FILE`)
Biến môi trường `SAMPLE_FILE` hỗ trợ 2 dạng:
1. **Đường dẫn tới 1 file JSON đơn lẻ** (Ví dụ: `SAMPLE_FILE=scripts/simulate_multi_index/sample_templates.json`).
2. **Đường dẫn tới 1 thư mục chứa nhiều file JSON** (Ví dụ: `SAMPLE_FILE=scripts/audit_delta_sync/configs/`). Script sẽ tự động quét đệ quy (recursive scan) toàn bộ các file `.json` trong thư mục và tự động phát hiện danh sách các index!

---

## Biến môi trường Cấu hình
| Biến Môi Trường | Biến dự phòng | Giá trị Mặc định | Mô tả |
|---|---|---|---|
| `ES_URL` | - | `http://localhost:9200` | URL của Elasticsearch target |
| `ES_USER` | - | `elastic` | Basic Auth Username |
| `ES_PASS` | `ES_PW` | `""` | Basic Auth Password |
| `INDICES` | `INDEX` | Tự động đọc từ template nếu rỗng | Danh sách Index (phân cách dấu phẩy) |
| `SAMPLE_FILE` | - | `sample_templates.json` | File `.json` hoặc **Thư mục** chứa các file `.json` |
| `REPORT_FILE` | - | `report.json` | Đường dẫn file báo cáo |

---

## Cách chạy

### 1. Trỏ vào 1 File Template cụ thể
```bash
SAMPLE_FILE=scripts/simulate_multi_index/sample_templates.json python scripts/simulate_multi_index/simulate_multi_index.py
```

### 2. Trỏ vào Thư mục chứa nhiều JSON Configs (Tự quét toàn bộ index)
```bash
SAMPLE_FILE=scripts/audit_delta_sync/configs/ python scripts/simulate_multi_index/simulate_multi_index.py
```

### 3. Đổi soát kết quả
```bash
python scripts/simulate_multi_index/verify_multi_index.py
```
