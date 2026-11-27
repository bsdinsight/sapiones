# -*- coding: utf-8 -*-
"""Remap hr.employee.private_vn_ward_id: sapiones.vn.ward (cũ) -> frm.vn.ward (bsd_vn_address).

CHẠY TRƯỚC khi Odoo đổi FK của field sang frm_vn_ward → tránh vỡ ràng buộc khóa ngoại
(giá trị cũ là ID sapiones.vn.ward, không tồn tại trong frm.vn.ward). Khớp theo
(name, state_id): state_id chung res.country.state nên ID tỉnh khớp tuyệt đối; name khớp
vì cùng nguồn wards.json. Dòng nào không khớp → set NULL (an toàn FK; user chọn lại).
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        SELECT count(*) FROM information_schema.tables
        WHERE table_name IN ('sapiones_vn_ward', 'frm_vn_ward')
    """)
    if cr.fetchone()[0] < 2:
        # Thiếu 1 trong 2 bảng (vd cài mới, greenfield) → không có gì để remap.
        return

    cr.execute("""
        UPDATE hr_employee e
        SET private_vn_ward_id = f.id
        FROM sapiones_vn_ward s
        JOIN frm_vn_ward f ON f.name = s.name AND f.state_id = s.state_id
        WHERE e.private_vn_ward_id = s.id
    """)
    remapped = cr.rowcount
    cr.execute("""
        UPDATE hr_employee
        SET private_vn_ward_id = NULL
        WHERE private_vn_ward_id IS NOT NULL
          AND private_vn_ward_id NOT IN (SELECT id FROM frm_vn_ward)
    """)
    _logger.info('l10n_vn_hr: remap private_vn_ward_id — khớp %s, null %s dòng.',
                 remapped, cr.rowcount)
