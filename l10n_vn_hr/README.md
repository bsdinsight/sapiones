# Vietnam - HR Localization (`l10n_vn_hr`)

Bản địa hóa hồ sơ nhân sự Việt Nam cho Odoo — module nền (mã nguồn mở, **LGPL-3**) của bộ giải pháp **SapiOne** by [BSD](https://bsdinsight.com).

## Tính năng

Bổ sung vào hồ sơ nhân viên (`hr.employee`) các thông tin đặc thù Việt Nam:

- **Giấy tờ tùy thân:** số CCCD (12 số) / CMND (9 số), ngày cấp, nơi cấp.
- **Thuế:** mã số thuế thu nhập cá nhân (MST).
- **Bảo hiểm:** số sổ BHXH.
- **Khác:** quê quán, dân tộc, tôn giáo.
- **Người phụ thuộc:** quản lý danh sách người phụ thuộc (con / vợ-chồng / cha-mẹ...) phục vụ **giảm trừ gia cảnh** khi tính thuế TNCN, kèm thời gian hiệu lực giảm trừ.

Các trường thông tin nằm trong tab **“Thông tin Việt Nam”** của hồ sơ nhân viên, chỉ hiển thị cho người dùng nhóm Nhân sự (PII được bảo vệ).

## Kiểm tra dữ liệu

- CCCD/CMND: 9 hoặc 12 chữ số.
- MST: 10 hoặc 13 chữ số.
- Số sổ BHXH: đúng 10 chữ số.

## Phụ thuộc

- `hr`

## Cài đặt

Đặt thư mục `l10n_vn_hr` vào addons path của Odoo 19, cập nhật danh sách ứng dụng và cài đặt module.

## Vai trò trong SapiOne

Đây là **lớp dữ liệu nền** cho các module thương mại (đặc biệt là Payroll VN): MST, sổ BHXH, người phụ thuộc là đầu vào để tính BHXH và thuế TNCN.

## Giấy phép

LGPL-3. © BSD — https://bsdinsight.com
