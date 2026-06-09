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

# Глобальная переменная для хранения хеша пароля
_admin_pass_hash = None

def load_admin_pass_hash(app_dir):
    pass_file = os.path.join(app_dir, "admin.pass")
    if os.path.exists(pass_file):
        try:
            with open(pass_file, 'r') as f:
                h = f.read().strip()
                if h and (h.startswith('scrypt:') or h.startswith('pbkdf2:') or h.startswith('sha256:')):
                    return h
        except Exception as e:
            print(f"⚠ Ошибка чтения файла хэша {pass_file}: {e}")
    # Пароль по умолчанию
    default_password = "admin"
    default_hash = generate_password_hash(default_password)
    print("⚠ WARNING: admin.pass не найден. Пароль по умолчанию: admin")
    with open(pass_file, 'w') as f:
        f.write(default_hash)
    os.chmod(pass_file, 0o600)
    return default_hash

def init_auth(app_dir):
    global _admin_pass_hash
    _admin_pass_hash = load_admin_pass_hash(app_dir)

def check_auth(password) -> bool:
    return check_password_hash(_admin_pass_hash, password)

def check_auth_struct():
    """Возвращает хеш для внешней проверки (используется в app.py для логина)."""
    return _admin_pass_hash
