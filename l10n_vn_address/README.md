# Vietnam - Administrative Divisions 2025 (`l10n_vn_address`)

Đơn vị hành chính Việt Nam theo cải cách **2025**: **34 tỉnh/thành**, **bỏ cấp huyện/quận** — chỉ còn 2 cấp **Tỉnh/Thành phố → Phường/Xã**. Module nền (mã nguồn mở, **LGPL-3**) của SapiOne by [BSD](https://bsdinsight.com).

## Tính năng

- **Tỉnh/Thành phố**: dùng luôn `res.country.state` (Odoo 19 base đã có sẵn 34 tỉnh post-2025, mã `VN-XX`).
- **Phường/Xã**: model `sapione.vn.ward` (name, code, state_id, active) — **3321** đơn vị, **tự nạp khi cài** (`post_init_hook`).
- `res.partner` thêm trường **Phường/Xã** (lọc theo Tỉnh đã chọn).
- Menu quản lý: **Địa giới VN → Tỉnh/Thành phố · Phường/Xã**.

## Cách hoạt động (seed)

Khi cài, `post_init_hook` đọc `data/wards.json` và tạo phường/xã, **khớp về tỉnh** trong `res.country.state` theo **tên đã chuẩn hoá** (NFC Unicode + lowercase + bỏ tiền tố "thủ đô/thành phố/tỉnh"), có ALIAS `Huế ↔ Thừa Thiên - Huế`. **Idempotent** theo `(state_id, name)` — cài lại không trùng.

## Phụ thuộc

`base` (chứa `res.country.state`, `res.partner`).

## Lưu ý

- Yêu cầu base có sẵn 34 tỉnh post-2025 (đúng với **Odoo 19**). Nếu cài trên base cũ (63 tỉnh), một số xã có thể không khớp — xem log cảnh báo "xã chưa khớp tỉnh".
- Không mô hình hoá cấp huyện (đã bỏ từ 2025).

## Giấy phép

LGPL-3. © BSD — https://bsdinsight.com
