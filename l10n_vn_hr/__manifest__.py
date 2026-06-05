{
    'name': 'Vietnam - HR Localization',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Employees',
    'summary': 'Bản địa hóa hồ sơ nhân sự Việt Nam: CCCD, MST, sổ BHXH, người phụ thuộc',
    'description': """
Bản địa hóa nhân sự Việt Nam (Sapioness Community)
=================================================

Bổ sung các thông tin nhân sự đặc thù Việt Nam vào hồ sơ nhân viên:

* Giấy tờ tùy thân: số CCCD (12 số) / CMND (9 số), ngày cấp, nơi cấp
* Mã số thuế thu nhập cá nhân (MST)
* Số sổ Bảo hiểm xã hội (BHXH)
* Quê quán, dân tộc, tôn giáo
* Quản lý **người phụ thuộc** phục vụ giảm trừ gia cảnh (thuế TNCN)

Đây là module nền (mã nguồn mở, miễn phí) — làm cơ sở dữ liệu cho các
module thương mại như tính lương (Payroll VN).

Phát triển bởi BSD — https://bsdinsight.com
""",
    'author': 'BSD',
    'website': 'https://bsdinsight.com',
    'license': 'LGPL-3',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_dependent_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
}
