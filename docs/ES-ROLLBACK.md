# `es_rollback` — mang dữ liệu từ ES9 về ES6

Công cụ rollback blue-green: sau một thời gian dài (ví dụ 14 ngày) ES9 nhận
toàn bộ traffic đọc/ghi, nếu cần quay về ES6 thì ES6 đang thiếu mọi thứ đã
tạo/sửa/xoá trên ES9 kể từ lúc cutover. Công cụ này bù phần chênh đó.

Không snapshot, không đổi mapping, không thêm field nào vào document. Chỉ
dựa vào `updated_at` sẵn có và `_id`.

---

## Mục lục

1. [Yêu cầu](#1-yêu-cầu)
2. [Ý tưởng cốt lõi: vì sao phải chia pha](#2-ý-tưởng-cốt-lõi-vì-sao-phải-chia-pha)
3. [Checklist trước khi chạy](#3-checklist-trước-khi-chạy)
4. [Chạy — từng bước](#4-chạy--từng-bước)
5. [Bên trong từng pha](#5-bên-trong-từng-pha)
6. [Resume](#6-resume)
7. [Undo](#7-undo)
8. [Tinh chỉnh và bộ nhớ](#8-tinh-chỉnh-và-bộ-nhớ)
9. [Bảng biến môi trường](#9-bảng-biến-môi-trường)
10. [Xử lý sự cố](#10-xử-lý-sự-cố)
11. [Các cơ chế an toàn](#11-các-cơ-chế-an-toàn)
12. [Nội dung STATE_DIR](#12-nội-dung-state_dir)
13. [Những gì công cụ không làm](#13-những-gì-công-cụ-không-làm)
14. [Test](#14-test)

---

## 1. Yêu cầu

Một file bash duy nhất: `scripts/es_rollback.sh`.

| | |
|---|---|
| Phụ thuộc | `curl`, `jq`, `awk`, `sort`, `comm`, `gzip`, `split` |
| Cần cài thêm | **`jq`** — `apt-get install -y jq` |

Tất cả trừ `jq` đều có sẵn trên Ubuntu base. `jq` là thứ duy nhất phải cài.

`python3` chỉ cần cho bộ test (§14), không cần khi chạy thật.

---

## 2. Ý tưởng cốt lõi: vì sao phải chia pha

Chỉ có **một** điều thực sự cần hiểu.

Có hai loại thay đổi cần mang về ES6:

- **Tạo/sửa** — tìm được bằng query `updated_at > cutover_at`.
- **Xoá** — *không* tìm được bằng query. Một document bị xoá cứng trên ES9
  không để lại dấu vết. Cách duy nhất là so trực tiếp tập `_id` còn sống của
  hai bên: ID nào có ở ES6 mà không có ở ES9 nghĩa là đã bị xoá.

Phép so tập ID đó **chỉ đúng nếu delta sync đã chạy xong hoàn toàn**.

Nếu delta sync đứt giữa chừng và ES6 còn thiếu 50.000 document, phép so sẽ
thấy 50.000 ID "có ở ES9 mà không có ở ES6". Nếu chiều ngược lại bị hiểu
sai, một lần sync lỗi biến thành **xoá nhầm dữ liệu**. Đó là lý do có
`DELTA_GATE`: một cổng chặn cứng, không qua được thì tuyệt đối không có lệnh
xoá nào chạy.

```
0 PREFLIGHT   kiểm tra kết nối, index, ES6 ghi được, marker cutover,
              và xác minh ES9 thật sự đã dừng ghi
      |
1 DELTA_SYNC  ES9 (updated_at > cutover) -> ES6
              phân trang bằng PIT, checkpoint từng page, journal pre-image
      |
2 DELTA_GATE  <-- CỔNG CHẶN: con trỏ đã cạn? đã đọc đủ số doc? dead-letter rỗng?
      |           Sai một điều -> dừng, KHÔNG sang pha 3
      |
3 RECONCILE   export toàn bộ _id hai bên -> sắp xếp -> so sánh
              ES6-only  -> xoá khỏi ES6 (journal pre-image trước)
              ES9-only  -> vá ngược vào ES6
      |
4 VERIFY      so count, so tập ID kỳ vọng, so nội dung N doc ngẫu nhiên
```

---

## 3. Checklist trước khi chạy

**a. Dừng write vào ES9.** Bắt buộc. Toàn bộ lập luận đúng đắn ở trên dựa
vào việc nguồn đứng yên: cửa sổ delta đã đóng, và pha 3 so sánh hai tập
tĩnh. Công cụ tự kiểm tra và sẽ từ chối chạy nếu phát hiện ES9 còn động.

**b. Marker cutover.** `reindex_remote.sh` đã ghi `_meta.cutover_at` lên
`bench-es9`. Kiểm tra:
```bash
curl -s -u elastic:$ELASTIC_PW "$ES9_URL/bench-es9/_mapping" | grep cutover_at
```
Không có thì phải truyền `SINCE=<ISO-8601>` thủ công.

**c. Chỗ để `STATE_DIR`.** Journal có thể tới ~1,5 GB với 8M doc. Boot disk
của VM ES chỉ 30 GB và đã chứa OS + Docker + dữ liệu ES — **đừng đặt ở đó**.

**d. ES6 ghi được.** Sau hai tuần nhàn rỗi ES6 có thể đã chạm ngưỡng disk
watermark và tự khoá. Preflight sẽ báo, nhưng kiểm tra trước cho nhanh:
```bash
curl -s -u elastic:$ELASTIC_PW "$ES6_URL/bench-es6/_settings" | grep -o 'read_only[^,]*'
```

**e. `updated_at` được bump mọi lần ghi.** Nếu có ngoại lệ với *create*,
pha 3 vá được. Với *update* thì không phát hiện được — xem §13.

---

## 4. Chạy — từng bước

### Bước 0 — đặt biến môi trường

```bash
export ES6_URL=http://10.146.0.10:9200
export ES9_URL=http://10.146.0.11:9200
export ELASTIC_PW='...'
export STATE_DIR=/data/rollback
```

Tất cả các lệnh sau đều dùng chung bộ biến này.

### Bước 1 — `preflight`: kiểm tra, không ghi gì

```bash
./scripts/es_rollback.sh preflight
```

Mất khoảng 30 giây (phần lớn là `FREEZE_WAIT` chờ giữa hai mẫu). Kết quả
mong đợi:

```
== phase 0: preflight ==
   ES9 and ES6 reachable, both indices present
   bench-es6 is writable
   cutover_at=2026-07-10T00:00:00Z
   effective lower bound (-300s): 2026-07-09T23:55:00Z
   freeze sample 1: count=8000123 max(updated_at)=... -- waiting 30s
   freeze verified: ES9 static over 30s
preflight OK
```

**Dừng lại nếu**: thấy `still taking writes` (còn writer vào ES9),
`write-blocked` (ES6 tự khoá), hoặc `cutover_at missing`. Xử lý theo §10 rồi
chạy lại. Bước này chưa ghi gì nên chạy lại bao nhiêu lần cũng được.

### Bước 2 — `plan`: xem quy mô

```bash
./scripts/es_rollback.sh plan
```

```
plan (nothing written)
  ES9 bench-es9 total      : 8000123
  ES6 bench-es6 total      : 8000000
  delta since 2026-07-09T23:55:00Z : 412873 doc(s) to copy
  net count difference      : 123
  journal (approx, gzip)    : 74 MiB
```

Đọc kỹ ba số này trước khi đi tiếp:

- **`delta ... doc(s) to copy`** — khối lượng pha 1. Nhân với ~1 KB để ước
  băng thông, chia cho ~10–20k doc/s để ước thời gian.
- **`net count difference`** — chênh lệch *tổng*, không phải số xoá. Bằng
  (số tạo − số xoá). Bằng 0 **không** có nghĩa là không có gì để xoá.
- **`journal`** — dung lượng đĩa cần ở `STATE_DIR`. Kiểm tra `df` trước.

### Bước 3 — `run`: chạy thật

```bash
./scripts/es_rollback.sh run
```

Chạy liền mạch pha 1 → 2 → 3 → 4. Với 8M doc và delta lớn, việc này mất
hàng giờ; nên chạy trong `tmux`/`screen`. Tiến độ in ra theo từng page:

```
== phase 1: delta sync bench-es9 -> bench-es6 ==
   opened PIT
   delta window contains 412873 doc(s)
   page: 5000 docs (seen=5000 synced=5000 deadletter=0)
   ...
   delta sync finished: seen=412873 synced=412873 deadletter=0
== phase 2: delta gate ==
   gate passed: seen=412873 >= total=412873, deadletter=0
== phase 3: reconcile deletes ==
   exporting live ids from ES9/bench-es9
   exporting live ids from ES6/bench-es6
   id sets complete: ES9=8000123 ES6=8000412
   to delete from ES6: 289    to repair into ES6: 0
   deleting 289 doc(s) from ES6 (journaling pre-images first)
   reconcile done: deleted=289 repaired=0
== phase 4: verify ==
   counts: bench-es9=8000123 bench-es6=8000123
   expected ES6 id set matches ES9 exactly
   content sample: 1000 doc(s) identical
   VERIFY PASSED -- ES6 matches ES9; safe to flip traffic back
```

Mã thoát quyết định bước tiếp theo:

| Mã | Nghĩa | Làm gì |
|---|---|---|
| `0` | Xong, verify pass | Sang bước 4 |
| `1` | Lỗi dừng hẳn | §10, xử lý rồi `resume` |
| `2` | Xong nhưng có dead-letter | Đọc `deadletter.ndjson`, **chưa flip** |
| `130` | Bị Ctrl-C | `resume` |

Nếu bị chặn ở guard xoá (`more than 0.10 of ES6`), xem §10 — đó là chặn có
chủ đích, không phải lỗi.

### Bước 4 — kiểm tra lại bằng tay trước khi flip

Đừng chỉ tin log. Đối chiếu độc lập:

```bash
curl -s -u elastic:$ELASTIC_PW "$ES9_URL/bench-es9/_count"
curl -s -u elastic:$ELASTIC_PW "$ES6_URL/bench-es6/_count"
./scripts/es_rollback.sh status        # phải là phase: DONE
```

Và tự lấy vài document nghiệp vụ quan trọng ra so bằng mắt.

### Bước 5 — flip traffic về ES6

**Đây là điểm không quay lại.** Trước bước này, `undo` khôi phục ES6 chính
xác và bạn luôn có thể ở lại ES9. Sau bước này, ES6 bắt đầu nhận write mới
và `undo` sẽ ghi đè lên chúng — xem §7.

Chỉ flip khi `phase: DONE` và verify đã pass.

### Bước 6 — mở lại write, rồi dọn

```bash
./scripts/es_rollback.sh reset
```

`reset` trả `refresh_interval` của ES6 về giá trị gốc và xoá state. Nó **cố
ý giữ lại journal** và chỉ cảnh báo — xoá tay khi bạn chắc chắn không cần
`undo` nữa:

```bash
rm /data/rollback/journal.tsv.gz
```

---

## 5. Bên trong từng pha

### Pha 0 — PREFLIGHT

Sáu kiểm tra, tất cả đều là điều kiện cần cho tính đúng đắn:

1. Công cụ cần thiết có mặt.
2. ES6/ES9 kết nối và xác thực được, cả hai index tồn tại.
3. ES6 không bị khoá ghi (`read_only`, `read_only_allow_delete`, `write`).
4. `_meta.cutover_at` đọc được và parse được, không nằm ở tương lai.
5. Tính mốc dưới thực tế = `cutover_at − SAFETY_MARGIN`.
6. **Xác minh freeze**: lấy `_count` và `max(updated_at)` hai lần cách nhau
   `FREEZE_WAIT` giây; khác nhau là dừng.

Về (5): `cutover_at` do `date -u` trên VM ES9 ghi, còn `updated_at` trong
document do **application** ghi. Hai đồng hồ khác nhau. Nếu đồng hồ app chậm
hơn, document ghi ngay sau cutover mang timestamp *trước* marker và bị query
bỏ sót — âm thầm. Lùi mốc lại 300 giây khiến một số document được đồng bộ
thừa, hoàn toàn vô hại vì nguồn đứng yên và mỗi lần ghi là thay thế nguyên
document. Ghi thừa rẻ, bỏ sót thì mất dữ liệu.

### Pha 1 — DELTA_SYNC

Vòng lặp, mỗi page làm đúng thứ tự này và **thứ tự là bất biến**:

```
search ES9 (PIT + search_after)
  -> _mget pre-image từ ES6      (theo lô MGET_BATCH)
  -> ghi journal
  -> bulk vào ES6                (chia thành chunk ≤ 5 MB, tuần tự)
  -> cập nhật bộ đếm vào state
  -> đẩy con trỏ search_after
```

Phân trang bằng **PIT + sort `[updated_at asc, _shard_doc asc]`**. PIT cho
snapshot nhất quán; `_shard_doc` là tiebreaker nên nhiều document cùng một
`updated_at` vẫn phân trang chính xác. (`search_after` trên `_doc` mà không
có PIT thì thứ tự đổi khi segment merge, làm sót hoặc lặp document.)

**Con trỏ được đẩy sau cùng**, sau khi bulk đã xong và bộ đếm đã ghi. Chết
giữa chừng thì `resume` làm lại cả page — vô hại vì nguồn đứng yên và ghi là
thay thế nguyên document. Đẩy con trỏ sớm hơn thì một lần chết đúng lúc sẽ
khiến cả page bị nhảy qua.

### Pha 2 — DELTA_GATE

Chỉ qua khi **cả hai** đúng:

- `seen >= total` — đã đọc đủ số document mà cửa sổ delta báo có.
  (`seen` có thể *lớn hơn* `total` khi PIT hết hạn buộc quét lại phần chồng
  lấn; đó là đọc lại, không phải việc mới. Nhưng không bao giờ được thiếu.)
- `deadletter == 0` — không document nào bị ES6 từ chối.

Không qua thì dừng hẳn. `ALLOW_PARTIAL=true` bỏ qua điều kiện thứ hai, và
khi đó công cụ cảnh báo rõ ràng.

### Pha 3 — RECONCILE

1. Refresh cả hai bên. **Bắt buộc** — `bench-es6` có `refresh_interval: -1`,
   không refresh thì mọi thứ ghi ở pha 1 vô hình với bước export dưới đây.
2. Export toàn bộ `_id` còn sống. ES9 dùng **PIT**; ES6 6.8 không có PIT nên
   dùng **scroll**. Cả hai đều cho snapshot nhất quán.
3. **Guard đầy đủ**: số ID export được phải khớp **chính xác** `_count` mỗi
   bên. Không khớp là dừng. Thiếu guard này, một lần export ES9 bị đứt mạng
   trông y hệt "ES9 không còn những document đó" — và sẽ xoá gần hết ES6.
4. Sắp xếp, so hai chiều:
   - `ES6 \ ES9` → **xoá** khỏi ES6 (journal pre-image trước)
   - `ES9 \ ES6` → **vá** vào ES6 (delta đã bỏ sót create nào đó)
5. **Guard quy mô**: số xoá vượt `MAX_DELETE_RATIO` thì dừng, in mẫu ID, ghi
   danh sách đầy đủ ra `$STATE_DIR/to_delete`.

Luôn chạy so sánh **kể cả khi count hai bên bằng nhau**: N create cộng N
delete trên ES9 để lại tổng số y nguyên trong khi cả hai bên đều lệch.

### Pha 4 — VERIFY

Ba tầng, rẻ trước đắt sau:

1. So `_count` hai bên.
2. So **tập ID kỳ vọng**: `(ES6 − to_delete) ∪ to_repair` phải khớp tập ID
   ES9. Cả ba file đã có sẵn trên đĩa nên bước này miễn phí. Chỉ khi lệch mới
   export lại ES6 để định vị, kết quả ghi ra `verify_extra` / `verify_missing`.
3. So **nội dung** `SAMPLE_N` document ngẫu nhiên (seed cố định, lặp lại
   được). `_source` được copy nguyên văn nên mọi sai khác đều là lỗi thật,
   không phải khác biệt định dạng.

---

## 6. Resume

`resume` đọc checkpoint và chạy tiếp từ pha đang dở:

```bash
./scripts/es_rollback.sh status     # xem đang ở đâu
./scripts/es_rollback.sh resume
```

Checkpoint được ghi nguyên tử (file tạm rồi `replace`) sau **mỗi page**, nên
mất tối đa một page công.

**PIT hết hạn** được xử lý riêng: công cụ mở PIT mới và quét lại từ watermark
`updated_at` cuối cùng đã commit, dùng **`gte`** chứ không phải `gt`. Đây là
chi tiết quan trọng — với `gt`, mọi document có `updated_at` đúng bằng
watermark mà chưa kịp xử lý sẽ bị bỏ qua vĩnh viễn, vì ranh giới page có thể
rơi vào giữa một nhóm cùng timestamp. `gte` quét lại cả nhóm; phần chồng lấn
ghi đè trùng nội dung nên vô hại. Nếu PIT hết hạn quá 10 lần mà chưa xong,
công cụ dừng và yêu cầu tăng keep_alive hoặc giảm `PAGE_SIZE`.

---

## 7. Undo

Trước khi ghi đè hoặc xoá bất kỳ document nào, công cụ đọc bản hiện tại từ
ES6 và ghi vào `journal.tsv.gz`. `undo` phát lại journal đó:

```bash
./scripts/es_rollback.sh undo
```

### Định dạng journal

Năm cột, phân cách bằng tab, gzip (nhiều member vì được append qua nhiều lần
resume — `zcat` đọc liền mạch):

```
seq   id       op       found   source
1     doc-07   delta    1       {"id":"doc-07","title":"cũ",...}
2     doc-99   delta    0       {}
3     doc-04   delete   1       {"id":"doc-04",...}
4     doc-88   repair   0       {}
```

| Cột | |
|---|---|
| `seq` | Số thứ tự tăng dần trong một lần chạy. Dùng để chọn bản gốc nhất khi một ID có nhiều dòng |
| `id` | `_id` của document. **Luôn được ghi**, kể cả khi không có gì để backup |
| `op` | Thao tác sinh ra dòng này: `delta` (pha 1), `delete` / `repair` (pha 3). Chỉ để audit |
| `found` | `1` nếu ES6 đang có document đó. **Đây là cột `undo` dùng** |
| `source` | `_source` cũ nếu `found=1`, ngược lại `{}` |

Điểm quan trọng: **create và update đi chung đường `delta`** — ES9 không biết
ES6 đang có gì, nên chính kết quả `_mget` từ ES6 mới phân biệt được:

| Trên ES6 | Thực chất là | Journal ghi | `undo` làm gì |
|---|---|---|---|
| `found: true` | **update** | ID + toàn bộ `_source` cũ | ghi lại bản cũ |
| `found: false` | **create** | chỉ ID, `source` là `{}` | xoá document đó |

Nhờ vậy create chỉ tốn ~20 B/dòng thay vì ~190 B — delta càng nhiều create
thì journal càng nhỏ hơn bảng ước tính ở §8.

`op` là metadata thuần tuý; `undo` chỉ nhìn `found`, vì đó mới là thứ nói có
gì để khôi phục hay không.

### Truy vấn audit

```bash
J=$STATE_DIR/journal.tsv.gz
zcat $J | awk -F'\t' '$3=="delta"  && $4==1' | wc -l   # doc bị ghi đè
zcat $J | awk -F'\t' '$3=="delta"  && $4==0' | wc -l   # doc mới tạo trên ES6
zcat $J | awk -F'\t' '$3=="delete"'          | wc -l   # doc bị xoá
zcat $J | awk -F'\t' '$3=="repair"'          | wc -l   # doc delta bỏ sót, đã vá

# lấy lại nội dung cũ của một document cụ thể
zcat $J | awk -F'\t' '$2=="doc-07" {print $5; exit}' | jq .
```

### Chọn đúng bản pre-image

Khi `resume` ghi lại document mà lần chạy trước đã đồng bộ, `_mget` lúc đó
trả về bản **đã bị ghi đè**. Journal vì thế có thể có nhiều dòng cho một ID.
`undo` luôn lấy dòng có **seq nhỏ nhất mỗi ID** — tức bản gốc nhất.

Liên quan: `run` mới sẽ **lưu trữ** journal cũ thành
`journal.<timestamp>.tsv.gz` thay vì ghi tiếp vào đó, vì số seq bắt đầu lại
từ 0 mỗi lần chạy. Trộn hai lần chạy vào một file sẽ làm "seq nhỏ nhất" mất
ý nghĩa. `undo` chỉ phát lại lần chạy hiện tại; muốn dùng bản lưu trữ thì
phải thao tác tay.

### Giới hạn — đọc kỹ

- **Chỉ an toàn khi chưa flip traffic.** Sau khi flip, ES6 nhận write mới;
  `undo` ghi đè mù theo journal nên sẽ kéo những document đó về nội dung thời
  cutover, và xoá những document do sync tạo ra mà app vừa sửa.
- **Công cụ không chạy được chiều ngược.** Nếu đã flip và muốn quay lại phục
  vụ từ ES9, ES9 lại thiếu mọi write kể từ lúc flip — cần đồng bộ ES6→ES9.
  Công cụ này không làm được: nguồn cần PIT (ES6 6.8 không có) và đích dùng
  `/_doc/_bulk` (ES9 đã bỏ mapping type).
- Không khôi phục `refresh_interval` — đó là việc của `reset`.
- Journal nằm trong `STATE_DIR`. Mất `STATE_DIR` là mất khả năng undo (nhưng
  ES9 vẫn nguyên vẹn, xem §11).

---

## 8. Tinh chỉnh và bộ nhớ

Ba tham số quyết định bộ nhớ và thông lượng. Số liệu dưới đây đo trên bộ
dữ liệu của repo: `_source` trung bình **1054 B/doc**, dòng journal ~1085 B
thô và **~190 B sau gzip** (nén 5,7 lần).

| Biến | Ảnh hưởng |
|---|---|
| `PAGE_SIZE` | Số doc giữ trong RAM cùng lúc ở pha 1. Đây là tham số chi phối bộ nhớ. |
| `MGET_BATCH` | Số ID mỗi request đọc pre-image. **Độc lập với `PAGE_SIZE`.** |
| `BULK_BYTE_CAP` | Trần kích thước mỗi request `_bulk`. Hằng số 5 MB trong script, không phải env var — đúng khuyến nghị của Elastic và chưa từng có lý do đổi. |

### Vì sao `MGET_BATCH` tách rời `PAGE_SIZE`

`_mget` trả về **toàn bộ `_source`** của mọi ID được hỏi. Nếu đọc pre-image
cả page trong một request, với `PAGE_SIZE=100000`:

| | |
|---|---|
| Request body | 100k × ~12 B ≈ 1,2 MB — không sao |
| Response | 100k × ~1100 B ≈ **110 MB** |
| Sau khi parse | document 40 field → cây object phình ~4× → **~450 MB** |
| Đỉnh tạm thời | cộng bytes thô và bản decode → **~700 MB** |
| Cộng `pairs` của chính page đó | thêm **~220 MB** |

Tổng khoảng **1,2 GB RSS cho một page**, tuyến tính theo `PAGE_SIZE`. Không
có lỗi cứng nào — request nhỏ, ES không giới hạn kích thước response, vài
giây là xong — nên nó **âm thầm ngốn RAM** chứ không fail. Đường ghi đã có
`BULK_BYTE_CAP` chặn; `MGET_BATCH` làm điều tương tự cho đường đọc.

Mặc định `MGET_BATCH=1000` giữ mỗi response ở khoảng 1 MB bất kể `PAGE_SIZE`.
Không có lý do gì để tăng.

### Journal theo quy mô delta

| Số doc trong delta | Journal (gzip) |
|---|---|
| 80.000 (1% của 8M) | 15 MB |
| 400.000 (5%) | 76 MB |
| 2.000.000 (25%) | 381 MB |
| 8.000.000 (100%) | 1,5 GB |

Thời gian: `_mget` gộp vào chính vòng lặp phân trang, và là real-time GET
(không phân tích, không ghi segment) nên rẻ hơn bulk-index đáng kể. Thực tế
pha 1 chậm thêm khoảng **30–50%** so với không journal.

---

## 9. Bảng biến môi trường

Script chia thành ba tầng đúng theo thứ tự bạn có việc phải sửa tới chúng.
Chỉ tầng đầu là thứ phải nhìn mỗi lần chạy.

**Tầng 1 — kết nối** (luôn phải set cho một lần chạy thật)

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `ES6_URL` / `ES9_URL` | `http://localhost:9200` | |
| `SRC_INDEX` / `DST_INDEX` | `bench-es9` / `bench-es6` | Nguồn là ES9, đích là ES6 |
| `ES6_USER` / `ES6_PW` | `elastic` / `$ELASTIC_PW` | |
| `ES9_USER` / `ES9_PW` | `elastic` / `$ELASTIC_PW` | |
| `STATE_DIR` | `./.rollback-state` | Chứa cả journal — xem §3c và §12 |
| `TS_FIELD` | `updated_at` | Trường timestamp để delta sync |
| `SINCE` | (tự động đọc `_meta.cutover_at`) | Override mốc thời gian ISO-8601 bắt đầu delta sync |
| `REMOVE_FIELDS` | (rỗng) | Danh sách trường cần loại bỏ trước khi ghi về ES6 (ví dụ `modified_at`) |

**Tầng 2 — hiệu năng** (chỉ khi chạy chậm hoặc hết RAM)

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `PAGE_SIZE` | `10000` | Chi phối bộ nhớ pha 1. 10000 là trần của `index.max_result_window` |
| `MGET_BATCH` | `1000` | ID mỗi request đọc pre-image, và mỗi lô ở bước xoá/vá |
| `SLICES` | `auto` | Số slice song song khi quét ID. `auto` = mỗi shard một slice, `1` để tắt |
| `MAX_RETRY` | `6` | Số lần retry HTTP |

**Tầng 3 — an toàn.** Ba biến cuối *tắt* một guard, đọc pha tương ứng trước khi dùng.

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `SAFETY_MARGIN` | `300` | Giây lùi khỏi `cutover_at` |
| `MAX_DELETE_RATIO` | `0.10` | Chặn nếu số xoá vượt tỉ lệ này của ES6 |
| `FREEZE_WAIT` | `10` | Khoảng cách hai mẫu kiểm tra freeze |
| `SAMPLE_N` | `1000` | Số doc so nội dung ở pha verify |
| `SINCE` | *(rỗng)* | Ghi đè `cutover_at` |
| `ALLOW_PARTIAL` | `false` | Cho gate đi qua dù còn dead-letter |
| `ASSUME_YES` | `false` | Bỏ qua xác nhận khi vượt `MAX_DELETE_RATIO` |

**Debug** (tạm thời): `DEBUG_TIMING=1` bật các dòng `DEBUG` tách thời gian
theo từng chặng; `DEBUG_EVERY` (mặc định `50`) là khoảng cách page giữa các
dòng báo cáo khi quét ID.

`BULK_BYTE_CAP` (5 MB) là hằng số trong script, không phải env var — xem §8.

---

## 10. Xử lý sự cố

### Bảng tra nhanh

| Thông báo | Nên làm |
|---|---|
| `ES9 is still taking writes` | Dừng writer vào ES9 rồi chạy lại |
| `_meta.cutover_at missing` | `SINCE=2026-07-10T00:00:00Z ./es_rollback.sh run` |
| `is write-blocked` | Giải phóng disk ES6, chạy lệnh curl công cụ in ra |
| `gate FAILED ... only N were read` | `resume` cho tới khi delta chạy hết |
| `gate FAILED ... rejected by ES6` | Xem dưới |
| `id export incomplete` | Mạng đứt giữa chừng. `resume` — export chạy lại từ đầu |
| `scroll context lost` | Như trên. Tăng `PAGE_SIZE` để ít vòng lặp hơn |
| `more than 0.10 of ES6` | Xem dưới |
| `PIT expired N times` | Giảm `PAGE_SIZE` để mỗi page nhanh hơn |
| `VERIFY FAILED` | Xem `verify_extra`, `verify_missing`, `verify_sample_diff`. **Chưa flip** |

### Khi gate chặn vì dead-letter

```bash
head -3 $STATE_DIR/deadletter.ndjson | python3 -m json.tool
```

Mỗi bản ghi có `_id`, `status`, `error` nguyên văn và cả payload đã gửi.
Nguyên nhân thường gặp:

- **`mapper_parsing_exception`** — ES9 sinh ra field mới hoặc đổi kiểu trong
  14 ngày qua mà mapping ES6 không nhận. Sửa mapping ES6 rồi `resume`.
- **`strict_dynamic_mapping_exception`** — ES6 đặt `dynamic: strict` và
  document có field lạ. Thêm field vào mapping rồi `resume`.
- **`cluster_block_exception`** — ES6 đầy đĩa giữa chừng. Giải phóng, gỡ
  block, `resume`.

Chỉ dùng `ALLOW_PARTIAL=true` khi đã hiểu và chấp nhận rằng ES6 sẽ thiếu
đúng những document đó.

### Khi guard quy mô xoá chặn

```bash
wc -l $STATE_DIR/to_delete
head $STATE_DIR/to_delete
```

Đối chiếu vài ID trong đó với ES9 để xác nhận chúng thật sự đã bị xoá:

```bash
curl -s -u elastic:$ELASTIC_PW "$ES9_URL/bench-es9/_doc/<id>"   # phải 404
```

Đúng như dự kiến thì:
```bash
ASSUME_YES=true ./scripts/es_rollback.sh resume
```

### Thang xử lý khi bế tắc, rẻ → đắt

1. `resume` — lỗi tạm thời.
2. Sửa nguyên nhân gốc rồi `resume` — mapping conflict, đĩa đầy.
3. `ALLOW_PARTIAL=true` — chấp nhận thiếu một số document đã biết rõ.
4. `undo` → mở lại write cho ES9 → **ở lại ES9**. Luôn khả dụng khi chưa flip.
5. Copy lại toàn bộ: `SINCE=1970-01-02T00:00:00Z` biến cửa sổ delta thành
   *toàn bộ index*. Chính công cụ này copy lại cả 8M doc, không cần tin
   `updated_at` nữa — cũng là cách vá được hạn chế nêu ở §13. Đắt (vài giờ)
   nhưng luôn đúng.

---

## 11. Các cơ chế an toàn

**ES9 không bao giờ bị ghi.** Toàn bộ thao tác lên ES9 là `GET /`, `_count`,
`_mapping`, `_search`, `_pit`, `_mget`, `_refresh`. Nghĩa là ES9 luôn là bản
gốc nguyên vẹn, và mọi kịch bản hỏng đều còn đường lui — kể cả khi mất sạch
`STATE_DIR` lẫn journal.

**Gate chặn giữa sync và xoá.** Có document bị ES6 từ chối → gate không cho
qua → không lệnh xoá nào chạy.

**Kiểm tra export đầy đủ.** Số ID export phải khớp chính xác `_count` mỗi
bên trước khi so sánh.

**Chặn theo quy mô xoá.** Vượt `MAX_DELETE_RATIO` thì dừng và đòi xác nhận
tường minh.

**Vá cả chiều ngược.** ID có ở ES9 mà thiếu ở ES6 được `_mget` về và ghi vào
ES6, thay vì chỉ báo cáo.

**Vẫn so sánh dù count bằng nhau.** Count khớp không suy ra tập ID khớp.

**Snapshot nhất quán khi phân trang.** ES9 dùng PIT + `_shard_doc`; ES6 6.8
dùng scroll.

**Thứ tự byte khi so tập ID.** `LC_ALL=C` là **bắt buộc** và đã được set
sẵn trong script. Dưới locale UTF-8, collation bỏ qua dấu câu nên hai ID khác
nhau có thể so ra bằng nhau và `comm` ghép sai cặp — tức xoá nhầm document.
`comm` so theo đúng collation mà `sort` đã dùng, nên cả hai phải cùng ở C.

**Đọc kỹ response `_bulk`.** ES trả HTTP 200 ngay cả khi có item lỗi. Công cụ
phân loại từng item: lỗi tạm thời (429, circuit breaker) retry riêng subset
đó với backoff; lỗi vĩnh viễn vào `deadletter.ndjson` kèm payload gốc.

**`refresh_interval`.** Tạm đặt `30s`, nhớ giá trị gốc, `reset` trả lại.

**Khoá chống chạy song song.** Tiến trình thứ hai bị từ chối; khoá cũ của
tiến trình đã chết được nhận diện qua tín hiệu 0.

---

## 12. Nội dung `STATE_DIR`

Hai tầng, và phân biệt được hai tầng này là quan trọng khi sự cố:

- **`$STATE_DIR/`** — mọi thứ mà `resume` và `undo` phụ thuộc vào. **Mất là
  mất khả năng undo.** Đừng xoá tay khi một lần chạy chưa kết thúc.
- **`$STATE_DIR/work/`** — file tạm. Lần chạy nào cũng có thể xoá sạch, kể cả
  giữa lúc đang chạy. Xoá thư mục này không làm mất tiến độ (`resume` đọc
  `state.env`, không đọc `work/`).

### 12.1 Tầng bền — `$STATE_DIR/`

| File | Chức năng |
|---|---|
| `state.env` | Pha hiện tại + toàn bộ bộ đếm, dạng `key=value` source được bằng bash. Ghi theo kiểu temp+`mv` nên crash không bao giờ để lại file dở. Đây là thứ `resume` đọc để biết đang ở đâu |
| `journal.tsv.gz` | Pre-image của **lần chạy hiện tại**: `seq/id/op/found/source`, xem §7. Mọi document đều được đọc từ ES6 và ghi vào đây **trước khi** bị ghi đè hoặc xoá — đây là toàn bộ cơ sở của `undo` |
| `journal.<ts>.tsv.gz` | Journal các lần chạy trước, tự động lưu trữ khi `run` mới bắt đầu. `undo` **không** đọc các file này (seq đánh lại từ 0 mỗi lần chạy nên trộn vào sẽ làm "seq nhỏ nhất mỗi id" mất nghĩa). Muốn phục hồi từ đây phải làm tay |
| `deadletter.ndjson` | Document ES6 từ chối vĩnh viễn, kèm status, error, action và source gốc. Gate ở pha 2 chặn nếu file này không rỗng |
| `pit_id.txt` | PIT id của pha 1 đang mở, để `resume` dùng lại thay vì quét lại từ đầu |
| `search_after.json` | Con trỏ phân trang của pha 1. Chỉ được đẩy lên sau khi page đã bulk xong và bộ đếm đã ghi — xem §"Con trỏ được đẩy sau cùng" |
| `es9_ids.sorted` / `es6_ids.sorted` | Toàn bộ ID sống của hai bên, đã `sort -u`. Đầu vào của phép `comm` ở pha 3 |
| `to_delete` / `to_repair` | Kết quả so sánh hai chiều: chỉ có ở ES6 (sẽ xoá) và chỉ có ở ES9 (sẽ vá). **Đọc `to_delete` trước khi dùng `ASSUME_YES`** |
| `verify_extra` / `verify_missing` | Chỉ sinh ra khi verify fail: ID thừa/thiếu trên ES6 so với ES9 |
| `verify_sample_diff` | ID mà nội dung `_source` lệch giữa hai bên |
| `run.log` | Log đầy đủ có timestamp, append qua mọi lần `resume` |
| `lock/pid` | Chống hai tiến trình chạy song song. Lock của tiến trình đã chết được nhận diện qua tín hiệu 0 và tự thu hồi |

### 12.2 Tầng tạm — `$STATE_DIR/work/`

Tên file theo đúng một quy ước: **`<chủ sở hữu>.<mục đích>.<đuôi>`**, trong đó
chủ sở hữu là pha hoặc hàm ghi ra nó. Nhờ vậy một glob không bao giờ quét
trúng file của chủ khác. Mọi output của `split(1)` nằm riêng trong
`work/parts/`, để glob theo lô (`parts/delete.*`) không thể trúng file có tên
riêng.

Một thứ chỉ là **file** thay vì pipe khi thuộc đúng một trong hai trường hợp:

1. **Nó là request body của curl.** `http_retry` gửi lại *đúng file đó* sau khi
   gặp 429/503, mà pipe thì không đọc lại được.
2. **Nó là con trỏ phải sống sót qua crash**, nên được ghi ra tên tạm rồi `mv`
   vào chỗ — `mv` trên cùng filesystem là atomic nên không có ghi dở.

Mọi thứ ngoài hai trường hợp trên đều đã là pipe.

| File | Chủ | Chức năng |
|---|---|---|
| `http.resp.json` | mọi request | Body của response HTTP gần nhất. Các slice chạy song song mỗi cái trỏ biến này sang file riêng `ids.<side>.<n>.resp` |
| `delta.request.json` | pha 1 | Body search một page delta (PIT + `search_after` + range) |
| `delta.page.ids` | pha 1 | Danh sách ID của page, đầu vào cho bước đọc pre-image |
| `delta.chunk.NNNN.ndjson` | pha 1 | Page đã chia thành các bulk body ≤ 5 MB. Chia theo byte và **theo cặp dòng**, để dòng action không bao giờ bị tách khỏi dòng source của nó |
| `delta.cursor.next.json` | pha 1 | Con trỏ kế tiếp, ghi tạm ở đây rồi `mv` sang `search_after.json` |
| `journal.mget.json` | pha 1, 3 | Body `_mget` đọc pre-image từ ES6 |
| `bulk.send.ndjson` | bulk io | Chỉ sinh ra khi bulk bị từ chối một phần. Lượt đầu gửi thẳng file của caller, không copy |
| `bulk.retry.ndjson` | bulk io | Các item bị từ chối tạm thời, chờ gửi lại. **Bắt buộc khác path** với `bulk.send.ndjson` vì `parse_bulk` truncate file retry trước khi đọc file đã gửi |
| `bulk.pairs.tsv` | bulk io | Map thứ tự item trong bulk → dòng action + dòng source, để ghép với verdict từ response |
| `preflight.maxagg.json` | pha 0 | Body agg `max(updated_at)`, dùng ở hai mẫu kiểm tra freeze |
| `pit.close.json` | pha 1, 3 | Body đóng PIT |
| `ids.src.<n>.{request,resp,ids}` | pha 3 | Một bộ cho mỗi slice quét ID trên ES9. Con trỏ `search_after` giữ trong biến shell, không ra file — slice hỏng thì chạy lại cả walk nên không cần bền |
| `ids.dst.<n>.{request,resp,ids}` | pha 3 | Tương tự cho ES6. `request` dùng chung cho cả body khởi tạo và body scroll — mỗi body đã được request tiêu thụ trước khi body sau ghi lên |
| `verify.sample.ids` | pha 4 | Mẫu ID ngẫu nhiên (seed cố định 42 nên lặp lại được) |
| `verify.sample.mget.json` | pha 4 | Body `_mget` cho mẫu, dùng cho cả hai cluster |
| `verify.sample.src.json` | pha 4 | Bản copy response của ES9. Response ES6 đọc thẳng từ `http.resp.json`, không cần copy thứ hai |
| `verify.expected.ids` | pha 4 | Tập ID ES6 **đáng lẽ phải có** = (es6 − to_delete) + to_repair |
| `verify.dst.sorted` | pha 4 | Chỉ có khi tập trên không khớp: ID ES6 quét lại để khoanh vùng lệch |
| `plan.count.json` | `plan` | Body count phạm vi delta |
| `undo.rows.tsv` | `undo` | Journal đã giải nén và lọc còn seq nhỏ nhất mỗi ID |
| `undo.bulk.ndjson` | `undo` | Bulk body phục hồi: `index` nếu `found=1`, `delete` nếu `found=0` |
| `parts/preimage.*` | pha 1, 3 | Lô ID `MGET_BATCH` dòng để đọc pre-image |
| `parts/delete.*` | pha 3 | Lô ID cần xoá |
| `parts/repair.*` | pha 3 | Lô ID cần vá |
| `parts/undo.*` | `undo` | Lô dòng journal cần replay |

---

## 13. Những gì công cụ **không** làm

- Không replication liên tục — chỉ chạy một lần theo yêu cầu.
- Không chuyển traffic. Flip là thao tác riêng của bạn, sau khi verify pass.
- Không phát hiện được update *không* bump `updated_at`. Create bỏ sót thì
  pha 3 vá được; update bỏ sót thì không có tín hiệu nào để nhận ra. Cách vá
  duy nhất là copy lại toàn bộ (§10, mục 5).
- Không đồng bộ chiều ES6 → ES9.
- Không tạo index. `DST_INDEX` phải tồn tại sẵn.
- Không đụng tới alias hay mapping.

---

## 14. Test

Không cần cluster thật — `fake_es.py` dựng một ES giả trong bộ nhớ kèm
fault injection (cần `python3`, chỉ để chạy test).

```bash
./scripts/test_es_rollback.sh
```

Phủ cả happy path lẫn các đường hỏng: ES9 chưa freeze, document bị từ chối
chặn được pha xoá, bão 429, node chết giữa delta rồi resume, export ID bị cắt
cụt, chặn theo quy mô xoá, lưu trữ journal giữa hai lần chạy, chống chạy song
song, và `undo` khôi phục chính xác.
