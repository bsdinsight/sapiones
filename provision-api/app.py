# -*- coding: utf-8 -*-
"""Sapiones Provisioning API — đăng ký tự phục vụ (xác thực EMAIL).

Khớp contract của form đăng ký trên sapiones.com/dang-ky (BSD Website):
  POST /v1/register/start  {email,name,company,province,phone} → {ok,request_id,expires_in}
  POST /v1/register/verify {request_id,code,password}          → {ok,tenant_id,url}

Chạy TRÊN HOST của VPS (không trong container) để gọi được `docker compose ...`
qua demo-data/packs/provision.sh. Cloudflare Tunnel: api.sapiones.com → BIND_HOST:PORT.
Cấu hình SMTP + repo path + CF token qua biến môi trường (xem .env.example) — KHÔNG hardcode creds.
"""
import os
import re
import ssl
import json
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

app = FastAPI(title="Sapiones Provisioning API")
app.add_middleware(
    CORSMiddleware, allow_origins=ALLOWED_ORIGINS,
    allow_methods=['POST'], allow_headers=['*'])

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


class VerifyIn(BaseModel):
    request_id: str
    code: str
    password: str = ''


@app.get('/v1/health')
def health():
    return {'ok': True, 'domain': BASE_DOMAIN}


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
    code = '%06d' % secrets.randbelow(1000000)
    rid = secrets.token_urlsafe(9)
    _REQ[rid] = {'email': email, 'name': (body.name or '').strip(), 'company': company,
                 'province': (body.province or '').strip(),
                 'phone': (body.phone or '').strip(), 'code': code,
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
    # ID = 6 SỐ (100000–999999) — DB + subdomain hợp lệ; provision.sh exit 2 khi trùng.
    tid = None
    for _attempt in range(6):
        cand = str(secrets.randbelow(900000) + 100000)
        try:
            subprocess.run(
                ['bash', 'demo-data/packs/provision.sh',
                 cand, r['email'], r['company'], r['name'], r['province'], r.get('phone', '')],
                cwd=REPO_DIR, env=env, check=True,
                capture_output=True, timeout=PROVISION_TIMEOUT)
            tid = cand
            break
        except subprocess.CalledProcessError as e:
            if e.returncode == 2:   # id trùng → thử số khác
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
        print("PROVISION_FAILED: hết lượt thử id (toàn trùng)", flush=True)
        return _err(500, 'provision_failed', 'Lỗi tạo tài khoản, vui lòng liên hệ hỗ trợ.')

    dns_ok = _create_tenant_dns(tid)
    _REQ.pop(body.request_id, None)
    return {'ok': True, 'tenant_id': tid,
            'url': 'https://%s.%s' % (tid, BASE_DOMAIN), 'dns_ok': dns_ok}
