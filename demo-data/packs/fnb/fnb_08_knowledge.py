# -*- coding: utf-8 -*-
"""SEED DEMO F&B — Kho tri thức (chuỗi cà phê; bản chỉnh từ seed_knowledge_demo.py).

Danh mục phân cấp, thẻ, ~35 bài: nội quy, ca cửa hàng, nghỉ phép – lễ – ốm – thai sản, hợp đồng (kể cả
bán thời gian), kỷ luật, lương – thưởng – bảo hiểm – thuế TNCN, vận hành cửa hàng, ATTP – ATVSLĐ – PCCC,
hướng dẫn dùng Sapiones, hội nhập, hỏi đáp. Căn cứ ATTP/khám sức khoẻ tra ngày 27/11/2026
(NĐ 155/2018/NĐ-CP, Công văn 125/ATTP-NĐTT, Luật ATVSLĐ 2015 Điều 21); lương tối thiểu giờ NĐ 293/2025.
Vài bài nháp, vài bài "Chỉ nội bộ HR", bài con (hướng dẫn thao tác dưới bài chính sách).

Số liệu pháp luật theo Bộ luật Lao động 2019, Nghị định 145/2020, Luật BHXH, Nghị định 44/2016,
Nghị quyết 110/2025/UBTVQH15 (giảm trừ gia cảnh từ 2026). Quy chế riêng (giờ ca, ngày trả lương,
thưởng KPI, phụ cấp) là của CÔNG TY MẪU, khớp với dữ liệu demo (ca, loại nghỉ, đánh giá KPI tháng).

Chỉ là DỮ LIỆU MẪU. Chạy lại: bỏ qua nếu đã có hơn 5 bài viết.

Run (VPS):
  docker run ... odoo shell -d demo --no-http < demo-data/packs/seed_knowledge_demo.py
"""
import random

rnd = random.Random(20261133)
ctx = dict(tracking_disable=True, mail_notrack=True, mail_create_nolog=True)
Cat = env['sapiones.knowledge.category'].sudo()
Tag = env['sapiones.knowledge.tag'].sudo()
Art = env['sapiones.knowledge.article'].sudo().with_context(**ctx)

if Art.with_context(active_test=False).search_count([]) > 5:
    print('Đã seed kho tri thức trước đó — bỏ qua.')
    raise SystemExit

author = env['res.users'].sudo().search([('login', '=', 'demo')], limit=1) or env.user


def cat(name, parent=None, seq=10):
    c = Cat.search([('name', '=', name), ('parent_id', '=', parent.id if parent else False)], limit=1)
    return c or Cat.create({'name': name, 'parent_id': parent.id if parent else False, 'sequence': seq})


C_NQ = cat('Nội quy & chính sách', seq=10)
C_GIO = cat('Thời giờ làm việc', C_NQ, 10)
C_NGHI = cat('Nghỉ phép, nghỉ lễ, chế độ', C_NQ, 20)
C_HD = cat('Hợp đồng & kỷ luật', C_NQ, 30)
C_LUONG = cat('Lương, thưởng & phúc lợi', seq=20)
C_BH = cat('Bảo hiểm & thuế TNCN', C_LUONG, 10)
C_SX = cat('Vận hành cửa hàng', seq=30)
C_AT = cat('An toàn thực phẩm, lao động & PCCC', seq=40)
C_HDSD = cat('Hướng dẫn dùng Sapiones', seq=50)
C_NV = cat('Hội nhập nhân viên mới', seq=60)
C_FAQ = cat('Hỏi đáp nhân sự', seq=70)

TAGS = {}
for i, n in enumerate(['Bắt buộc đọc', 'Nhân viên mới', 'Cửa hàng', 'Quản lý', 'Luật lao động',
                       'Bảo hiểm', 'Thuế TNCN', 'An toàn', 'Cổng nhân viên', 'ATTP']):
    TAGS[n] = Tag.search([('name', '=', n)], limit=1) or Tag.create({'name': n, 'color': i + 1})


def ul(*items):
    return '<ul>%s</ul>' % ''.join('<li>%s</li>' % x for x in items)


def ol(*items):
    return '<ol>%s</ol>' % ''.join('<li>%s</li>' % x for x in items)


def table(head, *rows):
    th = ''.join('<th>%s</th>' % h for h in head)
    tr = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % c for c in r) for r in rows)
    return '<table class="table table-bordered"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (th, tr)


def h(t):
    return '<h3>%s</h3>' % t


def p(t):
    return '<p>%s</p>' % t


# (khoá, tiêu đề, danh mục, thẻ, tóm tắt, nội dung, tuỳ chọn)
A = []


def art(key, name, c, tags, summary, body, **opt):
    A.append((key, name, c, tags, summary, body, opt))


# ── Nội quy ─────────────────────────────────────────────
art('noiquy', 'Nội quy lao động (tóm tắt)', C_NQ, ['Bắt buộc đọc', 'Nhân viên mới', 'Luật lao động'],
    'Những điều mọi người cần tuân thủ: giờ giấc, đồng phục, vệ sinh, tiền két, thái độ phục vụ.',
    p('Nội quy lao động đầy đủ đã đăng ký với cơ quan quản lý lao động và niêm yết tại phòng nhân viên mỗi cửa hàng. '
      'Bài này tóm tắt các điểm chính.')
    + ul('Có mặt trước giờ vào ca 10 phút, chấm công khi vào và khi tan ca.',
         'Mặc đồng phục, đeo tạp dề, bảng tên; tóc gọn gàng, đội mũ/lưới trùm tóc khi đứng quầy pha chế và bếp.',
         'Rửa tay đúng quy trình trước khi vào quầy, sau khi đi vệ sinh, sau khi cầm tiền.',
         'Không dùng điện thoại cá nhân trong khu vực quầy và bếp; không ăn uống trong khu chế biến.',
         'Tiền két chỉ người được giao trong ca quản lý; kiểm két khi giao ca có hai người ký.',
         'Lịch sự với khách; mọi khiếu nại chuyển ca trưởng xử lý.')
    + p('Vi phạm nội quy được xử lý theo bài <b>Xử lý kỷ luật lao động</b>.'), seq=1, views=(180, 260))

art('gio', 'Thời giờ làm việc và ca cửa hàng', C_GIO, ['Bắt buộc đọc', 'Cửa hàng', 'Nhân viên mới'],
    'Ca sáng, ca chiều, ca gãy, ca bán thời gian 4 giờ; nghỉ giữa ca; nghỉ hằng tuần luân phiên.',
    table(['Ca', 'Giờ làm', 'Áp dụng'],
          ['Ca sáng cửa hàng', '06:00 – 14:00, nghỉ giữa ca 30 phút', 'Mở cửa hàng, barista, phụ bếp'],
          ['Ca chiều cửa hàng', '14:00 – 22:00, nghỉ giữa ca 30 phút', 'Đóng cửa hàng, ca trưởng'],
          ['Ca gãy', '10:00 – 14:00 và 17:00 – 21:00', 'Cửa hàng trưởng, giờ cao điểm trưa – tối'],
          ['Bán thời gian', '4 giờ: 07:00 – 11:00 hoặc 17:00 – 21:00', 'Sinh viên, nhân viên bán thời gian'],
          ['Hành chính', '08:00 – 17:00, nghỉ trưa 60 phút', 'Văn phòng'],
          ['Bếp trung tâm', '05:00 – 13:00', 'Sản xuất bánh, sốt cho các cửa hàng'])
    + p('Thời giờ làm việc bình thường không quá 8 giờ/ngày và 48 giờ/tuần (Điều 105 BLLĐ 2019). '
        'Cửa hàng mở cả cuối tuần nên ngày nghỉ hằng tuần được xếp luân phiên, mỗi tuần ít nhất 24 giờ liên tục (Điều 111).')
    + p('Làm việc từ 6 giờ/ngày trở lên được nghỉ giữa giờ ít nhất <b>30 phút</b> liên tục (Điều 109).')
    + p('Lịch ca từng tuần do cửa hàng trưởng xếp và đăng trước thứ Sáu; đổi ca phải được ca trưởng đồng ý.'),
    seq=1, views=(150, 230))

art('tangca', 'Làm thêm giờ: giới hạn và cách tính lương', C_GIO, ['Cửa hàng', 'Luật lao động'],
    'Tối đa 40 giờ/tháng, 200 giờ/năm; mức 150% / 200% / 300%; phụ trội ban đêm.',
    h('Điều kiện')
    + p('Làm thêm giờ phải có sự đồng ý của người lao động (Điều 107 BLLĐ 2019). '
        'Cửa hàng trưởng đăng ký giờ làm thêm trên hệ thống trước ca.')
    + h('Giới hạn')
    + ul('Không quá 50% số giờ làm việc bình thường trong ngày; tổng giờ làm bình thường + làm thêm không quá 12 giờ/ngày.',
         'Không quá 40 giờ/tháng.',
         'Không quá <b>200 giờ/năm</b>. Dịch vụ ăn uống không thuộc các ngành được làm thêm tới 300 giờ/năm '
         '(Điều 107 BLLĐ 2019, Điều 61 Nghị định 145/2020).')
    + h('Tiền lương làm thêm (Điều 98)')
    + table(['Thời điểm làm thêm', 'Mức tối thiểu'],
            ['Ngày thường', '150%'], ['Ngày nghỉ hằng tuần', '200%'],
            ['Ngày lễ, Tết, nghỉ có hưởng lương', '300% (chưa kể lương ngày lễ)'])
    + p('Làm việc vào ban đêm (22h – 6h) được trả thêm ít nhất 30% tiền lương.')
    + p('Phần tiền lương làm thêm giờ trả cao hơn so với làm việc bình thường được miễn thuế TNCN.'),
    seq=2, views=(120, 210))

art('phepnam', 'Nghỉ phép năm', C_NGHI, ['Bắt buộc đọc', 'Luật lao động'],
    '12 ngày phép/năm hưởng nguyên lương, cộng 1 ngày cho mỗi 5 năm làm việc; vào giữa năm tính theo tỷ lệ.',
    p('Người lao động làm đủ 12 tháng được nghỉ <b>12 ngày làm việc</b> hưởng nguyên lương '
      '(công việc nặng nhọc, độc hại: 14 ngày) — Điều 113 BLLĐ 2019.')
    + p('Cứ đủ <b>5 năm</b> làm việc được cộng thêm <b>1 ngày</b> (Điều 114). '
        'Người làm chưa đủ 12 tháng được nghỉ theo tỷ lệ số tháng làm việc.')
    + p('Công ty cấp phép năm vào đầu năm trên hệ thống; số ngày còn lại xem ở '
        '<b>Cổng nhân viên › Nghỉ phép</b>. Ngày phép chưa nghỉ hết được giải quyết theo quy chế của công ty.')
    + p('Nên đăng ký nghỉ phép dài ngày tránh dịp Tết, lễ 30/4 – 1/5 và 2/9 — mùa đông khách của cửa hàng.'), seq=1, views=(240, 380))

art('phep_hd', 'Hướng dẫn xin nghỉ phép trên Cổng nhân viên', C_HDSD, ['Cổng nhân viên', 'Cửa hàng'],
    'Các bước tạo đơn nghỉ phép, theo dõi duyệt, huỷ đơn.',
    ol('Mở <b>Cổng nhân viên</b> trên điện thoại hoặc máy tính, đăng nhập bằng tài khoản được cấp.',
       'Chọn <b>Nghỉ phép › Tạo đơn</b>; chọn loại nghỉ (phép năm, nghỉ ốm, việc riêng…).',
       'Chọn ngày bắt đầu – kết thúc; hệ thống tự trừ ngày nghỉ cuối tuần và báo số ngày phép còn lại.',
       'Ghi lý do, đính kèm giấy tờ nếu có (giấy khám bệnh, giấy đăng ký kết hôn…) rồi gửi.',
       'Quản lý duyệt hoặc từ chối; bạn nhận thông báo trên cổng.')
    + p('Đơn chưa duyệt có thể sửa hoặc huỷ. Đơn đã duyệt muốn huỷ thì báo quản lý.'),
    parent='phepnam', seq=5, views=(160, 300))

art('le', 'Nghỉ lễ, Tết', C_NGHI, ['Luật lao động'],
    'Các ngày nghỉ lễ, Tết hưởng nguyên lương theo Điều 112 BLLĐ 2019 và lịch nghỉ Tết của công ty.',
    p('Người lao động được nghỉ làm việc, hưởng nguyên lương trong các ngày lễ, Tết (Điều 112 BLLĐ 2019):')
    + ul('Tết Dương lịch: 1 ngày (01/01).', 'Tết Âm lịch: 5 ngày.', 'Ngày Chiến thắng: 1 ngày (30/4).',
         'Ngày Quốc tế lao động: 1 ngày (01/5).', 'Quốc khánh: 2 ngày (02/9 và 1 ngày liền kề trước hoặc sau).',
         'Giỗ Tổ Hùng Vương: 1 ngày (10/3 âm lịch).')
    + p('Lịch nghỉ cụ thể mỗi năm theo thông báo của cơ quan nhà nước và thông báo của Phòng Nhân sự. '
        'Lao động là người nước ngoài được nghỉ thêm 1 ngày Tết cổ truyền và 1 ngày Quốc khánh của nước họ.'),
    seq=2, views=(90, 170))

art('viecrieng', 'Nghỉ việc riêng có lương và nghỉ không lương', C_NGHI, ['Luật lao động'],
    'Kết hôn 3 ngày, con kết hôn 1 ngày, tang cha mẹ – vợ/chồng – con 3 ngày; nghỉ không lương theo thoả thuận.',
    h('Nghỉ việc riêng hưởng nguyên lương (Điều 115)')
    + table(['Trường hợp', 'Số ngày'],
            ['Bản thân kết hôn', '3 ngày'], ['Con đẻ, con nuôi kết hôn', '1 ngày'],
            ['Cha đẻ, mẹ đẻ, cha nuôi, mẹ nuôi (bố mẹ); cha mẹ của vợ/chồng; vợ hoặc chồng; con chết (mất)', '3 ngày'])
    + h('Nghỉ không hưởng lương')
    + p('Được nghỉ 1 ngày khi ông bà, anh chị em ruột chết; cha hoặc mẹ kết hôn; anh chị em ruột kết hôn '
        '(phải báo công ty). Ngoài ra có thể thoả thuận nghỉ không lương với quản lý.')
    + p('Tạo đơn trên cổng nhân viên với loại <b>Nghỉ việc riêng có lương</b> hoặc <b>Nghỉ không lương</b>.'),
    seq=3, views=(70, 140))

art('om', 'Nghỉ ốm và chế độ ốm đau BHXH', C_NGHI, ['Bảo hiểm'],
    'Thời gian hưởng chế độ ốm đau 30 / 40 / 60 ngày/năm theo số năm đóng BHXH, mức 75% lương đóng BHXH.',
    p('Người lao động đang đóng BHXH bị ốm, có xác nhận của cơ sở khám chữa bệnh, được hưởng chế độ ốm đau:')
    + table(['Thời gian đã đóng BHXH', 'Số ngày tối đa/năm (điều kiện bình thường)'],
            ['Dưới 15 năm', '30 ngày'], ['Từ 15 năm đến dưới 30 năm', '40 ngày'], ['Từ 30 năm trở lên', '60 ngày'])
    + p('Mức hưởng bằng <b>75%</b> tiền lương đóng BHXH của tháng gần nhất trước khi nghỉ. '
        'Số ngày tính theo ngày làm việc, không tính ngày lễ, Tết, nghỉ hằng tuần.')
    + p('Nộp <b>giấy chứng nhận nghỉ việc hưởng BHXH</b> cho Phòng Nhân sự trong tháng để kịp làm hồ sơ.'),
    seq=4, views=(85, 160))

art('thaisan', 'Chế độ thai sản (lao động nữ và nam)', C_NGHI, ['Bảo hiểm', 'Luật lao động'],
    'Nữ nghỉ sinh 6 tháng; nam nghỉ 5 – 14 ngày làm việc khi vợ sinh; khám thai; điều kiện hưởng.',
    h('Lao động nữ sinh con')
    + ul('Nghỉ trước và sau sinh <b>6 tháng</b>; thời gian nghỉ trước sinh không quá 2 tháng.',
         'Sinh đôi trở lên: từ con thứ hai, mỗi con được nghỉ thêm 1 tháng.',
         'Được nghỉ đi khám thai 5 lần, mỗi lần 1 ngày.',
         'Điều kiện: đóng BHXH từ đủ 6 tháng trở lên trong 12 tháng trước khi sinh.')
    + h('Lao động nam khi vợ sinh con')
    + table(['Trường hợp', 'Số ngày làm việc'],
            ['Sinh thường', '5 ngày'], ['Sinh phải phẫu thuật hoặc sinh con dưới 32 tuần tuổi', '7 ngày'],
            ['Sinh đôi', '10 ngày (thêm 3 ngày mỗi con từ con thứ ba)'], ['Sinh đôi phải phẫu thuật', '14 ngày'])
    + p('Lao động nam nghỉ trong vòng 60 ngày kể từ ngày vợ sinh (Luật BHXH 2024).')
    + p('Báo Phòng Nhân sự trước ngày dự sinh để chuẩn bị hồ sơ và bố trí người thay.'),
    seq=5, views=(60, 120))

art('hopdong', 'Thử việc và hợp đồng lao động', C_HD, ['Nhân viên mới', 'Luật lao động'],
    'Thời gian thử việc tối đa theo vị trí, lương thử việc tối thiểu 85%, hợp đồng toàn thời gian và bán thời gian.',
    h('Thời gian thử việc tối đa (Điều 25 BLLĐ 2019)')
    + table(['Công việc', 'Tối đa'],
            ['Người quản lý doanh nghiệp', '180 ngày'],
            ['Cần trình độ cao đẳng trở lên', '60 ngày'],
            ['Cần trình độ trung cấp, nhân viên nghiệp vụ', '30 ngày'],
            ['Công việc khác (phục vụ, thu ngân…)', '6 ngày làm việc'])
    + p('Lương thử việc ít nhất bằng <b>85%</b> mức lương của công việc đó (Điều 26). '
        'Hợp đồng dưới 1 tháng không áp dụng thử việc.')
    + h('Các loại hợp đồng tại công ty')
    + ul('Toàn thời gian: hợp đồng xác định thời hạn 12 tháng, sau đó 36 tháng; '
         'hợp đồng không xác định thời hạn sau khi đã ký 2 hợp đồng xác định thời hạn.',
         'Bán thời gian (Điều 32): hợp đồng 12 tháng, làm 4 giờ/ca, trả lương theo giờ thực làm; '
         'mức lương giờ không thấp hơn lương tối thiểu giờ của vùng (vùng I năm 2026: 25.500 đ/giờ — Nghị định 293/2025).',
         'Nhân viên bán thời gian được hưởng đủ các quyền như toàn thời gian theo tỷ lệ giờ làm: phép năm, BHXH khi đủ điều kiện.')
    + p('Phòng Nhân sự nhắc tái ký trước khi hợp đồng hết hạn 30 ngày.'), seq=1, views=(95, 170))

art('nghiviec', 'Nghỉ việc: thời hạn báo trước và thủ tục', C_HD, ['Luật lao động'],
    'Báo trước 45 / 30 / 3 ngày tuỳ loại hợp đồng; bàn giao, chốt sổ BHXH, quyết toán lương.',
    h('Thời hạn báo trước khi người lao động đơn phương chấm dứt hợp đồng (Điều 35)')
    + table(['Loại hợp đồng', 'Báo trước ít nhất'],
            ['Không xác định thời hạn', '45 ngày'], ['Xác định thời hạn từ 12 đến 36 tháng', '30 ngày'],
            ['Xác định thời hạn dưới 12 tháng', '3 ngày làm việc'])
    + h('Thủ tục')
    + ol('Nộp đơn nghỉ việc cho quản lý trực tiếp và Phòng Nhân sự.', 'Bàn giao công việc, dụng cụ, thẻ nhân viên.',
         'Phòng Nhân sự chốt công, quyết toán lương và các khoản trong vòng 14 ngày làm việc (Điều 48).',
         'Chốt sổ BHXH và trả lại giấy tờ cho người lao động.'), seq=2, views=(75, 150))

art('kyluat', 'Xử lý kỷ luật lao động', C_HD, ['Quản lý', 'Luật lao động'],
    '4 hình thức kỷ luật theo Điều 124, nguyên tắc và trình tự xử lý.',
    h('Hình thức xử lý (Điều 124 BLLĐ 2019)')
    + ol('Khiển trách.', 'Kéo dài thời hạn nâng lương không quá 6 tháng.', 'Cách chức.', 'Sa thải.')
    + h('Nguyên tắc')
    + ul('Công ty phải chứng minh được lỗi của người lao động.',
         'Phải có sự tham gia của tổ chức đại diện người lao động tại cơ sở mà người lao động là thành viên.',
         'Người lao động có quyền tự bào chữa hoặc nhờ người bào chữa.',
         'Không áp dụng nhiều hình thức kỷ luật cho một hành vi vi phạm; không phạt tiền, cắt lương thay cho kỷ luật.')
    + p('Cửa hàng trưởng ghi nhận vi phạm bằng biên bản và chuyển Phòng Nhân sự; không tự xử lý tại cửa hàng.'),
    seq=3, views=(40, 90))

# ── Lương, thưởng, phúc lợi ─────────────────────────────
art('luong', 'Quy chế trả lương và ngày trả lương', C_LUONG, ['Bắt buộc đọc', 'Cửa hàng'],
    'Kỳ lương theo tháng, trả qua tài khoản ngân hàng ngày 10 tháng sau; cách đọc phiếu lương.',
    ul('Kỳ công: từ ngày 1 đến cuối tháng; bảng công chốt vào ngày 3 tháng sau.',
       'Lương trả qua tài khoản ngân hàng vào <b>ngày 10</b> tháng sau; trùng ngày nghỉ thì trả ngày làm việc liền trước.',
       'Phiếu lương gồm: lương theo ngày công, làm thêm giờ, phụ cấp, thưởng KPI, các khoản trừ (BHXH, thuế TNCN, công đoàn).',
       'Thắc mắc về công, lương gửi Phòng Nhân sự trong 5 ngày kể từ ngày nhận phiếu lương.'),
    seq=1, views=(200, 320))

art('phieuluong_hd', 'Hướng dẫn xem phiếu lương trên Cổng nhân viên', C_HDSD, ['Cổng nhân viên'],
    'Xem, tải phiếu lương từng tháng và đối chiếu ngày công.',
    ol('Đăng nhập <b>Cổng nhân viên</b>, chọn <b>Phiếu lương</b>.', 'Chọn tháng cần xem; bấm vào phiếu để xem chi tiết từng khoản.',
       'Bấm <b>Tải PDF</b> để lưu hoặc in.', 'Đối chiếu ngày công ở mục <b>Chấm công</b>; sai lệch thì báo tổ trưởng trong 5 ngày.'),
    parent='luong', seq=5, views=(140, 260))

art('phucap', 'Phụ cấp và hỗ trợ', C_LUONG, ['Cửa hàng'],
    'Phụ cấp chuyên cần, xăng xe, ăn ca, đồng phục; điều kiện hưởng.',
    table(['Khoản', 'Mức (nhân viên toàn thời gian)', 'Điều kiện'],
          ['Chuyên cần', '500.000 đ/tháng', 'Đủ công trong tháng, không nghỉ không phép, không trễ ca quá 2 lần'],
          ['Xăng xe', '300.000 đ/tháng', 'Nhân viên toàn thời gian'],
          ['Ăn ca', '730.000 đ/tháng', 'Mỗi ca làm việc thực tế'],
          ['Đồng phục', '2 bộ/năm', 'Cấp khi vào làm và đầu năm'])
    + p('Nhân viên bán thời gian được ăn nhẹ tại cửa hàng trong ca và hưởng thưởng doanh thu cửa hàng theo giờ làm.'),
    seq=2, views=(110, 190))

art('kpi_thuong', 'Quy chế thưởng KPI tháng', C_LUONG, ['Quản lý'],
    '(Nội bộ HR) Xếp loại KPI tháng và hệ số thưởng tương ứng.',
    p('Thưởng KPI tháng tính trên kết quả <b>phiếu đánh giá KPI</b> đã hoàn tất của tháng đó.')
    + table(['Điểm tổng', 'Xếp loại', 'Hệ số thưởng'],
            ['Từ 90', 'Xuất sắc', '1,2'], ['80 – dưới 90', 'Tốt', '1,0'], ['65 – dưới 80', 'Khá', '0,8'],
            ['50 – dưới 65', 'Đạt', '0,5'], ['Dưới 50', 'Chưa đạt', '0'])
    + p('Quỹ thưởng tháng do Ban Giám đốc duyệt theo doanh thu và lợi nhuận cửa hàng. Tài liệu này chỉ dành cho HR và quản lý.'),
    internal=True, seq=3, views=(30, 60))

art('kpi_qt', 'Quy trình đánh giá KPI hằng tháng', C_LUONG, ['Quản lý', 'Cửa hàng'],
    '4 bước: tạo phiếu – nhân viên tự đánh giá – quản lý đánh giá – hoàn tất; mốc thời gian mỗi tháng.',
    ol('<b>Ngày 25</b>: Phòng Nhân sự tạo đợt KPI tháng, hệ thống sinh phiếu cho từng nhân viên kèm bộ chỉ tiêu theo vị trí.',
       '<b>Ngày 25 – 28</b>: nhân viên nhập kết quả thực tế và tự chấm điểm, gửi tự đánh giá.',
       '<b>Đến ngày 2 tháng sau</b>: quản lý trực tiếp chấm điểm từng chỉ tiêu và nhận xét.',
       '<b>Ngày 3</b>: hoàn tất phiếu; điểm tổng và xếp loại chuyển sang tính thưởng KPI.')
    + p('Chỉ tiêu barista/phục vụ: thời gian ra món, tỷ lệ làm lại món, điểm khách bí mật, chuyên cần. '
        'Cửa hàng trưởng: doanh thu, chi phí nguyên liệu, chi phí nhân công, điểm kiểm tra vệ sinh – ATTP, tỷ lệ nghỉ việc.'),
    seq=4, views=(80, 150))

art('bhxh', 'Mức đóng BHXH, BHYT, BHTN', C_BH, ['Bảo hiểm', 'Bắt buộc đọc'],
    'Người lao động đóng 10,5%; công ty đóng 21,5% cộng kinh phí công đoàn 2%.',
    table(['Khoản', 'Người lao động', 'Công ty'],
          ['BHXH (hưu trí, tử tuất; ốm đau, thai sản; TNLĐ-BNN)', '8%', '17,5%'],
          ['BHYT', '1,5%', '3%'], ['BHTN', '1%', '1%'], ['Tổng', '<b>10,5%</b>', '<b>21,5%</b>'])
    + p('Tỷ lệ tính trên tiền lương tháng đóng BHXH ghi trong hợp đồng. '
        'Công ty đóng thêm kinh phí công đoàn 2% quỹ lương đóng BHXH. '
        'Tra cứu quá trình đóng trên ứng dụng VssID.'), seq=1, views=(130, 220))

art('giamtru', 'Giảm trừ gia cảnh và đăng ký người phụ thuộc', C_BH, ['Thuế TNCN'],
    'Từ kỳ tính thuế 2026: bản thân 15,5 triệu đồng/tháng, mỗi người phụ thuộc 6,2 triệu đồng/tháng.',
    p('Theo Nghị quyết 110/2025/UBTVQH15, áp dụng từ kỳ tính thuế năm 2026:')
    + ul('Giảm trừ cho bản thân người nộp thuế: <b>15,5 triệu đồng/tháng</b>.',
         'Giảm trừ cho mỗi người phụ thuộc: <b>6,2 triệu đồng/tháng</b>.')
    + h('Đăng ký người phụ thuộc')
    + ol('Điền mẫu đăng ký người phụ thuộc, kèm giấy khai sinh (con) hoặc giấy tờ chứng minh quan hệ.',
         'Nộp Phòng Nhân sự; công ty đăng ký mã số người phụ thuộc với cơ quan thuế.',
         'Người phụ thuộc được giảm trừ từ tháng phát sinh nghĩa vụ nuôi dưỡng.')
    + p('Mỗi người phụ thuộc chỉ được tính giảm trừ cho một người nộp thuế.'), seq=2, views=(150, 260))

art('quyettoan', 'Quyết toán thuế TNCN cuối năm', C_BH, ['Thuế TNCN'],
    'Khi nào uỷ quyền công ty quyết toán, khi nào tự quyết toán; giấy tờ cần nộp.',
    ul('Có hợp đồng từ 3 tháng trở lên và đang làm việc tại thời điểm quyết toán: có thể <b>uỷ quyền công ty</b> quyết toán.',
       'Có thêm thu nhập từ nơi khác (trừ thu nhập vãng lai bình quân tháng không quá 10 triệu đồng đã khấu trừ 10%): tự quyết toán.',
       'Nộp mẫu uỷ quyền quyết toán cho Phòng Nhân sự trước hạn thông báo hằng năm.')
    + p('Chứng từ khấu trừ thuế TNCN do công ty cấp dạng điện tử.'), seq=3, views=(60, 130))

# ── Sản xuất & chất lượng ───────────────────────────────
art('moca', 'Quy trình mở ca và đóng ca', C_SX, ['Cửa hàng', 'Bắt buộc đọc'],
    'Checklist mở cửa hàng, giao ca và đóng cửa hàng; ai ký, ghi vào đâu.',
    h('Mở ca (ca sáng, 06:00)')
    + ol('Kiểm tra nhiệt độ tủ mát (≤ 5°C) và tủ đông (≤ -18°C), ghi sổ nhiệt độ.',
         'Bật máy pha espresso, xả nước nhóm pha, chạy thử 2 shot; kiểm tra máy xay.',
         'Kiểm nguyên liệu, nhận hàng bếp trung tâm giao, kiểm hạn dùng (vào trước – ra trước).',
         'Nhận tiền lẻ đầu ca, ký sổ két.', 'Vệ sinh quầy, bàn ghế, khu vực khách.')
    + h('Giao ca')
    + ul('Đếm két với ca sau, hai người cùng ký.', 'Bàn giao đơn đang làm, nguyên liệu sắp hết, sự cố trong ca.')
    + h('Đóng ca (22:00)')
    + ol('Kết ca trên máy bán hàng, đếm két, nộp tiền vào két sắt.', 'Vệ sinh máy pha, ngâm phin lọc, đổ bã.',
         'Huỷ nguyên liệu đã mở quá hạn dùng trong ngày, ghi sổ huỷ.', 'Tắt điện, khoá gas, khoá cửa, gửi báo cáo ca.'),
    seq=1, views=(160, 260))

art('congthuc', 'Công thức chuẩn và định lượng', C_SX, ['Cửa hàng', 'ATTP'],
    'Pha chế đúng công thức chuẩn, cân định lượng, nhãn ngày mở nguyên liệu.',
    ul('Mỗi món có thẻ công thức: định lượng cà phê, sữa, đường, đá, thời gian chiết xuất.',
       'Dùng cân và ly định lượng; không ước lượng bằng mắt.',
       'Nguyên liệu đã mở phải dán nhãn ngày giờ mở và hạn dùng; bỏ khi quá hạn.',
       'Món mới chỉ bán khi cửa hàng trưởng đã kiểm tra nhân viên làm đạt.')
    + p('Đúng định lượng giúp vị đồng đều giữa các cửa hàng và kiểm soát chi phí nguyên liệu.'), seq=2, views=(120, 210))

art('khieunai', 'Xử lý khiếu nại của khách', C_SX, ['Cửa hàng'],
    'Lắng nghe – xin lỗi – xử lý – ghi nhận; khi nào làm lại món, khi nào báo cửa hàng trưởng.',
    ol('Lắng nghe hết ý khách, không ngắt lời, không tranh cãi.',
       'Xin lỗi về trải nghiệm chưa tốt.',
       'Món không đạt: làm lại ngay hoặc đổi món khác; ghi vào sổ làm lại món.',
       'Khách phản ánh về vệ sinh, dị vật, sức khoẻ: báo ngay ca trưởng/cửa hàng trưởng, giữ mẫu món.',
       'Ghi nhận khiếu nại trong báo cáo ca để cửa hàng trưởng theo dõi.'),
    seq=3, views=(90, 170))

art('kiemke', 'Kiểm kê cuối ngày và chênh lệch két', C_SX, ['Cửa hàng', 'Quản lý'],
    'Kiểm kê nguyên liệu chính mỗi tối, kiểm kê toàn bộ cuối tháng; xử lý chênh lệch két.',
    table(['Việc', 'Tần suất', 'Người làm'],
          ['Kiểm cà phê hạt, sữa, nguyên liệu chính', 'Mỗi tối khi đóng ca', 'Ca trưởng'],
          ['Kiểm kê toàn bộ kho cửa hàng', 'Ngày cuối tháng', 'Cửa hàng trưởng + nhân viên kho'],
          ['Đối soát doanh thu với ngân hàng', 'Hằng ngày', 'Kế toán'])
    + p('Chênh lệch két trên 0,1% doanh thu ca phải lập biên bản ngay trong ca. '
        'Chênh lệch kho và két là chỉ tiêu trong KPI tháng của ca trưởng và cửa hàng trưởng.'),
    seq=4, views=(50, 110))

# ── An toàn ─────────────────────────────────────────────
art('atvsld', 'Huấn luyện an toàn, vệ sinh lao động định kỳ', C_AT, ['An toàn', 'Bắt buộc đọc', 'Luật lao động'],
    '6 nhóm đối tượng huấn luyện theo Nghị định 44/2016, chu kỳ huấn luyện lại, chứng chỉ trên hồ sơ.',
    table(['Nhóm', 'Đối tượng', 'Huấn luyện định kỳ'],
          ['1', 'Người quản lý phụ trách công tác ATVSLĐ', 'Ít nhất 2 năm/lần'],
          ['2', 'Người làm công tác ATVSLĐ', 'Ít nhất 2 năm/lần'],
          ['3', 'Người làm công việc có yêu cầu nghiêm ngặt về ATVSLĐ', 'Ít nhất 2 năm/lần'],
          ['4', 'Người lao động còn lại (nhân viên cửa hàng, bếp, văn phòng…)', 'Ít nhất 1 năm/lần'],
          ['5', 'Người làm công tác y tế', 'Ít nhất 2 năm/lần'],
          ['6', 'An toàn, vệ sinh viên', 'Ít nhất 1 năm/lần'])
    + p('Kết quả huấn luyện lưu ở tab <b>Chứng chỉ</b> trên hồ sơ nhân viên; '
        'hệ thống nhắc Phòng Nhân sự trước khi hết hạn 60 ngày.'), seq=1, views=(100, 190))

art('attp', 'An toàn thực phẩm: tập huấn và sức khoẻ người chế biến', C_AT, ['ATTP', 'Bắt buộc đọc', 'Nhân viên mới'],
    'Mọi người tiếp xúc thực phẩm phải được tập huấn kiến thức ATTP và khám sức khoẻ định kỳ.',
    h('Tập huấn kiến thức ATTP')
    + p('Chủ cơ sở tự tổ chức tập huấn kiến thức ATTP cho người trực tiếp chế biến, phục vụ và xác nhận danh sách người '
        'đã được tập huấn (Nghị định 155/2018/NĐ-CP sửa Nghị định 15/2018/NĐ-CP). Công ty tập huấn trong tuần đầu cho '
        'nhân viên mới; kết quả lưu ở tab <b>Chứng chỉ</b>.')
    + h('Sức khoẻ')
    + ul('Khám sức khoẻ định kỳ ít nhất <b>1 lần/năm</b> (Luật An toàn, vệ sinh lao động 2015, Điều 21).',
         'Người đang mắc tả, lỵ, thương hàn, viêm gan A, viêm gan E, viêm da nhiễm trùng, lao phổi, tiêu chảy cấp '
         'không được trực tiếp chế biến, phục vụ cho đến khi khỏi bệnh.',
         'Có triệu chứng sốt, tiêu chảy, vết thương hở ở tay: báo ca trưởng để đổi việc trong ngày.')
    + p('Đoàn kiểm tra có thể yêu cầu xem danh sách tập huấn và giấy khám sức khoẻ — hồ sơ lấy trực tiếp từ hệ thống.'),
    seq=2, views=(140, 240))

art('quytac', '5 quy tắc an toàn tại quầy và bếp', C_AT, ['An toàn', 'Cửa hàng', 'Nhân viên mới'],
    'Hơi nóng máy pha, nước sôi, dao, sàn trơn, gas và điện — năm nguy cơ thường gặp.',
    ol('Không chạm vòi đánh sữa, nhóm pha khi máy đang chạy; dùng khăn cách nhiệt.',
       'Rót nước sôi, dầu nóng bằng bình có tay cầm; không bê nồi nóng qua lối khách.',
       'Dao để đúng giá, lưỡi quay vào trong; dùng găng chống cắt khi thái số lượng lớn.',
       'Lau ngay sàn ướt, đặt biển cảnh báo; mang giày chống trơn trong bếp.',
       'Khoá van gas sau ca; không chạm thiết bị điện bằng tay ướt; báo ngay khi ngửi thấy mùi gas.'),
    seq=3, views=(130, 230))

art('pccc', 'Phòng cháy chữa cháy và thoát hiểm', C_AT, ['An toàn', 'Bắt buộc đọc'],
    'Nguy cơ cháy ở bếp gas, dầu, thiết bị điện; cách dùng bình chữa cháy và chăn chữa cháy; thoát hiểm cùng khách.',
    p('Bếp gas, chảo dầu và ổ điện máy pha là nguồn cháy chính của cửa hàng. Cháy chảo dầu: tắt bếp, phủ chăn chữa cháy, '
      'tuyệt đối không dùng nước. Mọi người phải biết vị trí bình, chăn chữa cháy và lối thoát gần nhất.')
    + h('Sử dụng bình chữa cháy')
    + ol('Rút chốt an toàn.', 'Hướng loa phun vào gốc lửa, đứng đầu hướng gió.', 'Bóp van, quét qua lại gốc lửa.')
    + h('Khi có hiệu lệnh báo cháy')
    + ul('Khoá gas, ngắt điện khu bếp; hướng dẫn khách ra theo lối thoát hiểm, không quay lại lấy đồ.',
         'Tập trung tại điểm tập kết; ca trưởng điểm danh nhân viên, báo cáo đội PCCC cơ sở.')
    + p('Công ty tổ chức diễn tập PCCC ít nhất mỗi năm một lần.'), seq=3, views=(90, 160))

art('socuu', 'Sơ cứu khi bỏng hơi nóng, đứt tay, trượt ngã', C_AT, ['An toàn', 'Cửa hàng'],
    'Xử lý ban đầu các tai nạn nhỏ thường gặp ở quầy và bếp; tủ thuốc và người sơ cứu ở mỗi cửa hàng.',
    h('Bỏng hơi nóng, nước sôi')
    + ul('Xả nước mát 15 – 20 phút, tháo nhẫn, đồng hồ; không bôi kem đánh răng, không chọc vỡ bọng nước.')
    + h('Đứt tay do dao') + ul('Ép chặt vết thương bằng gạc sạch, giơ cao tay; băng kín, đeo găng trước khi làm tiếp.')
    + h('Trượt ngã') + ul('Không tự đứng dậy nếu đau nhiều ở lưng, cổ; báo ca trưởng, gọi cấp cứu khi cần.')
    + p('Mỗi cửa hàng có tủ thuốc và người đã được huấn luyện sơ cấp cứu (danh sách dán tại tủ thuốc). '
        'Mọi tai nạn đều phải báo ca trưởng để ghi sổ.'), seq=5, views=(60, 120))

# ── Hướng dẫn Sapiones ──────────────────────────────────
art('chamcong', 'Hướng dẫn chấm công và xử lý quên chấm công', C_HDSD, ['Cổng nhân viên', 'Cửa hàng', 'Nhân viên mới'],
    'Chấm công khi vào và tan ca tại cửa hàng, xem công trên cổng, gửi yêu cầu điều chỉnh khi quên chấm.',
    ol('Chấm công trên máy tại cửa hàng khi vào ca và khi tan ca; chờ máy báo thành công.',
       'Xem công từng ngày ở <b>Cổng nhân viên › Chấm công</b>.',
       'Quên chấm: báo ca trưởng trong ngày để xác nhận và điều chỉnh công.',
       'Bảng công tháng chốt ngày 3 tháng sau; nhân viên bán thời gian đối chiếu số giờ làm trước ngày này.'),
    seq=1, views=(170, 280))

art('hoi_ai', 'Hỏi Trợ lý tri thức', C_HDSD, ['Cổng nhân viên'],
    'Đặt câu hỏi bằng tiếng Việt, trợ lý tìm và tóm tắt câu trả lời từ kho tri thức của công ty.',
    p('Mở <b>Kho tri thức › Hỏi Trợ lý AI</b>, gõ câu hỏi như cách hỏi đồng nghiệp — '
      'về phép, lương, bảo hiểm, ca làm, quy trình cửa hàng hay an toàn thực phẩm.')
    + p('Trợ lý chỉ trả lời dựa trên bài viết đã đăng trong kho và luôn kèm bài viết nguồn để đối chiếu. '
        'Câu hỏi về trường hợp riêng, hãy liên hệ Phòng Nhân sự.'), seq=3, views=(120, 210))

# ── Hội nhập ────────────────────────────────────────────
art('tuandau', 'Cẩm nang tuần đầu tiên cho nhân viên mới', C_NV, ['Nhân viên mới', 'Bắt buộc đọc'],
    'Việc cần làm trong tuần đầu: hồ sơ, đồng phục, tập huấn ATTP, ca kèm cặp, tài khoản cổng nhân viên.',
    table(['Ngày', 'Việc'],
          ['Ngày 1', 'Nộp hồ sơ (CCCD, sơ yếu lý lịch, giấy khám sức khoẻ, số BHXH nếu có); nhận đồng phục, tạp dề, bảng tên'],
          ['Ngày 1', 'Nhận tài khoản Cổng nhân viên; xem lịch ca tuần đầu'],
          ['Ngày 2', 'Tập huấn ATTP, ATVSLĐ, PCCC và nội quy tại cửa hàng'],
          ['Ngày 2 – 5', 'Làm ca kèm cặp với barista chính; học quy trình mở/đóng ca và 10 món bán chạy'],
          ['Cuối tuần', 'Gặp cửa hàng trưởng đánh giá tuần đầu, chốt lịch ca tháng'])
    + p('Đọc trước các bài có thẻ <b>Nhân viên mới</b> trong kho tri thức.'), seq=1, views=(140, 240))

art('sodo', 'Sơ đồ tổ chức và người liên hệ', C_NV, ['Nhân viên mới'],
    'Khối vận hành, cửa hàng, bếp trung tâm và các phòng; gặp ai khi cần.',
    table(['Việc cần hỏi', 'Liên hệ'],
          ['Lịch ca, đổi ca', 'Ca trưởng, cửa hàng trưởng'], ['Công, lương, phép, bảo hiểm', 'Phòng Nhân sự & Đào tạo'],
          ['Thiếu nguyên liệu, hàng giao trễ', 'Mua hàng & Kho'], ['Vệ sinh, ATTP, khách phản ánh sức khoẻ', 'QA An toàn thực phẩm'],
          ['Máy pha hỏng, điện nước', 'Cửa hàng trưởng (gọi đơn vị bảo trì)'])
    + p('Sơ đồ tổ chức cập nhật xem trong ứng dụng <b>Nhân viên › Sơ đồ tổ chức</b>.'), seq=2, views=(80, 150))

art('faq', 'Câu hỏi thường gặp về công, lương, phép', C_FAQ, ['Cửa hàng', 'Nhân viên mới'],
    'Giải đáp nhanh các thắc mắc hay gặp nhất của người lao động.',
    h('Nghỉ ốm có bị trừ phép năm không?')
    + p('Không. Nghỉ ốm có giấy của cơ sở y tế được hưởng chế độ ốm đau BHXH, không trừ phép năm.')
    + h('Đang thử việc có được nghỉ phép năm không?')
    + p('Thời gian thử việc được tính vào thời gian làm việc để tính phép năm nếu tiếp tục làm việc sau thử việc.')
    + h('Làm thêm vào ngày nghỉ hằng tuần tính thế nào?')
    + p('Ngày nghỉ hằng tuần của bạn là ngày ghi trên lịch ca (không nhất thiết Chủ nhật). Làm thêm vào ngày đó: '
        'ít nhất 200% lương giờ. Xem bài <b>Làm thêm giờ</b>.')
    + h('Làm bán thời gian có được đóng BHXH, nghỉ phép không?')
    + p('Có. Hợp đồng bán thời gian từ 1 tháng trở lên tham gia BHXH bắt buộc khi đủ điều kiện về mức lương; '
        'phép năm tính theo tỷ lệ giờ làm. Xem bài <b>Thử việc và hợp đồng lao động</b>.')
    + h('Đổi số tài khoản nhận lương?')
    + p('Gửi Phòng Nhân sự bản sao thông tin tài khoản đứng tên chính mình trước ngày 3 hằng tháng.'),
    seq=1, views=(210, 340))

# ── Nháp ────────────────────────────────────────────────
art('caodiem', 'Kế hoạch nhân sự cao điểm Tết (dự thảo)', C_GIO, ['Quản lý'],
    'Dự thảo bổ sung nhân viên bán thời gian và giờ làm thêm cho 6 tuần cao điểm Tết, trong giới hạn 200 giờ/năm.',
    p('Dự thảo đang lấy ý kiến cửa hàng trưởng: tuyển thêm bán thời gian theo doanh thu dự kiến từng cửa hàng, '
      'xếp ca gãy cho giờ cao điểm, theo dõi luỹ kế giờ làm thêm để không vượt 40 giờ/tháng và 200 giờ/năm.'),
    draft=True, internal=True, seq=9)

art('tuyendung', 'Quy trình tuyển bán thời gian hàng loạt (dự thảo)', C_HD, ['Quản lý'],
    'Dự thảo: đăng tin, mã QR tại quầy, phỏng vấn nhóm, làm thử 1 ca, tập huấn ATTP trước ca đầu.',
    p('Dự thảo: nhận hồ sơ qua link ứng tuyển và mã QR dán tại quầy, cửa hàng trưởng phỏng vấn nhóm cuối tuần, '
      'làm thử 1 ca có trả lương, ký hợp đồng bán thời gian, tập huấn ATTP trước ca đầu tiên.'), draft=True, internal=True, seq=9)

# ── Tạo bản ghi ─────────────────────────────────────────
recs = {}
for key, name, c, tags, summary, body, opt in A:
    lo, hi = opt.get('views', (0, 0))
    recs[key] = Art.create({
        'name': name, 'category_id': c.id, 'summary': summary, 'body': body,
        'tag_ids': [(6, 0, [TAGS[t].id for t in tags])], 'author_id': author.id,
        'state': 'draft' if opt.get('draft') else 'published', 'is_internal': opt.get('internal', False),
        'sequence': opt.get('seq', 10), 'view_count': rnd.randint(lo, hi) if hi else 0})
for key, name, c, tags, summary, body, opt in A:
    if opt.get('parent'):
        recs[key].parent_id = recs[opt['parent']]
env.cr.commit()

print('Danh mục:', Cat.search_count([]), '— thẻ:', Tag.search_count([]))
print('Bài viết:', Art.search_count([]), '— đã đăng:', Art.search_count([('state', '=', 'published')]),
      '— trên cổng NV:', Art.search_count([('state', '=', 'published'), ('is_internal', '=', False)]))
