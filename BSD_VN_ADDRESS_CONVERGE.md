# Hội tụ địa giới VN về `bsd_vn_address` (frm.vn.ward) — GROUNDWORK, CHƯA MERGE

Nhánh: `feat/bsd-vn-address-converge`.

## Bối cảnh
Ghép Agrione (nhà máy đường) + Sapiones HR vào CÙNG 1 DB Odoo. Cả hai đều có module
địa giới VN 2025 và **cùng thêm `res.partner.vn_ward_id`** nhưng trỏ 2 model khác nhau
(`sapiones.vn.ward` vs `frm.vn.ward`) → co-install thô **vỡ định nghĩa field**.

Chốt (anh Đại duyệt hướng (b)): **model-canonical = `frm.vn.ward`** (Agrione cắm sâu 15 model
→ giữ tên), tách ra module dùng chung **`bsd_vn_address`**.

## ⚠️ Phát hiện quan trọng (Agrione rà code, 2 điểm)
1. ✓ `frm.vn.ward.state_id` = Many2one `res.country.state` (required) → domain/onchange của
   Sapiones chạy KHÔNG cần sửa. frm.vn.ward có thêm `code` (Char) + ~15 field nông học.
2. ⚠️ **DATA-canonical = SAPIONES, KHÔNG phải Agrione.** frm_vn_address KHÔNG có data ward
   (chỉ ~21 ward tên CŨ trước cải cách, code=NULL, tạo ad-hoc). Bộ **3321 phường/xã chuẩn
   (NFC + code)** là của Sapiones (`l10n_vn_address` nạp qua post_init). → `bsd_vn_address`
   phải MANG bộ data + loader của Sapiones.

## Split 3 module (đã thống nhất với Agrione)
- **`bsd_vn_address`** (mới, shared BSD): model `frm.vn.ward` CORE (name/code/state_id/active)
  + **sở hữu `res.partner.vn_ward_id`** + **loader 3321 ward (port từ Sapiones l10n_vn_address)**.
- **`frm_vn_address`** (Agrione): depend bsd_vn_address + INHERIT frm.vn.ward thêm 15 field nông học
  (15 model Agrione zero-change) + migrate 21 ward cũ; BỎ khai res.partner.vn_ward_id.
- **Sapiones**: `l10n_vn_hr` repoint `private_vn_ward_id` → frm.vn.ward + depend bsd_vn_address.
  `l10n_vn_address` **tan vào bsd_vn_address** (model + loader + res.partner field + views chuyển sang),
  coi như retire (nội dung ~90% chính là bsd_vn_address, chỉ đổi tên model sapiones.vn.ward→frm.vn.ward).

## Nhánh này (groundwork) đang làm gì
- `l10n_vn_hr/hr_employee.py`: `private_vn_ward_id` comodel → `frm.vn.ward`. ✓
- `l10n_vn_address/res_partner.py`: `vn_ward_id` → `frm.vn.ward` (tạm; field này sẽ CHUYỂN hẳn sang bsd_vn_address).
- `l10n_vn_address/__manifest__.py`: depend `+ bsd_vn_address`.

## ⛔ CHƯA MERGE tới khi
1. **`bsd_vn_address` được dựng** (port l10n_vn_address của Sapiones → đổi model thành frm.vn.ward
   + giữ loader 3321) và deploy lên sapiones.com prod.
2. Agrione refactor `frm_vn_address` (inherit + bỏ res.partner field + migrate 21 ward).
3. **Migration sapiones.com prod**: remap `private_vn_ward_id`/`vn_ward_id` cũ (ID sapiones.vn.ward)
   → ID frm.vn.ward khớp theo tên chuẩn hoá. (Data ward prod hiện gần như trống → nhẹ.)

## Điểm chờ Đại quyết
Ai dựng `bsd_vn_address` + đặt repo nào (đề xuất: **repo shared BSD mới**, vì RealtyPro/Parkone
cũng sẽ xài). Sapiones sẵn sàng port l10n_vn_address (vì nội dung là của mình).
