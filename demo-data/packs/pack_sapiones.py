# -*- coding: utf-8 -*-
"""KNOWLEDGE PACK — Sapiones (HR/HCM).

Dữ liệu DÙNG CHUNG ship cho MỌI tenant (BSD xây 1 lần). Chạy trên **DB TEMPLATE**
`sapiones_tpl` (sau khi đã cài module, KHÔNG demo) → rồi clone template cho từng khách.
Khách mở app là có sẵn chức danh / ca / loại nghỉ / loại chứng chỉ để dùng ngay.

CHỈ tạo dữ liệu DANH MỤC nền (không nhân viên/phiếu lương/hồ sơ thật).
Idempotent — chạy lại không nhân đôi (tra theo tên/mã). Defensive — field/model
thiếu thì bỏ qua, KHÔNG làm hỏng template.

Run (trên DB template):
    docker compose -f docker-compose.vps.yml exec -T odoo bash -lc '
      odoo shell -d sapiones_tpl --db_host="$HOST" --db_user="$USER" \
        --db_password="$PASSWORD" --no-http' < demo-data/packs/pack_sapiones.py
"""

JOBS = ['Công nhân may', 'Tổ trưởng chuyền', 'Nhân viên QC', 'Quản đốc xưởng',
        'Nhân viên kinh doanh', 'Kế toán', 'Chuyên viên nhân sự', 'Nhân viên kho']

SHIFTS = [  # (tên, mã, giờ bắt đầu, giờ kết thúc)
    ('Ca sáng', 'CA-S', 6.0, 14.0),
    ('Ca chiều', 'CA-C', 14.0, 22.0),
    ('Ca đêm', 'CA-D', 22.0, 6.0),
    ('Giờ hành chính', 'HC', 8.0, 17.5),
]

LEAVE_TYPES = ['Nghỉ phép năm', 'Nghỉ ốm', 'Nghỉ không lương',
               'Nghỉ việc riêng có lương', 'Nghỉ chế độ thai sản']

CERT_TYPES = [  # (tên, mã, bắt buộc)
    ('An toàn lao động (ATLĐ)', 'ATLD', True),
    ('Phòng cháy chữa cháy (PCCC)', 'PCCC', True),
    ('Vận hành máy may công nghiệp', 'VHMM', False),
    ('Sơ cấp cứu', 'SCC', False),
]


def run(env):
    print("=" * 64)
    print("KNOWLEDGE PACK — Sapiones (HR danh mục nền, no demo)")
    print("=" * 64)

    def fields_ok(model, vals):
        f = env[model]._fields
        return {k: v for k, v in vals.items() if k in f}

    def ensure(model, domain, vals):
        if model not in env:
            return None
        try:
            rec = env[model].search(domain, limit=1)
            if not rec:
                rec = env[model].create(fields_ok(model, vals))
            return rec
        except Exception as e:
            print("  ⚠ bỏ qua %s %r: %s" % (model, vals.get('name'), e))
            return None

    n = 0
    for nm in JOBS:
        if ensure('hr.job', [('name', '=', nm)], {'name': nm}):
            n += 1
    print("  ✓ Chức danh (hr.job): %d" % n)

    n = 0
    for nm, code, ts, te in SHIFTS:
        if ensure('sapiones.shift', ['|', ('code', '=', code), ('name', '=', nm)],
                  {'name': nm, 'code': code, 'time_start': ts, 'time_end': te}):
            n += 1
    print("  ✓ Ca làm việc (sapiones.shift): %d" % n)

    n = 0
    for nm in LEAVE_TYPES:
        if ensure('hr.leave.type', [('name', '=', nm)], {'name': nm}):
            n += 1
    print("  ✓ Loại nghỉ (hr.leave.type): %d" % n)

    n = 0
    for nm, code, mand in CERT_TYPES:
        if ensure('sapiones.hr.certificate.type', ['|', ('code', '=', code), ('name', '=', nm)],
                  {'name': nm, 'code': code, 'is_mandatory': mand}):
            n += 1
    print("  ✓ Loại chứng chỉ (sapiones.hr.certificate.type): %d" % n)

    env.cr.commit()
    print("\n✅ PACK DONE — template đã có danh mục HR nền. KHÔNG có demo.")


run(env)
