# -*- coding: utf-8 -*-
"""SEED DEMO — Kho tri thức cho demo (công ty may mặc).

Danh mục phân cấp, thẻ, ~30 bài: nội quy, thời giờ làm việc / ca, nghỉ phép – lễ – ốm – thai sản,
hợp đồng & nghỉ việc, kỷ luật, lương – thưởng – bảo hiểm – thuế TNCN, sản xuất & chất lượng,
ATVSLĐ & PCCC, hướng dẫn dùng cổng nhân viên Sapiones, hội nhập, hỏi đáp.
Vài bài nháp, vài bài "Chỉ nội bộ HR", bài con (hướng dẫn thao tác dưới bài chính sách).

Số liệu pháp luật theo Bộ luật Lao động 2019, Nghị định 145/2020, Luật BHXH, Nghị định 44/2016,
Nghị quyết 110/2025/UBTVQH15 (giảm trừ gia cảnh từ 2026). Quy chế riêng (giờ ca, ngày trả lương,
thưởng KPI, phụ cấp) là của CÔNG TY MẪU, khớp với dữ liệu demo (ca, loại nghỉ, đánh giá KPI tháng).

Chỉ là DỮ LIỆU MẪU. Chạy lại: bỏ qua nếu đã có hơn 5 bài viết.

Run (VPS):
  docker run ... odoo shell -d demo --no-http < demo-data/packs/seed_knowledge_demo.py
"""
import random

rnd = random.Random(20261129)
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
C_SX = cat('Sản xuất & chất lượng', seq=30)
C_AT = cat('An toàn lao động & PCCC', seq=40)
C_HDSD = cat('Hướng dẫn dùng Sapiones', seq=50)
C_NV = cat('Hội nhập nhân viên mới', seq=60)
C_FAQ = cat('Hỏi đáp nhân sự', seq=70)

TAGS = {}
for i, n in enumerate(['Bắt buộc đọc', 'Nhân viên mới', 'Công nhân', 'Quản lý', 'Luật lao động',
                       'Bảo hiểm', 'Thuế TNCN', 'An toàn', 'Cổng nhân viên', 'Chất lượng']):
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
    'Những điều mọi người lao động cần tuân thủ: giờ giấc, tác phong, tài sản, an toàn.',
    p('Nội quy lao động đầy đủ đã đăng ký với cơ quan quản lý lao động và niêm yết tại bảng tin mỗi xưởng. '
      'Bài này tóm tắt các điểm chính.')
    + ul('Đi làm đúng giờ, chấm công vào/ra bằng máy vân tay ở cổng xưởng.',
         'Mặc đồng phục, đeo thẻ nhân viên trong khu vực sản xuất.',
         'Không mang thực phẩm, chất dễ cháy vào khu vực chuyền may và kho.',
         'Giữ gìn máy móc, nguyên phụ liệu; báo tổ trưởng khi máy hỏng.',
         'Tuân thủ quy định an toàn lao động và PCCC; tham gia huấn luyện định kỳ.',
         'Không tự ý rời vị trí trong giờ làm việc khi chưa báo tổ trưởng.')
    + p('Vi phạm nội quy được xử lý theo bài <b>Xử lý kỷ luật lao động</b>.'), seq=1, views=(180, 260))

art('gio', 'Thời giờ làm việc và ca sản xuất', C_GIO, ['Bắt buộc đọc', 'Công nhân', 'Nhân viên mới'],
    'Ca hành chính, ca sáng – chiều – đêm, nghỉ giữa ca, nghỉ hằng tuần.',
    table(['Ca', 'Giờ làm', 'Áp dụng'],
          ['Hành chính', '08:00 – 17:00, nghỉ trưa 60 phút', 'Khối văn phòng, kho'],
          ['Ca sáng', '06:00 – 14:00', 'Chuyền may, tổ cắt, hoàn thiện'],
          ['Ca chiều', '14:00 – 22:00', 'Chuyền may, hoàn thiện'],
          ['Ca đêm', '22:00 – 06:00', 'Khi có đơn gấp, có thông báo trước'])
    + p('Thời giờ làm việc bình thường không quá 8 giờ/ngày và 48 giờ/tuần (Điều 105 BLLĐ 2019). '
        'Mỗi tuần được nghỉ ít nhất 24 giờ liên tục (Điều 111).')
    + p('Nghỉ giữa giờ: làm việc từ 6 giờ/ngày trở lên được nghỉ ít nhất <b>30 phút</b> liên tục; '
        'làm việc ban đêm được nghỉ ít nhất <b>45 phút</b> liên tục (Điều 109). '
        'Giờ làm việc ban đêm tính từ 22 giờ đến 6 giờ sáng hôm sau (Điều 106).')
    + p('Lịch ca của từng người xem trên <b>Cổng nhân viên › Lịch ca</b>.'), seq=1, views=(150, 230))

art('tangca', 'Làm thêm giờ: giới hạn và cách tính lương', C_GIO, ['Công nhân', 'Luật lao động'],
    'Giới hạn giờ làm thêm (ngành may tối đa 300 giờ/năm), mức 150% / 200% / 300%, phụ trội ban đêm.',
    h('Điều kiện')
    + p('Làm thêm giờ phải có sự đồng ý của người lao động (Điều 107 BLLĐ 2019). '
        'Tổ trưởng đăng ký danh sách tăng ca trước ít nhất 1 ngày.')
    + h('Giới hạn')
    + ul('Không quá 50% số giờ làm việc bình thường trong ngày; tổng giờ làm bình thường + làm thêm không quá 12 giờ/ngày.',
         'Không quá 40 giờ/tháng.',
         'Không quá 200 giờ/năm; riêng ngành <b>dệt, may</b> được tới <b>300 giờ/năm</b> '
         '(Điều 107 BLLĐ 2019, Điều 61 Nghị định 145/2020) và phải thông báo cho Sở LĐ-TB&amp;XH.')
    + h('Tiền lương làm thêm (Điều 98)')
    + table(['Thời điểm làm thêm', 'Mức tối thiểu'],
            ['Ngày thường', '150%'], ['Ngày nghỉ hằng tuần', '200%'],
            ['Ngày lễ, Tết, nghỉ có hưởng lương', '300% (chưa kể lương ngày lễ)'])
    + p('Làm việc vào ban đêm được trả thêm ít nhất 30% tiền lương. '
        'Làm thêm giờ vào ban đêm còn được trả thêm 20% theo quy định tại Điều 98.')
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
    + p('Nên đăng ký nghỉ phép dài ngày tránh tháng cao điểm giao hàng (tháng 9 – 11).'), seq=1, views=(240, 380))

art('phep_hd', 'Hướng dẫn xin nghỉ phép trên Cổng nhân viên', C_HDSD, ['Cổng nhân viên', 'Công nhân'],
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
    'Thời gian thử việc tối đa theo vị trí, lương thử việc tối thiểu 85%, các loại hợp đồng của công ty.',
    h('Thời gian thử việc tối đa (Điều 25 BLLĐ 2019)')
    + table(['Công việc', 'Tối đa'],
            ['Người quản lý doanh nghiệp', '180 ngày'],
            ['Cần trình độ cao đẳng trở lên', '60 ngày'],
            ['Cần trình độ trung cấp, công nhân kỹ thuật, nhân viên nghiệp vụ', '30 ngày'],
            ['Công việc khác', '6 ngày làm việc'])
    + p('Lương thử việc ít nhất bằng <b>85%</b> mức lương của công việc đó (Điều 26). '
        'Hợp đồng dưới 1 tháng không áp dụng thử việc.')
    + h('Các loại hợp đồng tại công ty')
    + ul('Hợp đồng xác định thời hạn 12 tháng (công nhân mới), sau đó 36 tháng.',
         'Hợp đồng không xác định thời hạn sau khi đã ký 2 hợp đồng xác định thời hạn.',
         'Hợp đồng thời vụ cho mùa cao điểm.')
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
    + p('Quản lý ghi nhận vi phạm bằng biên bản và chuyển Phòng Nhân sự; không tự xử lý tại tổ.'),
    seq=3, views=(40, 90))

# ── Lương, thưởng, phúc lợi ─────────────────────────────
art('luong', 'Quy chế trả lương và ngày trả lương', C_LUONG, ['Bắt buộc đọc', 'Công nhân'],
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

art('phucap', 'Phụ cấp và hỗ trợ', C_LUONG, ['Công nhân'],
    'Phụ cấp chuyên cần, hỗ trợ nhà trọ, đi lại, con nhỏ, ăn ca — điều kiện hưởng.',
    table(['Khoản', 'Điều kiện'],
          ['Chuyên cần', 'Đi làm đủ công trong tháng, không nghỉ không phép, không đi trễ quá 2 lần'],
          ['Hỗ trợ nhà trọ, đi lại', 'Công nhân thuê trọ, có đăng ký tạm trú'],
          ['Hỗ trợ con nhỏ', 'Có con dưới 6 tuổi, nộp giấy khai sinh'],
          ['Ăn ca', 'Mỗi ca làm việc thực tế; tăng ca từ 2 giờ có thêm bữa phụ'])
    + p('Mức cụ thể của từng khoản theo quy chế lương hiện hành, niêm yết tại bảng tin và trên phiếu lương.'),
    seq=2, views=(110, 190))

art('kpi_thuong', 'Quy chế thưởng KPI tháng', C_LUONG, ['Quản lý'],
    '(Nội bộ HR) Xếp loại KPI tháng và hệ số thưởng tương ứng.',
    p('Thưởng KPI tháng tính trên kết quả <b>phiếu đánh giá KPI</b> đã hoàn tất của tháng đó.')
    + table(['Điểm tổng', 'Xếp loại', 'Hệ số thưởng'],
            ['Từ 90', 'Xuất sắc', '1,2'], ['80 – dưới 90', 'Tốt', '1,0'], ['65 – dưới 80', 'Khá', '0,8'],
            ['50 – dưới 65', 'Đạt', '0,5'], ['Dưới 50', 'Chưa đạt', '0'])
    + p('Quỹ thưởng tháng do Ban Giám đốc duyệt theo kết quả sản lượng. Tài liệu này chỉ dành cho HR và quản lý.'),
    internal=True, seq=3, views=(30, 60))

art('kpi_qt', 'Quy trình đánh giá KPI hằng tháng', C_LUONG, ['Quản lý', 'Công nhân'],
    '4 bước: tạo phiếu – nhân viên tự đánh giá – quản lý đánh giá – hoàn tất; mốc thời gian mỗi tháng.',
    ol('<b>Ngày 25</b>: Phòng Nhân sự tạo đợt KPI tháng, hệ thống sinh phiếu cho từng nhân viên kèm bộ chỉ tiêu theo vị trí.',
       '<b>Ngày 25 – 28</b>: nhân viên nhập kết quả thực tế và tự chấm điểm, gửi tự đánh giá.',
       '<b>Đến ngày 2 tháng sau</b>: quản lý trực tiếp chấm điểm từng chỉ tiêu và nhận xét.',
       '<b>Ngày 3</b>: hoàn tất phiếu; điểm tổng và xếp loại chuyển sang tính thưởng KPI.')
    + p('Chỉ tiêu công nhân may: năng suất so với định mức, tỷ lệ hàng lỗi, chuyên cần, tuân thủ ATLĐ & 5S.'),
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
art('maymay', 'Vận hành máy may công nghiệp an toàn', C_SX, ['Công nhân', 'An toàn'],
    'Kiểm tra trước ca, vận hành, xử lý khi gãy kim, kết thúc ca.',
    ol('Kiểm tra kim, chân vịt, dây curoa, che chắn puly và tấm chắn kim trước khi chạy.',
       'Bật nguồn, chạy thử không tải; điều chỉnh tốc độ phù hợp mã hàng.',
       'Không đưa tay vào vùng kim khi máy đang chạy; tắt máy khi thay chỉ, thay kim.',
       'Gãy kim: dừng máy, thu đủ mảnh kim nộp tổ trưởng để ghi sổ kiểm soát kim.',
       'Hết ca: tắt nguồn, vệ sinh máy, phủ bạt.'), seq=1, views=(110, 200))

art('kim', 'Quy định kiểm soát kim gãy', C_SX, ['Chất lượng', 'Công nhân'],
    'Thu hồi đủ mảnh kim gãy, sổ kiểm soát kim, cách ly sản phẩm nghi lẫn kim.',
    ul('Mỗi công nhân chỉ được cấp kim mới khi nộp lại kim cũ hoặc đủ mảnh kim gãy.',
       'Không tìm đủ mảnh: cách ly bó hàng đang may, báo QC dò kim trước khi chuyển công đoạn.',
       'Tổ trưởng ghi sổ kiểm soát kim mỗi ca; QC kiểm tra sổ hằng ngày.',
       '100% sản phẩm đi qua máy dò kim trước khi đóng thùng.'), seq=2, views=(70, 140))

art('qc', 'Quy trình kiểm tra chất lượng (QC) theo AQL', C_SX, ['Chất lượng'],
    'Kiểm tra trong chuyền, cuối chuyền và kiểm thành phẩm theo AQL trước khi xuất hàng.',
    ol('<b>Kiểm trong chuyền</b>: QC đi chuyền kiểm 7 sản phẩm/công đoạn/giờ, phát hiện lỗi báo ngay công nhân.',
       '<b>Kiểm cuối chuyền (end-line)</b>: kiểm 100% sản phẩm; ghi nhận tỷ lệ lỗi theo giờ.',
       '<b>Kiểm thành phẩm</b>: lấy mẫu theo AQL khách hàng yêu cầu (thường AQL 2.5) trước khi đóng thùng.',
       'Lô không đạt: tái kiểm 100%, sửa lỗi, kiểm lại.')
    + p('Lỗi thường gặp: bỏ mũi, sụp mí, nhăn đường may, lệch thông số, dính bẩn, sai nhãn.'),
    seq=3, views=(90, 170))

art('5s', 'Thực hiện 5S tại chuyền may', C_SX, ['Công nhân'],
    'Sàng lọc – Sắp xếp – Sạch sẽ – Săn sóc – Sẵn sàng; chấm điểm 5S hằng tuần.',
    table(['Bước', 'Việc cần làm tại chuyền'],
          ['Sàng lọc', 'Bỏ vải vụn, chỉ thừa, dụng cụ không dùng khỏi bàn máy'],
          ['Sắp xếp', 'Bán thành phẩm để đúng khay, đúng vị trí đánh dấu'],
          ['Sạch sẽ', 'Vệ sinh máy, sàn cuối mỗi ca'],
          ['Săn sóc', 'Tổ trưởng kiểm tra hằng ngày'],
          ['Sẵn sàng', 'Mọi người tự giác duy trì'])
    + p('Điểm 5S là một chỉ tiêu trong KPI tháng của công nhân và tổ trưởng.'), seq=4, views=(50, 110))

# ── An toàn ─────────────────────────────────────────────
art('atvsld', 'Huấn luyện an toàn, vệ sinh lao động định kỳ', C_AT, ['An toàn', 'Bắt buộc đọc', 'Luật lao động'],
    '6 nhóm đối tượng huấn luyện theo Nghị định 44/2016, chu kỳ huấn luyện lại, chứng chỉ trên hồ sơ.',
    table(['Nhóm', 'Đối tượng', 'Huấn luyện định kỳ'],
          ['1', 'Người quản lý phụ trách công tác ATVSLĐ', 'Ít nhất 2 năm/lần'],
          ['2', 'Người làm công tác ATVSLĐ', 'Ít nhất 2 năm/lần'],
          ['3', 'Người làm công việc có yêu cầu nghiêm ngặt (nồi hơi, điện, xe nâng…)', 'Ít nhất 2 năm/lần'],
          ['4', 'Người lao động còn lại (công nhân may, cắt, hoàn thiện…)', 'Ít nhất 1 năm/lần'],
          ['5', 'Người làm công tác y tế', 'Ít nhất 2 năm/lần'],
          ['6', 'An toàn, vệ sinh viên', 'Ít nhất 1 năm/lần'])
    + p('Chứng chỉ, kết quả huấn luyện được lưu ở tab <b>Chứng chỉ</b> trên hồ sơ nhân viên; '
        'hệ thống nhắc Phòng Nhân sự trước khi hết hạn 60 ngày.'), seq=1, views=(100, 190))

art('quytac', '5 quy tắc an toàn bắt buộc trong xưởng', C_AT, ['An toàn', 'Công nhân', 'Nhân viên mới'],
    'Bảo hộ lao động, chỉ vận hành máy đã được huấn luyện, báo sự cố, lối thoát hiểm, khoá – treo biển khi bảo trì.',
    ol('Mang đầy đủ bảo hộ đúng khu vực: khẩu trang, găng tay sắt ở tổ cắt, giày bảo hộ ở kho.',
       'Chỉ vận hành máy, thiết bị đã được huấn luyện và giao.',
       'Kiểm tra thiết bị trước khi vận hành; báo ngay tổ trưởng khi có sự cố.',
       'Giữ lối thoát hiểm, tủ điện, bình chữa cháy luôn thông thoáng.',
       'Khoá nguồn và treo biển khi sửa chữa, bảo trì máy.'), seq=2, views=(130, 230))

art('pccc', 'Phòng cháy chữa cháy và thoát hiểm', C_AT, ['An toàn', 'Bắt buộc đọc'],
    'Nguy cơ cháy trong xưởng may, cách dùng bình chữa cháy, sơ đồ và hiệu lệnh thoát hiểm.',
    p('Vải, bông, chỉ và thùng carton rất dễ cháy. Mọi người phải biết vị trí bình chữa cháy và lối thoát gần nhất.')
    + h('Sử dụng bình chữa cháy')
    + ol('Rút chốt an toàn.', 'Hướng loa phun vào gốc lửa, đứng đầu hướng gió.', 'Bóp van, quét qua lại gốc lửa.')
    + h('Khi có hiệu lệnh báo cháy')
    + ul('Tắt máy, bình tĩnh đi theo lối thoát hiểm đã chỉ dẫn, không quay lại lấy đồ.',
         'Tập trung tại điểm tập kết sân trước; tổ trưởng điểm danh, báo cáo đội PCCC cơ sở.')
    + p('Công ty tổ chức diễn tập PCCC ít nhất mỗi năm một lần.'), seq=3, views=(90, 160))

art('socuu', 'Sơ cứu khi bị kim đâm, đứt tay, bỏng bàn là', C_AT, ['An toàn', 'Công nhân'],
    'Xử lý ban đầu các tai nạn nhỏ thường gặp; tủ thuốc và người sơ cứu ở mỗi xưởng.',
    h('Kim đâm tay')
    + ul('Tắt máy; nếu kim còn trong ngón tay, không tự rút khi kim gãy sâu — báo người sơ cứu.',
         'Rửa sạch, sát trùng, băng lại; đến trạm y tế nếu vết thương sâu.')
    + h('Đứt tay (tổ cắt)') + ul('Ép chặt vết thương bằng gạc sạch, giơ cao tay, báo người sơ cứu.')
    + h('Bỏng bàn là hơi') + ul('Xả nước mát 15 – 20 phút, không bôi kem đánh răng, không chọc vỡ bọng nước.')
    + p('Mỗi xưởng có tủ thuốc và người đã được huấn luyện sơ cấp cứu (danh sách dán tại tủ thuốc). '
        'Mọi tai nạn đều phải báo tổ trưởng để ghi sổ.'), seq=4, views=(60, 120))

# ── Hướng dẫn Sapiones ──────────────────────────────────
art('chamcong', 'Hướng dẫn chấm công và xử lý quên chấm công', C_HDSD, ['Cổng nhân viên', 'Công nhân', 'Nhân viên mới'],
    'Chấm vân tay vào/ra, xem công trên cổng, gửi yêu cầu điều chỉnh khi quên chấm.',
    ol('Đặt ngón tay đã đăng ký lên máy khi vào ca và khi tan ca; chờ máy báo thành công.',
       'Xem công từng ngày ở <b>Cổng nhân viên › Chấm công</b>.',
       'Quên chấm hoặc máy không nhận: báo tổ trưởng trong ngày để xác nhận và điều chỉnh công.',
       'Bảng công tháng được chốt ngày 3 tháng sau; sau ngày này điều chỉnh tính vào kỳ sau.'),
    seq=1, views=(170, 280))

art('hoi_ai', 'Hỏi Trợ lý tri thức', C_HDSD, ['Cổng nhân viên'],
    'Đặt câu hỏi bằng tiếng Việt, trợ lý tìm và tóm tắt câu trả lời từ kho tri thức của công ty.',
    p('Mở <b>Kho tri thức › Hỏi Trợ lý AI</b>, gõ câu hỏi như cách hỏi đồng nghiệp — '
      'về phép, lương, bảo hiểm, ca làm, quy trình sản xuất hay an toàn.')
    + p('Trợ lý chỉ trả lời dựa trên bài viết đã đăng trong kho và luôn kèm bài viết nguồn để đối chiếu. '
        'Câu hỏi về trường hợp riêng, hãy liên hệ Phòng Nhân sự.'), seq=3, views=(120, 210))

# ── Hội nhập ────────────────────────────────────────────
art('tuandau', 'Cẩm nang tuần đầu tiên cho nhân viên mới', C_NV, ['Nhân viên mới', 'Bắt buộc đọc'],
    'Việc cần làm trong tuần đầu: hồ sơ, huấn luyện an toàn, đăng ký vân tay, tài khoản cổng nhân viên.',
    table(['Ngày', 'Việc'],
          ['Ngày 1', 'Nhận đồng phục, thẻ nhân viên; nộp hồ sơ (CCCD, sơ yếu lý lịch, giấy khám sức khoẻ, sổ/số BHXH nếu có)'],
          ['Ngày 1', 'Đăng ký vân tay chấm công; nhận tài khoản Cổng nhân viên'],
          ['Ngày 2', 'Huấn luyện an toàn lao động lần đầu, PCCC, nội quy'],
          ['Ngày 2 – 5', 'Kèm cặp tại chuyền với công nhân tay nghề cao; làm quen công đoạn'],
          ['Cuối tuần', 'Gặp tổ trưởng đánh giá tuần đầu, giải đáp thắc mắc'])
    + p('Đọc trước các bài có thẻ <b>Nhân viên mới</b> trong kho tri thức.'), seq=1, views=(140, 240))

art('sodo', 'Sơ đồ tổ chức và người liên hệ', C_NV, ['Nhân viên mới'],
    'Các xưởng, chuyền, tổ và phòng ban; gặp ai khi cần.',
    table(['Việc cần hỏi', 'Liên hệ'],
          ['Công, lương, phép, bảo hiểm', 'Phòng Nhân sự'], ['Máy hỏng, điện', 'Tổ Cơ điện · Bảo trì'],
          ['Nguyên phụ liệu thiếu', 'Kho Nguyên phụ liệu'], ['Lỗi hàng, tiêu chuẩn khách', 'Tổ QC'],
          ['Tai nạn, sơ cứu', 'Người sơ cứu của xưởng, tổ trưởng'])
    + p('Sơ đồ tổ chức cập nhật xem trong ứng dụng <b>Nhân viên › Sơ đồ tổ chức</b>.'), seq=2, views=(80, 150))

art('faq', 'Câu hỏi thường gặp về công, lương, phép', C_FAQ, ['Công nhân', 'Nhân viên mới'],
    'Giải đáp nhanh các thắc mắc hay gặp nhất của người lao động.',
    h('Nghỉ ốm có bị trừ phép năm không?')
    + p('Không. Nghỉ ốm có giấy của cơ sở y tế được hưởng chế độ ốm đau BHXH, không trừ phép năm.')
    + h('Đang thử việc có được nghỉ phép năm không?')
    + p('Thời gian thử việc được tính vào thời gian làm việc để tính phép năm nếu tiếp tục làm việc sau thử việc.')
    + h('Tăng ca ngày Chủ nhật tính thế nào?')
    + p('Nếu Chủ nhật là ngày nghỉ hằng tuần của bạn: ít nhất 200% lương giờ. Xem bài <b>Làm thêm giờ</b>.')
    + h('Đổi số tài khoản nhận lương?')
    + p('Gửi Phòng Nhân sự bản sao thông tin tài khoản đứng tên chính mình trước ngày 3 hằng tháng.'),
    seq=1, views=(210, 340))

# ── Nháp ────────────────────────────────────────────────
art('caodiem', 'Kế hoạch tăng ca mùa cao điểm (dự thảo)', C_GIO, ['Quản lý'],
    'Dự thảo phân bổ giờ tăng ca theo chuyền tháng cao điểm, trong giới hạn 300 giờ/năm.',
    p('Dự thảo đang lấy ý kiến tổ trưởng: bố trí tăng ca luân phiên theo chuyền, '
      'theo dõi luỹ kế giờ làm thêm từng người để không vượt 40 giờ/tháng và 300 giờ/năm.'),
    draft=True, internal=True, seq=9)
art('tuyendung', 'Quy trình tuyển công nhân thời vụ (dự thảo)', C_HD, ['Quản lý'],
    'Dự thảo quy trình tuyển, ký hợp đồng thời vụ và huấn luyện nhanh cho mùa cao điểm.',
    p('Dự thảo: nhận hồ sơ qua cổng tuyển dụng, kiểm tra tay nghề tại chỗ, ký hợp đồng thời vụ, '
      'huấn luyện ATVSLĐ trước khi vào chuyền.'), draft=True, internal=True, seq=9)

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
