# Sapiones

**Phần mềm quản lý nhân sự (HRM/HCM) cho doanh nghiệp Việt Nam — chuyên sâu cho ngành sản xuất.**

Phát triển trên nền tảng [Odoo](https://www.odoo.com) Community 19, bởi [BSD](https://bsdinsight.com).

---

## Sapiones là gì?

Sapiones là bộ giải pháp quản trị nguồn nhân lực thiết kế cho doanh nghiệp Việt Nam, đặc biệt là các doanh nghiệp **sản xuất** với nhu cầu quản lý lao động số lượng lớn, ca kíp và tính lương phức tạp.

Định hướng dài hạn: đạt độ sâu chức năng của các nền tảng HCM hàng đầu (Workday, SAP SuccessFactors, Oracle HCM), nhưng tối ưu cho bối cảnh và pháp luật lao động Việt Nam.

## Mô hình Open-Core

Sapiones phát triển theo mô hình **open-core**:

- 🟢 **Sapiones Community (mã nguồn mở, miễn phí)** — một HRIS hoàn chỉnh cho một pháp nhân, đủ dùng cho doanh nghiệp nhỏ và vừa.
- 🔵 **Sapiones Professional / Enterprise (thương mại)** — bổ sung các năng lực nâng cao cho doanh nghiệp sản xuất quy mô lớn và nhiều pháp nhân.

### Bản Community gồm

- **Hồ sơ & tổ chức:** hồ sơ nhân viên, cơ cấu tổ chức, chức danh, sơ đồ tổ chức, hợp đồng, tài liệu.
- **Bản địa hóa Việt Nam:** CCCD, mã số thuế, sổ BHXH, người phụ thuộc...
- **Chấm công & nghỉ phép cơ bản:** check in/out, đơn nghỉ phép, số dư phép, lịch làm việc.
- **Tuyển dụng cơ bản:** đăng tin, quản lý ứng viên, pipeline phỏng vấn.
- **Cổng nhân viên (ESS):** tự phục vụ qua web.
- **Báo cáo cơ bản:** nhân sự, biến động, danh sách.

### Bản thương mại bổ sung (tiêu biểu)

- **Tính lương Việt Nam:** gross-to-net, BHXH/BHYT/BHTN/KPCĐ, thuế TNCN, lương sản phẩm/khoán, phiếu lương, file ngân hàng, kê khai điện tử.
- **Chấm công sản xuất:** engine ca kíp (đảo ca, 3 ca 4 kíp), tích hợp máy chấm công, quy tắc tăng ca tự động.
- **Quản trị tài năng:** KPI/OKR, đánh giá 360, đào tạo (LMS), lộ trình phát triển.
- **Phân tích & hoạch định:** dashboard, định biên, dự báo biến động nhân sự.
- **Đặc thù sản xuất:** phân bổ chi phí nhân công, an toàn lao động (EHS), ma trận tay nghề.

> Cần tư vấn phiên bản thương mại? Liên hệ BSD: <https://bsdinsight.com>

## Modules

| Module | Tier | Mô tả |
|---|---|---|
| [`l10n_vn_hr`](l10n_vn_hr) | 🟢 Community (LGPL-3) | Bản địa hóa hồ sơ nhân sự VN: CCCD, MST cá nhân, sổ BHXH, quê quán/dân tộc/tôn giáo và quản lý **người phụ thuộc** (giảm trừ gia cảnh). |

> Các module Community khác sẽ được bổ sung dần theo lộ trình.

## Nền tảng

- Odoo Community 19

## Chạy thử với Docker

Yêu cầu: Docker + Docker Compose.

```bash
cp odoo.conf.example odoo.conf          # tùy chọn: đổi admin_passwd
docker compose up -d                     # Postgres 16 + Odoo 19 (container "sapiones")

# Tạo DB và cài module:
docker exec sapiones odoo -d sapiones -i l10n_vn_hr \
  --db_host=db --db_user=odoo --db_password=odoo --stop-after-init --no-http
docker restart sapiones
```

Mở **http://localhost:8079** (mặc định chỉ bind localhost; đổi cổng trong `docker-compose.yml` nếu cần).

## Giấy phép

Các module mã nguồn mở của Sapiones phát hành theo **LGPL-3.0** (tương thích Odoo) — xem [`LICENSE`](LICENSE).

## Về BSD

BSD ([bsdinsight.com](https://bsdinsight.com)) — đối tác triển khai giải pháp quản trị doanh nghiệp trên nền Odoo cho thị trường Việt Nam.

---

> 🚧 Dự án đang ở giai đoạn đầu. Lộ trình và các module sẽ được công bố dần.
