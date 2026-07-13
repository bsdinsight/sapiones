# -*- coding: utf-8 -*-
{
    'name': 'Sapiones - Chứng chỉ nhân viên & Cảnh báo hết hạn',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Quản lý chứng chỉ, bằng cấp, giấy phép của nhân viên; tự động theo dõi trạng thái '
               '& nhắc gia hạn trước khi hết hạn | Employee certificate & license expiry tracking',
    'description': """
Chứng chỉ nhân viên & Cảnh báo hết hạn (Sapiones)
=================================================

Quản lý tập trung chứng chỉ / bằng cấp / giấy phép của nhân viên và để Odoo
tự canh ngày hết hạn giúp bạn — nhắc quản lý gia hạn trước khi hết hạn.

* Hồ sơ chứng chỉ theo từng nhân viên: số hiệu, đơn vị cấp, ngày cấp / ngày hết hạn, tệp đính kèm
* Danh mục loại chứng chỉ (an toàn lao động, vận hành thiết bị, nghề, ngoại ngữ, bằng cấp…) kèm thời hạn mặc định & cờ "bắt buộc"
* Trạng thái tự động: Còn hạn / Sắp hết hạn / Hết hạn / Không thời hạn, kèm số ngày còn lại
* Cron nhắc hạn: tự tạo việc cần làm (To-Do) cho quản lý trước khi chứng chỉ hết hạn
* Tab "Chứng chỉ" ngay trên hồ sơ nhân viên + báo cáo lọc chứng chỉ sắp / đã hết hạn

Chỉ phụ thuộc Odoo HR chuẩn (hr). Mã nguồn mở, miễn phí (LGPL-3).

Phát triển bởi BSD — https://bsdinsight.com
""",
    'author': 'BSD',
    'website': 'https://sapiones.com',
    'support': 'info@bsdinsight.com',
    'license': 'LGPL-3',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/certificate_type_data.xml',
        'data/cron_data.xml',
        'views/certificate_views.xml',
        'views/hr_employee_views.xml',
        'views/menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
}
