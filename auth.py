import os, secrets, logging
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, jsonify

logger = logging.getLogger('homecore')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({"success": False, "error": "Требуется авторизация"}), 401
        return f(*args, **kwargs)
    return decorated

def _pass_file():
    from config import get_settings
    path = get_settings().get("paths", {}).get("audit_log", "")
    if path:
        return os.path.join(os.path.dirname(path), "admin.pass")
    return os.path.join(os.path.dirname(__file__), "admin.pass")

def _read_hash():
    pass_file = _pass_file()
    if os.path.exists(pass_file):
        try:
            with open(pass_file, 'r') as f:
                h = f.read().strip()
                if h and (h.startswith('scrypt:') or h.startswith('pbkdf2:') or h.startswith('sha256:')):
                    return h
        except Exception as e:
            print(f"Error reading {pass_file}: {e}")
    return None

def _write_hash(h):
    pass_file = _pass_file()
    with open(pass_file, 'w') as f:
        f.write(h)
    os.chmod(pass_file, 0o600)

def ensure_admin_pass():
    h = _read_hash()
    if h:
        return h
    default_password = "admin"
    default_hash = generate_password_hash(default_password)
    print("WARNING: admin.pass not found. Default password: admin")
    _write_hash(default_hash)
    return default_hash

def init_auth(app_dir):
    # ensure admin.pass exists on startup
    ensure_admin_pass()

def check_auth_struct():
    return _read_hash()

def check_auth(password) -> bool:
    h = _read_hash()
    if not h:
        return False
    return check_password_hash(h, password)

def change_password(new_password):
    h = generate_password_hash(new_password)
    _write_hash(h)
    return True
