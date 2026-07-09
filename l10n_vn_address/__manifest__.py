{
    'name': 'Vietnam - Administrative Divisions (2025)',
    'version': '19.0.1.1.0',
    'category': 'Localization',
    'summary': 'Tỉnh/Thành phố → Phường/Xã Việt Nam (cải cách 2025: 34 tỉnh, 2 cấp, bỏ huyện)',
    'description': """
Đơn vị hành chính Việt Nam 2025 (Sapiones Community)
====================================================

Phản ánh cải cách hành chính 2025: **34 tỉnh/thành**, **bỏ cấp huyện/quận** —
chỉ còn 2 cấp **Tỉnh/Thành phố → Phường/Xã**.

* Tỉnh/TP: dùng luôn ``res.country.state`` (Odoo 19 base đã có sẵn 34 tỉnh).
* Phường/Xã: model ``sapiones.vn.ward`` (3321 đơn vị), tự nạp khi cài (post_init).
* ``res.partner`` bổ sung trường Phường/Xã (lọc theo Tỉnh).

Dữ liệu khớp xã → tỉnh theo tên đã chuẩn hoá (NFC + bỏ tiền tố). Idempotent.

Phát triển bởi BSD — https://bsdinsight.com
""",
    'author': 'BSD',
    'website': 'https://bsdinsight.com',
    'license': 'LGPL-3',
    'depends': ['base', 'bsd_vn_address'],
    'data': [
        'security/ir.model.access.csv',
        'views/vn_ward_views.xml',
        'views/res_partner_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
