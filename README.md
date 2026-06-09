# Sapiones

**Phần mềm Quản trị Nhân sự (HRM/HCM) cho doanh nghiệp Việt Nam — đúng luật, trên nền Odoo.**

*Open-core HR for Vietnamese businesses, built on Odoo.*

Phát triển trên [Odoo](https://www.odoo.com) Community 19, bởi [BSD](https://bsdinsight.com).

🔗 **Demo trực tiếp:** <https://demo.sapiones.com> (`demo` / `demo`)  ·  🌐 **Website:** <https://sapiones.com>

---

## Sapiones là gì?

Nền tảng HRM/HCM cho **mọi doanh nghiệp** Việt Nam: tính lương đúng luật (BHXH, thuế TNCN), chấm công, kê khai điện tử, cổng nhân viên, tuyển dụng, đánh giá, đào tạo, kho tri thức + AI, báo cáo. Trên nền đó là các **phiên bản chuyên ngành** đi sâu từng lĩnh vực — **bắt đầu với Sản xuất** (ca kíp, máy chấm công, lương sản phẩm, ATLĐ). Triển khai **on-premise** (chủ quyền dữ liệu) hoặc cloud.

Định hướng dài hạn: đạt độ sâu chức năng của Workday / SAP SuccessFactors / Oracle HCM, nhưng tối ưu cho bối cảnh và pháp luật Việt Nam.

## Mô hình Open-Core — Miễn phí tới 30 nhân viên

Sapiones theo mô hình **open-core**:

- 🟢 **Mã nguồn mở (repo này, LGPL-3):** bản địa hóa hồ sơ nhân sự VN, đơn vị hành chính 2025, chứng chỉ — miễn phí, không giới hạn.
- 🔵 **Bản thương mại (Professional / Enterprise, by BSD):** tính lương, ca kíp & tăng ca, kê khai điện tử, cổng nhân viên, KPI/OKR, đào tạo & ATLĐ, kho tri thức + AI…

> 💡 **Dùng MIỄN PHÍ toàn bộ tính năng tới 30 nhân viên đang hoạt động — không giới hạn thời gian.**
> Khi vượt 30 nhân viên → bản quyền theo số lao động (liên hệ BSD). Phần mã nguồn mở luôn chạy không giới hạn.

## Module trong repo này (🟢 mã nguồn mở · LGPL-3)

| Module | Mô tả |
|---|---|
| [`l10n_vn_hr`](l10n_vn_hr) | Bản địa hóa hồ sơ nhân sự VN: CCCD/CMND, MST cá nhân, sổ BHXH, dân tộc/tôn giáo/quê quán và **người phụ thuộc** (giảm trừ gia cảnh). |
| [`l10n_vn_address`](l10n_vn_address) | Đơn vị hành chính Việt Nam **2025**: 34 tỉnh/thành → phường/xã (bỏ cấp huyện); nhập địa chỉ chuẩn cho nhân viên & đối tác. |
| [`sapiones_hr_certificate`](sapiones_hr_certificate) | Quản lý **chứng chỉ / bằng cấp** nhân viên + **cảnh báo hết hạn** tự động (an toàn lao động, vận hành thiết bị…). |

Cùng nền Odoo Community: hồ sơ & cơ cấu tổ chức, nghỉ phép (Time Off), chấm công check-in/out, báo cáo trực quan.

## Bản thương mại (🔵 by BSD) — đã có

- **Tính lương Việt Nam:** gross→net BHXH/BHYT/BHTN + thuế TNCN lũy tiến + giảm trừ gia cảnh; phiếu lương PDF (đọc số thành chữ), **file chuyển khoản ngân hàng**, **bảng kê thuế & BHXH**.
- **Chấm công ca kíp & tăng ca:** 3 ca 4 kíp, tăng ca 150/200/300% + ca đêm (đúng luật); **máy chấm công** (vân tay/khuôn mặt); **lương sản phẩm/khoán**.
- **Kê khai điện tử:** tờ khai thuế TNCN (05/KK, 05-1/BK) & BHXH (D02-LT).
- **Cổng nhân viên (ESS)** · **Đánh giá KPI/OKR** · **Đào tạo (LMS) & An toàn lao động (EHS)** · **Kho tri thức + Trợ lý AI**.

> Tư vấn bản thương mại / triển khai on-premise: <https://bsdinsight.com>

## Nền tảng

- Odoo Community 19

## Chạy thử với Docker

Yêu cầu: Docker + Docker Compose.

```bash
cp odoo.conf.example odoo.conf          # tùy chọn: đổi admin_passwd

docker compose up -d                     # PostgreSQL 16 + Odoo 19 (container "sapiones")

# Tạo DB và cài 3 module mã nguồn mở:
docker exec sapiones odoo -d sapiones \
  -i l10n_vn_hr,l10n_vn_address,sapiones_hr_certificate \
  --db_host=db --db_user=odoo --db_password=odoo --stop-after-init --no-http
docker restart sapiones
```

Mở **http://localhost:8079** (mặc định chỉ bind localhost; đổi cổng trong `docker-compose.yml` nếu cần).

## Giấy phép

- Các module mã nguồn mở của Sapiones phát hành theo **LGPL-3.0** (tương thích Odoo) — xem [`LICENSE`](LICENSE).
- Các module thương mại (Professional / Enterprise) phát hành riêng bởi BSD theo giấy phép OPL-1.

## Về BSD

BSD ([bsdinsight.com](https://bsdinsight.com)) — đối tác triển khai giải pháp quản trị doanh nghiệp trên nền Odoo cho thị trường Việt Nam.
