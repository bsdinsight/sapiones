# -*- coding: utf-8 -*-
"""Remap res.partner.vn_ward_id: sapiones.vn.ward (cũ) -> frm.vn.ward (bsd_vn_address).

CHẠY TRƯỚC khi Odoo đổi FK sang frm_vn_ward → tránh vỡ khóa ngoại. Khớp (name, state_id).
Không khớp → set NULL. Xem l10n_vn_hr/migrations cho field bên hr.employee.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        SELECT count(*) FROM information_schema.tables
        WHERE table_name IN ('sapiones_vn_ward', 'frm_vn_ward')
    """)
    if cr.fetchone()[0] < 2:
        return

    cr.execute("""
        UPDATE res_partner p
        SET vn_ward_id = f.id
        FROM sapiones_vn_ward s
        JOIN frm_vn_ward f ON f.name = s.name AND f.state_id = s.state_id
        WHERE p.vn_ward_id = s.id
    """)
    remapped = cr.rowcount
    cr.execute("""
        UPDATE res_partner
        SET vn_ward_id = NULL
        WHERE vn_ward_id IS NOT NULL
          AND vn_ward_id NOT IN (SELECT id FROM frm_vn_ward)
    """)
    _logger.info('l10n_vn_address: remap res_partner.vn_ward_id — khớp %s, null %s dòng.',
                 remapped, cr.rowcount)
