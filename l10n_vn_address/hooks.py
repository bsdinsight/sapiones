"""Tự nạp 3321 phường/xã khi cài module, khớp vào 34 tỉnh có sẵn trong res.country.state.

Chỉ ghi vào bảng sapiones.vn.ward (không sửa res.country.state) → an toàn, idempotent
theo (state_id, name). Khớp tỉnh theo tên chuẩn hoá: NFC + lowercase + bỏ tiền tố
('thủ đô', 'thành phố', 'tỉnh'...). ALIAS xử lý Huế (mới) ↔ Thừa Thiên - Huế (cũ).
"""
import json
import logging
import os
import unicodedata

_logger = logging.getLogger(__name__)

_PREFIXES = ['thủ đô ', 'thành phố ', 'tp. ', 'tp ', 'tỉnh ']
ALIASES = {
    'huế': 'thừa thiên - huế',
    'thừa thiên - huế': 'huế',
}


def _norm(s):
    s = unicodedata.normalize('NFC', (s or '').strip().lower())
    for p in _PREFIXES:
        if s.startswith(p):
            s = s[len(p):]
    return s.strip()


def post_init_hook(env):
    Ward = env['sapiones.vn.ward']
    vn = env['res.country'].search([('code', '=', 'VN')], limit=1)
    if not vn:
        _logger.warning('l10n_vn_address: không tìm thấy quốc gia VN, bỏ qua seed.')
        return

    states = env['res.country.state'].search([('country_id', '=', vn.id)])
    by_norm = {}
    for s in states:
        by_norm.setdefault(_norm(s.name), s)

    def find_state(province_name):
        k = _norm(province_name)
        if k in by_norm:
            return by_norm[k]
        if k in ALIASES and ALIASES[k] in by_norm:
            return by_norm[ALIASES[k]]
        return None

    path = os.path.join(os.path.dirname(__file__), 'data', 'wards.json')
    with open(path, encoding='utf-8') as fh:
        wards = json.load(fh)

    existing = {(w.state_id.id, (w.name or '').strip()) for w in Ward.search([])}
    to_create, unmatched = [], {}
    for w in wards:
        name = (w.get('ten') or '').strip()
        prov = w.get('provinceName') or ''
        st = find_state(prov)
        if not st:
            unmatched[prov] = unmatched.get(prov, 0) + 1
            continue
        key = (st.id, name)
        if key in existing:
            continue
        existing.add(key)
        to_create.append({
            'name': name,
            'code': str(w.get('stt') or '').strip(),
            'state_id': st.id,
        })

    if to_create:
        Ward.create(to_create)
    if unmatched:
        _logger.warning('l10n_vn_address: %d xã chưa khớp tỉnh: %s',
                        sum(unmatched.values()), dict(unmatched))
    _logger.info('l10n_vn_address: đã tạo %d phường/xã (tổng hiện có %d).',
                 len(to_create), Ward.search_count([]))
