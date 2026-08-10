# Multi-Index ES Mutation Simulator (Shell Script Version)

Phiên bản Shell Script (`.sh`) tương thích 100% với môi trường Jenkins CI/CD và Git Bash Linux operator runner.

## Các file Shell trong thư mục `sh/`
- `simulate_multi_index.sh`: Script chạy mô phỏng đột biến dữ liệu trên nhiều index.
- `verify_multi_index.sh`: Script chạy đối soát kiểm tra lại kết quả trên ES.

## Cách chạy

```bash
# 1. Chạy mô phỏng đột biến dữ liệu bằng Shell Script
bash scripts/simulate_multi_index/sh/simulate_multi_index.sh

# 2. Chạy kiểm tra đối soát bằng Shell Script
bash scripts/simulate_multi_index/sh/verify_multi_index.sh
```

## Biến môi trường Cấu hình
```bash
ES_URL=http://localhost:9200 \
ES_USER=elastic \
ES_PASS=secret \
SAMPLE_FILE=scripts/audit_delta_sync/configs/ \
bash scripts/simulate_multi_index/sh/simulate_multi_index.sh
```
