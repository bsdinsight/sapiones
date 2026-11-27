# Hội tụ địa giới VN về `bsd_vn_address` (frm.vn.ward)

Nhánh: `feat/bsd-vn-address-converge`.

## Tình trạng
- ✅ `bsd_vn_address` LIVE: `github.com/bsdinsight/bsd-vn-address` (main, f31aa5f) — model `frm.vn.ward`
  core + `res.partner.vn_ward_id` + loader 3321 phường/xã.
- ✅ Nhánh này: repoint `hr.employee.private_vn_ward_id` + `res.partner.vn_ward_id` → `frm.vn.ward`;
  `l10n_vn_address` depend `bsd_vn_address`; **bump version 19.0.1.1.0** + **pre-migrate** remap.
- Agrione: inherit `frm.vn.ward` + 15 field nông học + migrate 21 ward (phía họ, song song).

## Migration (đã viết)
- `l10n_vn_hr/migrations/19.0.1.1.0/pre-migrate.py` — remap `hr.employee.private_vn_ward_id`.
- `l10n_vn_address/migrations/19.0.1.1.0/pre-migrate.py` — remap `res.partner.vn_ward_id`.
- Cách chạy: **pre-migrate** (TRƯỚC khi Odoo đổi FK) → UPDATE ID cũ (sapiones.vn.ward) sang ID
  frm.vn.ward khớp theo `(name, state_id)`; dòng không khớp → NULL (tránh vỡ FK). Idempotent,
  tự bỏ qua nếu thiếu bảng (greenfield). state_id khớp tuyệt đối (chung res.country.state).
- Giữ model `sapiones.vn.ward` trong l10n_vn_address ở nhánh này để pre-migrate còn đọc được
  tên/tỉnh cũ. Gỡ model đó = **PR follow-up** sau khi migrate xong.

## ⛔ Điều kiện MERGE (vào main) — chỉ khi quyết converge prod
Nhánh vẫn treo tới khi release prod xong (dưới). Nhà máy đường greenfield KHÔNG cần nhánh này.

## Release plan cho sapiones.com prod (KHÔNG gấp — rủi ro THẤP vì data ward prod ~trống)
Trên VPS, stack `sapiones`:
1. **BACKUP** toàn bộ DB (demo + mọi tenant) — bắt buộc.
2. Đưa `bsd_vn_address` lên addons-path: clone `github.com/bsdinsight/bsd-vn-address` vào thư mục
   addons của stack (hoặc submodule) + đảm bảo `addons_path` trỏ tới. Pull code sapiones nhánh này.
3. **Canary — DB demo trước:**
   `odoo -d demo -i bsd_vn_address -u l10n_vn_address,l10n_vn_hr --stop-after-init ...`
   (bsd_vn_address cài mới → post_init nạp 3321; pre-migrate remap ward cũ.)
4. **Verify demo:** `frm.vn.ward` có ~3321; `private_vn_ward_id`/`vn_ward_id` trỏ frm.vn.ward;
   không lỗi FK; địa chỉ NV/partner còn đúng; log migrate in "khớp N, null M".
5. **Từng tenant DB:** lặp qua danh sách DB tenant, chạy cùng lệnh `-d <tenant>`.
6. Verify vài tenant → restart stack.
7. **Merge nhánh → main** (để main = prod).

Rủi ro chính = thao tác fleet nhiều DB → canary demo trước + có backup. Data remap gần như 0 dòng.

## Follow-up (PR riêng, sau converge)
Gỡ model `sapiones.vn.ward` + loader (`hooks.py`) + `views/vn_ward_views.xml` khỏi `l10n_vn_address`
(đã dư vì frm.vn.ward canonical). `l10n_vn_address` còn lại chỉ là shim (hoặc gộp hẳn vào bsd).
