# Helm Backup Management & Image Synchronization

Tập hợp các script hỗ trợ vận hành, đồng bộ image và dọn dẹp các release/workload backup trong quá trình migration/upgrade.

---

## 1. `sync_backup_images.sh`

Script tự động duyệt danh sách cụm Kubernetes (Cluster contexts) qua vòng lặp `foreach`, xử lý độc lập từng cluster: quét các deployment backup, truy vấn deployment gốc tương ứng trong cùng cluster (hỗ trợ cùng namespace hoặc khác namespace như `default`/`user-workload`), chuẩn hóa tên container (hỗ trợ đuôi `-backup`, `-backup-uq`, `-uq-backup`, v.v.) và cập nhật image chính xác.

### Điểm nổi bật
- **Foreach tuần tự qua danh sách cụm**: Duyệt qua danh sách context (mặc định: `CLUSTERS=("kind-cluster-primary" "kind-cluster-backup")` hoặc truyền qua cờ `-c`), mỗi vòng lặp chỉ xét độc lập trong 1 cluster.
- **Tự động quét toàn bộ Namespace (`-A`)**: Mặc định scan tất cả namespace nếu không chỉ định `-n`.
- **Hỗ trợ mapping khác namespace (Ví dụ: `default` vs `user-workload`)**:
  - Nếu deployment backup nằm ở `user-workload`, script tự động tìm kiếm deployment gốc tương ứng trong namespace hiện tại trước, sau đó tìm trong namespace `default`, hoặc bất kỳ namespace nào trong cụm đó.
- **Hỗ trợ deployment trung gian (Ví dụ: `app-backup-uq-deployment` $\rightarrow$ `app-backup-deployment`)**:
  - Chuẩn hóa tên deployment backup để map chính xác với deployment gốc kể cả khi có thêm tag ở giữa.
- **Chuẩn hóa Container Name**: Tự động strip hậu tố `-backup`, `-backup-uq`, `-uq-backup` ở container phía backup để map với container phía original, nhưng khi `kubectl set image` luôn chỉ định chính xác tên container thực tế của backup deployment.
- **Không bao giờ set nhầm về deployment gốc**: Lệnh `kubectl set image` chỉ tác động lên deployment backup (`$NAME`), deployment gốc không bị sửa đổi.
- **Danh sách loại trừ an toàn**: Tự động bỏ qua các workload chứa `dlbiz`, `cmp`, `bff`.
- **An toàn với DRY-RUN mặc định**: Chỉ apply khi truyền cờ `--apply`.

### Cú pháp
```bash
./sync_backup_images.sh [OPTIONS]
```

### Các tùy chọn
| Option | Mô tả | Mặc định |
| :--- | :--- | :--- |
| `--apply` | Thực thi lệnh `kubectl set image` thực tế | `DRY-RUN` (chỉ hiển thị) |
| `-n`, `--namespace <ns>` | Chỉ quét trên 1 namespace cụ thể | Quét toàn bộ namespace (`-A`) |
| `-c`, `--clusters '<c1> <c2>'` | Danh sách context cluster cần duyệt tuần tự | `kind-cluster-primary kind-cluster-backup` |
| `-h`, `--help` | Hiển thị hướng dẫn sử dụng | |

### Ví dụ sử dụng
```bash
# 1. Chạy mô phỏng (DRY-RUN) quét qua danh sách cluster mặc định
./sync_backup_images.sh

# 2. Thực thi cập nhật image thực tế trên các cluster
./sync_backup_images.sh --apply

# 3. Chỉ quét trên một namespace cụ thể
./sync_backup_images.sh -n user-workload --apply

# 4. Chỉ định danh sách cụm tùy biến
./sync_backup_images.sh -c "gke_prod_cluster,gke_stg_cluster" --apply
```

---

## 2. `delete_backup_helms.sh`

Script quét và gỡ bỏ hàng loạt các Helm release chứa hậu tố `-backup`.

### Cú pháp
```bash
./delete_backup_helms.sh [-y|--yes] [-n <namespace>]
```
