# Hội tụ địa giới VN về `bsd_vn_address` (frm.vn.ward) — GROUNDWORK, CHƯA MERGE

Nhánh: `feat/bsd-vn-address-converge`.

## Bối cảnh
Ghép Agrione (nhà máy đường) + Sapiones HR vào CÙNG 1 DB Odoo. Cả hai đều có module
địa giới VN 2025 và **cùng thêm `res.partner.vn_ward_id`** nhưng trỏ 2 model khác nhau
(`sapiones.vn.ward` vs `frm.vn.ward`) → co-install thô **vỡ định nghĩa field**.

Chốt (anh Đại duyệt hướng (b)): **canonical = `frm.vn.ward`** (Agrione cắm sâu 15 model →
giữ nguyên), tách ra module dùng chung **`bsd_vn_address`**. Sapiones repoint sang đó.

## Nhánh này làm gì (nhỏ, chỉ repoint)
- `l10n_vn_hr/models/hr_employee.py`: `private_vn_ward_id` comodel `sapiones.vn.ward` → `frm.vn.ward`.
- `l10n_vn_address/models/res_partner.py`: `vn_ward_id` comodel `sapiones.vn.ward` → `frm.vn.ward`.
- `l10n_vn_address/__manifest__.py`: depends `+ bsd_vn_address` (l10n_vn_hr nhận `frm.vn.ward` qua transitive dep).

## ⛔ CHƯA ĐƯỢC MERGE cho tới khi đủ 3 điều
1. **`bsd_vn_address` tồn tại + deploy** (Agrione tách): định nghĩa `frm.vn.ward` + tỉnh + nạp
   ~3321 phường/xã (phủ đủ như `sapiones.vn.ward` đang có).
2. **Xác nhận `frm.vn.ward.state_id` → `res.country.state`.** Nếu Agrione đặt tên field tỉnh khác
   (vd `province_id`) thì phải sửa `domain` + onchange ở 2 file trên.
3. **Migration cho sapiones.com prod** (demo + tenants đang chạy `sapiones.vn.ward`): remap
   giá trị `private_vn_ward_id`/`vn_ward_id` cũ (ID sapiones.vn.ward) → ID `frm.vn.ward`
   khớp theo tên phường/xã đã chuẩn hoá. (Data ward hiện gần như trống nên migration nhẹ,
   nhưng vẫn phải có để không treo FK.)

## Follow-up (PR riêng, sau khi migrate)
- Gỡ hẳn model `sapiones.vn.ward` + post_init loader + `views/vn_ward_views.xml` khỏi
  `l10n_vn_address` (dư thừa khi đã có `frm.vn.ward`). Giữ lại nhánh này tối thiểu để dễ review.

## Rollout
Deploy `bsd_vn_address` lên **sapiones.com prod TRƯỚC/CÙNG** khi merge (vì `l10n_vn_hr` chạy ở
demo + tenants). Agrione greenfield thì không cần migrate (DB mới).
