# -*- coding: utf-8 -*-
"""Sapiones Provisioning API — đăng ký tự phục vụ (xác thực EMAIL).

Khớp contract của form đăng ký trên sapiones.com/dang-ky (BSD Website):
  POST /v1/register/start  {email,name,company,province,phone} → {ok,request_id,expires_in}
  POST /v1/register/verify {request_id,code,password}          → {ok,tenant_id,url}

Chạy TRÊN HOST của VPS (không trong container) để gọi được `docker compose ...`
qua demo-data/packs/provision.sh. Cloudflare Tunnel: register.sapiones.com → BIND_HOST:PORT.
Cấu hình SMTP + repo path + CF token qua biến môi trường (xem .env.example) — KHÔNG hardcode creds.
"""
import os
import re
import ssl
import json
import unicodedata
import time
import secrets
import smtplib
import subprocess
import urllib.request
import urllib.error
from email.message import EmailMessage

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Config (env) ──────────────────────────────────────────────────────────
REPO_DIR = os.environ.get('SAPIONES_REPO', '/root/sapiones')
SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', 'resend')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
MAIL_FROM = os.environ.get('MAIL_FROM', 'Sapiones <noreply@sapiones.com>')
ALLOWED_ORIGINS = (os.environ.get('ALLOWED_ORIGINS')
                   or 'https://sapiones.com,https://www.sapiones.com').split(',')
CODE_TTL = int(os.environ.get('CODE_TTL', '600'))  # 10 phút
PROVISION_TIMEOUT = int(os.environ.get('PROVISION_TIMEOUT', '240'))

# Cloudflare DNS — gói Free KHÔNG proxy được wildcard, nên mỗi tenant tạo 1 record
# proxied <id>.sapiones.com → tunnel qua API (tunnel ingress *.sapiones.com đã khớp).
# Token chỉ cần quyền Zone.DNS:Edit cho sapiones.com.
BASE_DOMAIN = os.environ.get('BASE_DOMAIN', 'sapiones.com')
CF_API_TOKEN = os.environ.get('CF_API_TOKEN', '')
CF_ZONE_ID = os.environ.get('CF_ZONE_ID', '')
CF_TUNNEL_CNAME = os.environ.get('CF_TUNNEL_CNAME', '')  # <tunnel-uuid>.cfargotunnel.com

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_TENANT_ID_RE = re.compile(r'^[a-z0-9][a-z0-9-]{2,30}$')  # subdomain/DB hợp lệ: 3–31 ký tự

# Từ khoá KHÔNG cho làm subdomain (hệ thống / dễ nhầm).
_RESERVED = {
    'www', 'api', 'demo', 'register', 'tuyendung', 'mail', 'admin', 'app',
    'static', 'cdn', 'ftp', 'smtp', 'ns', 'ns1', 'ns2', 'mx', 'webmail',
    'portal', 'status', 'blog', 'docs', 'help', 'support', 'sapiones',
    'test', 'staging', 'dev', 'root', 'system', 'billing', 'account',
}
# Token pháp lý bỏ khi suy slug từ TÊN CÔNG TY (đã bỏ dấu, thường).
_LEGAL_TOKENS = [
    'cong ty', 'cty', 'tnhh', 'mtv', 'mot thanh vien', 'co phan', 'cp',
    'tap doan', 'doanh nghiep tu nhan', 'dntn', 'chi nhanh', 'cn',
]


def _ascii_fold(s: str) -> str:
    """Bỏ dấu tiếng Việt → ASCII. đ/Đ xử tay (NFKD không tách)."""
    s = (s or '').replace('đ', 'd').replace('Đ', 'D')
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c))


def _slugify(name: str, strip_legal: bool = True) -> str:
    """Tên → slug subdomain hợp lệ, hoặc '' nếu không tạo được (<3 ký tự).

    strip_legal=True: bỏ tiền/hậu tố pháp lý (khi suy từ TÊN CÔNG TY).
    strip_legal=False: chỉ sanitize (khi user tự gõ slug).
    """
    s = _ascii_fold(name).lower()
    if strip_legal:
        changed = True
        while changed:
            changed = False
            for tok in _LEGAL_TOKENS:
                for pat in (r'^\s*' + re.escape(tok) + r'\b[\s.,-]*',
                            r'[\s.,-]*\b' + re.escape(tok) + r'\s*$'):
                    new = re.sub(pat, '', s)
                    if new != s:
                        s, changed = new.strip(), True
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-{2,}', '-', s).strip('-')
    if len(s) > 31:                       # regex tối đa 1+30 = 31 ký tự
        head = s[:31]
        s = (head.rsplit('-', 1)[0] if '-' in head else head).strip('-')
    return s if _TENANT_ID_RE.match(s) else ''


def _tenant_db_exists(slug: str) -> bool:
    """DB tenant đã tồn tại chưa (nguồn sự thật cho 'đã bị lấy'). Best-effort."""
    if not _TENANT_ID_RE.match(slug):
        return False
    sql = "SELECT 1 FROM pg_database WHERE datname='%s'" % slug
    cmd = 'psql -U "${POSTGRES_USER:-odoo}" -d postgres -tAc "%s"' % sql
    try:
        out = subprocess.run(
            ['docker', 'compose', '-f', 'docker-compose.vps.yml', 'exec', '-T', 'db',
             'bash', '-lc', cmd],
            cwd=REPO_DIR, capture_output=True, timeout=15)
        return b'1' in (out.stdout or b'')
    except Exception as e:
        print("DB_CHECK_ERROR:", repr(e), flush=True)
        return False

app = FastAPI(title="Sapiones Provisioning API")
app.add_middleware(
    CORSMiddleware, allow_origins=ALLOWED_ORIGINS,
    allow_methods=['GET', 'POST'], allow_headers=['*'])

_REQ = {}    # request_id -> {email,name,company,province,phone,code,exp,tries}
_RATE = {}   # key -> [timestamps]


def _client_ip(request: Request) -> str:
    return (request.headers.get('cf-connecting-ip')
            or (request.client.host if request.client else '?'))


def _rate_ok(key: str, limit: int, window: int) -> bool:
    now = time.time()
    arr = [t for t in _RATE.get(key, []) if now - t < window]
    if len(arr) >= limit:
        _RATE[key] = arr
        return False
    arr.append(now)
    _RATE[key] = arr
    return True


def _err(code_http: int, error: str, message: str):
    return JSONResponse(status_code=code_http,
                        content={'ok': False, 'error': error, 'message': message})


def _send_code(to: str, name: str, code: str):
    msg = EmailMessage()
    msg['Subject'] = 'Sapiones — Mã xác nhận: %s' % code
    msg['From'] = MAIL_FROM
    msg['To'] = to
    msg.set_content(
        "Xin chào %s,\n\n"
        "Mã xác nhận đăng ký Sapiones của bạn là: %s\n"
        "Mã hết hạn sau %d phút.\n\n"
        "Nếu bạn không yêu cầu, hãy bỏ qua email này.\n\n— Sapiones"
        % (name or 'bạn', code, CODE_TTL // 60))
    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        s.ehlo()
        s.starttls(context=ctx)
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)


def _send_welcome(to: str, name: str, company: str, url: str):
    """Email chào mừng sau khi tạo tenant — để khách KHÔNG mất địa chỉ workspace."""
    msg = EmailMessage()
    msg['Subject'] = 'Sapiones — Workspace của %s đã sẵn sàng' % (company or 'bạn')
    msg['From'] = MAIL_FROM
    msg['To'] = to
    msg.set_content(
        "Xin chào %s,\n\n"
        "Workspace Sapiones cho \"%s\" đã được tạo xong và sẵn sàng sử dụng:\n\n"
        "  Địa chỉ:   %s\n"
        "  Đăng nhập: %s\n"
        "  Mật khẩu:  mật khẩu bạn đã đặt khi đăng ký\n\n"
        "Mở địa chỉ trên, đăng nhập và bắt đầu thêm nhân viên đầu tiên.\n"
        "Hãy LƯU email này để không quên địa chỉ workspace của bạn.\n\n"
        "Cần hỗ trợ? Vui lòng liên hệ đội ngũ Sapiones (BSD).\n\n— Sapiones"
        % (name or 'bạn', company or 'bạn', url, to))
    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        s.ehlo()
        s.starttls(context=ctx)
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)


def _create_tenant_dns(tenant_id: str) -> bool:
    """Tạo proxied CNAME <id>.sapiones.com → tunnel (Free plan không proxy wildcard).
    Trả True nếu tạo được / đã tồn tại; False nếu thiếu config hoặc lỗi."""
    if not (CF_API_TOKEN and CF_ZONE_ID and CF_TUNNEL_CNAME):
        print("DNS_SKIP: thiếu CF_API_TOKEN/CF_ZONE_ID/CF_TUNNEL_CNAME", flush=True)
        return False
    url = "https://api.cloudflare.com/client/v4/zones/%s/dns_records" % CF_ZONE_ID
    payload = json.dumps({
        "type": "CNAME",
        "name": "%s.%s" % (tenant_id, BASE_DOMAIN),
        "content": CF_TUNNEL_CNAME,
        "proxied": True,
        "ttl": 1,
        "comment": "sapiones tenant %s" % tenant_id,
    }).encode()
    req = urllib.request.Request(url, data=payload, method='POST', headers={
        'Authorization': 'Bearer %s' % CF_API_TOKEN,
        'Content-Type': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode())
        if body.get('success'):
            return True
        print("DNS_FAILED:", json.dumps(body.get('errors', []))[:500], flush=True)
        return False
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')
        if 'already exist' in detail.lower():
            print("DNS_EXISTS: %s đã có record" % tenant_id, flush=True)
            return True
        print("DNS_HTTP_ERROR %s: %s" % (e.code, detail[:500]), flush=True)
        return False
    except Exception as e:
        print("DNS_ERROR:", repr(e), flush=True)
        return False


class StartIn(BaseModel):
    email: str
    name: str = ''       # người liên hệ
    company: str = ''    # tên công ty
    province: str = ''
    phone: str = ''
    subdomain: str = ''  # slug workspace user chọn/sửa; trống → suy từ company


class VerifyIn(BaseModel):
    request_id: str
    code: str
    password: str = ''


@app.get('/v1/health')
def health():
    return {'ok': True, 'domain': BASE_DOMAIN}


@app.get('/v1/subdomain/check')
def subdomain_check(request: Request, name: str = '', from_company: int = 0):
    """Form gọi realtime khi user gõ tên công ty / sửa slug.
    from_company=1: input là TÊN CÔNG TY (bỏ token pháp lý); mặc định: slug user gõ."""
    if not _rate_ok('chk:' + _client_ip(request), 60, 60):
        return _err(429, 'rate_limited', 'Bạn thử quá nhiều lần, vui lòng đợi.')
    slug = _slugify(name, strip_legal=bool(from_company))
    if not slug:
        return {'ok': True, 'available': False, 'slug': '', 'reason': 'invalid',
                'message': 'Tên workspace cần ≥3 ký tự chữ/số. Vui lòng nhập lại.'}
    if slug in _RESERVED:
        return {'ok': True, 'available': False, 'slug': slug, 'reason': 'reserved',
                'message': 'Tên này được giữ chỗ, vui lòng chọn tên khác.'}
    if _tenant_db_exists(slug):
        return {'ok': True, 'available': False, 'slug': slug, 'reason': 'taken',
                'message': '"%s.%s" đã có người dùng.' % (slug, BASE_DOMAIN)}
    return {'ok': True, 'available': True, 'slug': slug,
            'url': 'https://%s.%s' % (slug, BASE_DOMAIN)}


@app.post('/v1/register/start')
def register_start(body: StartIn, request: Request):
    email = (body.email or '').strip().lower()
    if not EMAIL_RE.match(email):
        return _err(400, 'email_invalid', 'Email không hợp lệ.')
    company = (body.company or '').strip()
    if len(company) < 2:
        return _err(400, 'company_required', 'Vui lòng nhập tên công ty.')
    ip = _client_ip(request)
    if not _rate_ok('e:' + email, 3, 3600) or not _rate_ok('ip:' + ip, 20, 3600):
        return _err(429, 'rate_limited', 'Bạn thử quá nhiều lần, vui lòng đợi.')
    # Subdomain: ưu tiên slug user tự gõ (sanitize nhẹ), else suy từ tên công ty (bỏ token pháp lý).
    slug = (_slugify(body.subdomain, strip_legal=False) if (body.subdomain or '').strip()
            else _slugify(company, strip_legal=True))
    if not slug:
        return _err(400, 'subdomain_required',
                    'Không tạo được tên workspace từ tên công ty. Vui lòng nhập tên workspace.')
    if slug in _RESERVED:
        return _err(400, 'subdomain_reserved', 'Tên workspace này được giữ chỗ, chọn tên khác.')
    if _tenant_db_exists(slug):
        return _err(409, 'subdomain_taken',
                    '"%s.%s" đã có người dùng, vui lòng chọn tên khác.' % (slug, BASE_DOMAIN))
    code = '%06d' % secrets.randbelow(1000000)
    rid = secrets.token_urlsafe(9)
    _REQ[rid] = {'email': email, 'name': (body.name or '').strip(), 'company': company,
                 'province': (body.province or '').strip(),
                 'phone': (body.phone or '').strip(), 'subdomain': slug, 'code': code,
                 'exp': time.time() + CODE_TTL, 'tries': 0}
    try:
        _send_code(email, body.name, code)
    except Exception as e:
        print("MAIL_FAILED:", repr(e), flush=True)
        _REQ.pop(rid, None)
        return _err(502, 'mail_failed', 'Không gửi được email xác nhận. Thử lại sau.')
    return {'ok': True, 'request_id': rid, 'expires_in': CODE_TTL}


@app.post('/v1/register/verify')
def register_verify(body: VerifyIn):
    r = _REQ.get(body.request_id)
    if not r:
        return _err(400, 'request_invalid', 'Yêu cầu không tồn tại, vui lòng đăng ký lại.')
    if time.time() > r['exp']:
        _REQ.pop(body.request_id, None)
        return _err(400, 'otp_expired', 'Mã đã hết hạn, vui lòng đăng ký lại.')
    r['tries'] += 1
    if r['tries'] > 5:
        _REQ.pop(body.request_id, None)
        return _err(429, 'too_many', 'Sai mã nhiều lần, vui lòng đăng ký lại.')
    if (body.code or '').strip() != r['code']:
        return _err(400, 'otp_wrong', 'Mã không đúng.')

    # Email đã xác thực → provision tenant
    env = dict(os.environ)
    if body.password:
        env['TENANT_PASSWORD'] = body.password
    # Subdomain = slug tên công ty (đã chốt ở /start). Trùng (race) → thử hậu tố -2..-6.
    base_slug = r.get('subdomain') or _slugify(r.get('company', ''))
    if not base_slug:
        return _err(400, 'subdomain_required', 'Thiếu tên workspace, vui lòng đăng ký lại.')
    cands = [c for c in [base_slug] + ['%s-%d' % (base_slug, n) for n in range(2, 7)]
             if _TENANT_ID_RE.match(c)]
    tid = None
    for cand in cands:
        try:
            subprocess.run(
                ['bash', 'demo-data/packs/provision.sh',
                 cand, r['email'], r['company'], r['name'], r['province'], r.get('phone', '')],
                cwd=REPO_DIR, env=env, check=True,
                capture_output=True, timeout=PROVISION_TIMEOUT)
            tid = cand
            break
        except subprocess.CalledProcessError as e:
            if e.returncode == 2:   # slug trùng → thử hậu tố kế
                print("PROVISION_RETRY: id %s đã tồn tại" % cand, flush=True)
                continue
            print("PROVISION_FAILED rc=%s\nSTDOUT:\n%s\nSTDERR:\n%s" % (
                e.returncode,
                (e.stdout or b'').decode('utf-8', 'replace')[-3000:],
                (e.stderr or b'').decode('utf-8', 'replace')[-3000:]), flush=True)
            return _err(500, 'provision_failed', 'Lỗi tạo tài khoản, vui lòng liên hệ hỗ trợ.')
        except Exception as e:
            print("PROVISION_ERROR:", repr(e), flush=True)
            return _err(500, 'provision_failed', 'Lỗi tạo tài khoản, vui lòng liên hệ hỗ trợ.')
    if not tid:
        return _err(409, 'subdomain_taken',
                    'Tên workspace đã có người dùng, vui lòng chọn tên khác.')

    dns_ok = _create_tenant_dns(tid)
    url = 'https://%s.%s' % (tid, BASE_DOMAIN)
    try:
        _send_welcome(r['email'], r['name'], r['company'], url)
    except Exception as e:
        print("WELCOME_MAIL_FAILED:", repr(e), flush=True)  # tenant đã tạo — không chặn
    _REQ.pop(body.request_id, None)
    return {'ok': True, 'tenant_id': tid, 'url': url, 'dns_ok': dns_ok}


# ── Quên mật khẩu (đặt lại qua OTP email — vì mail server tenant đã neutralize) ──
_RESET = {}   # request_id -> {tenant_id, email, code, exp, tries}


def _send_reset_code(to: str, code: str):
    msg = EmailMessage()
    msg['Subject'] = 'Sapiones — Mã đặt lại mật khẩu: %s' % code
    msg['From'] = MAIL_FROM
    msg['To'] = to
    msg.set_content(
        "Mã đặt lại mật khẩu Sapiones của bạn là: %s\n"
        "Mã hết hạn sau %d phút.\n\n"
        "Nếu bạn không yêu cầu, hãy bỏ qua email này.\n\n— Sapiones"
        % (code, CODE_TTL // 60))
    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        s.ehlo()
        s.starttls(context=ctx)
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)


class ResetStartIn(BaseModel):
    tenant_id: str      # mã workspace (subdomain), vd "265525"
    email: str


class ResetVerifyIn(BaseModel):
    request_id: str
    code: str
    password: str = ''


@app.post('/v1/reset/start')
def reset_start(body: ResetStartIn, request: Request):
    email = (body.email or '').strip().lower()
    tid = (body.tenant_id or '').strip().lower()
    if not EMAIL_RE.match(email):
        return _err(400, 'email_invalid', 'Email không hợp lệ.')
    if not _TENANT_ID_RE.match(tid):
        return _err(400, 'tenant_invalid', 'Mã workspace không hợp lệ.')
    ip = _client_ip(request)
    if not _rate_ok('re:' + email, 3, 3600) or not _rate_ok('rip:' + ip, 20, 3600):
        return _err(429, 'rate_limited', 'Bạn thử quá nhiều lần, vui lòng đợi.')
    code = '%06d' % secrets.randbelow(1000000)
    rid = secrets.token_urlsafe(9)
    _RESET[rid] = {'tenant_id': tid, 'email': email, 'code': code,
                   'exp': time.time() + CODE_TTL, 'tries': 0}
    try:
        _send_reset_code(email, code)
    except Exception as e:
        print("RESET_MAIL_FAILED:", repr(e), flush=True)
        _RESET.pop(rid, None)
        return _err(502, 'mail_failed', 'Không gửi được email. Thử lại sau.')
    return {'ok': True, 'request_id': rid, 'expires_in': CODE_TTL}


@app.post('/v1/reset/verify')
def reset_verify(body: ResetVerifyIn):
    r = _RESET.get(body.request_id)
    if not r:
        return _err(400, 'request_invalid', 'Yêu cầu không tồn tại, vui lòng thử lại.')
    if time.time() > r['exp']:
        _RESET.pop(body.request_id, None)
        return _err(400, 'otp_expired', 'Mã đã hết hạn, vui lòng thử lại.')
    r['tries'] += 1
    if r['tries'] > 5:
        _RESET.pop(body.request_id, None)
        return _err(429, 'too_many', 'Sai mã nhiều lần, vui lòng thử lại.')
    if (body.code or '').strip() != r['code']:
        return _err(400, 'otp_wrong', 'Mã không đúng.')
    if len(body.password or '') < 6:
        return _err(400, 'weak_password', 'Mật khẩu tối thiểu 6 ký tự.')
    # Đặt lại CHỈ khi email đúng là tài khoản trong workspace đó (reset.sh exit 4 nếu không).
    env = dict(os.environ)
    env['TENANT_PASSWORD'] = body.password
    try:
        subprocess.run(['bash', 'demo-data/packs/reset.sh', r['tenant_id'], r['email']],
                       cwd=REPO_DIR, env=env, check=True,
                       capture_output=True, timeout=PROVISION_TIMEOUT)
    except subprocess.CalledProcessError as e:
        rc = e.returncode
        msg = ('Không tìm thấy workspace.' if rc == 3
               else 'Email không khớp tài khoản của workspace này.' if rc == 4
               else 'Đặt lại mật khẩu thất bại, vui lòng liên hệ hỗ trợ.')
        print("RESET_FAILED rc=%s\n%s" % (rc, (e.stderr or b'')[-1500:].decode('utf-8', 'replace')), flush=True)
        return _err(400 if rc in (3, 4) else 500, 'reset_failed', msg)
    except Exception as e:
        print("RESET_ERROR:", repr(e), flush=True)
        return _err(500, 'reset_failed', 'Đặt lại mật khẩu thất bại, vui lòng liên hệ hỗ trợ.')
    _RESET.pop(body.request_id, None)
    return {'ok': True}
