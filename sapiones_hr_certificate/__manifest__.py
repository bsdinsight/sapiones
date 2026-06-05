{
    'name': 'Sapioness HR - Chứng chỉ nhân viên',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Employees',
    'summary': 'Quản lý chứng chỉ/bằng cấp nhân viên + theo dõi & cảnh báo hết hạn',
    'description': """
Chứng chỉ nhân viên (Sapioness Community)
========================================

Quản lý chứng chỉ / bằng cấp / giấy phép của nhân viên, đặc biệt phục vụ
tuân thủ an toàn & vận hành trong doanh nghiệp sản xuất.

* Danh mục loại chứng chỉ (an toàn LĐ, vận hành thiết bị, nghề, ngoại ngữ, bằng cấp...)
* Hồ sơ chứng chỉ: số hiệu, đơn vị cấp, ngày cấp / ngày hết hạn, tệp đính kèm
* Trạng thái tự động: Còn hạn / Sắp hết hạn / Hết hạn / Không thời hạn
* Cron nhắc hạn: tự tạo việc cần làm (To-Do) cho quản lý trước khi chứng chỉ hết hạn
* Tab "Chứng chỉ" trên hồ sơ nhân viên + báo cáo lọc chứng chỉ sắp/đã hết hạn

Phát triển bởi BSD — https://bsdinsight.com
""",
    'author': 'BSD',
    'website': 'https://bsdinsight.com',
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
    'installable': True,
    'application': False,
}
