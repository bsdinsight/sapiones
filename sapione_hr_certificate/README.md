# SapiOne HR - Chứng chỉ nhân viên (`sapione_hr_certificate`)

Quản lý chứng chỉ / bằng cấp / giấy phép của nhân viên + **theo dõi & cảnh báo hết hạn**. Module nền (mã nguồn mở, **LGPL-3**) của SapiOne by [BSD](https://bsdinsight.com).

## Tính năng

- **Loại chứng chỉ** (`sapione.hr.certificate.type`): danh mục theo nhóm (an toàn LĐ, vận hành thiết bị, nghề, bằng cấp, ngoại ngữ...), thời hạn mặc định, bắt buộc. Kèm sẵn ~12 loại phổ biến cho sản xuất (ATVSLĐ, PCCC, xe nâng, nồi hơi, an toàn điện, thợ hàn...).
- **Chứng chỉ** (`sapione.hr.certificate`): số hiệu, đơn vị cấp, ngày cấp/hết hạn, tệp đính kèm. Chọn loại → tự gợi ý ngày hết hạn theo thời hạn mặc định.
- **Trạng thái tự động**: Còn hạn / Sắp hết hạn / Hết hạn / Không thời hạn (badge màu).
- **Cron nhắc hạn** (chạy hằng ngày): tạo việc cần làm (To-Do) cho quản lý trực tiếp trước khi chứng chỉ hết hạn (mặc định 60 ngày — chỉnh qua `ir.config_parameter` `sapione_hr_certificate.warn_days`).
- **Hồ sơ nhân viên**: tab **Chứng chỉ** + cảnh báo nếu có cert hết hạn.
- **Báo cáo/lọc**: Hết hạn / Sắp hết hạn / Còn hạn; nhóm theo nhân viên / loại / nhóm.

## Phụ thuộc

`hr`

## Cấu hình

- Số ngày cảnh báo trước hạn: `ir.config_parameter` → `sapione_hr_certificate.warn_days` (mặc định 60).

## Lưu ý

Odoo có sẵn field `certificate` trên hr.employee (chỉ là *cấp học vấn*). Module này dùng model riêng `sapione.hr.certificate`, không xung đột.

## Giấy phép

LGPL-3. © BSD — https://bsdinsight.com
