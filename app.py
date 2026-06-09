import os, secrets, logging
from flask import Flask, render_template, jsonify, request, session
from werkzeug.security import check_password_hash
from functools import wraps

# Импортируем модули авторизации и конфигурации
from auth import init_auth, login_required, check_auth_struct
from config import get_settings, save_settings, init_logging, SETTINGS_FILE
# >>> ИСПРАВЛЕНИЕ: добавлен clear_dns_cache
from dns_api import api_data, add_record, edit_record, delete_record, fix_missing_ptr, validate_zone, debug as api_debug, clear_dns_cache
from reservations import list_reservations, add_reservation, delete_reservation, update_reservation

app = Flask(__name__)
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- НАСТРОЙКИ ----------
# Загружаем настройки, теперь через config.get_settings() (он же используется в dns_api)
settings = get_settings()
app.secret_key = settings["security"]["secret_key"]
app.config['SESSION_COOKIE_SAMESITE'] = settings["security"]["session_samesite"]
app.config['SESSION_COOKIE_HTTPONLY'] = settings["security"]["session_httponly"]

# Инициализируем авторизацию (загрузка хеша пароля)
init_auth(APP_DIR)

# Настройка логгера с ротацией
logger = init_logging(settings["paths"]["audit_log"])

# Проверка доступности ключевых путей при старте
def check_paths():
    paths_to_check = {
        "named.conf.local": settings["paths"]["bind_conf"],
        "zones_dir": settings["paths"]["zones_dir"],
        "dnsmasq.leases": settings["paths"]["dnsmasq_leases"]
    }
    for name, path in paths_to_check.items():
        if name == "zones_dir":
            if not os.path.isdir(path):
                logger.warning(f"Директория зон не найдена: {path}")
        else:
            if not os.path.exists(path):
                logger.warning(f"Файл {name} не найден: {path}")
check_paths()

# ---------- CSRF защита ----------
def csrf_token_required(f):
    """Декоратор для проверки CSRF-токена в заголовке X-CSRF-Token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Для GET-запросов не требуется
        if request.method == 'GET':
            return f(*args, **kwargs)
        token = request.headers.get('X-CSRF-Token', '')
        if not token or token != session.get('csrf_token'):
            return jsonify({"success": False, "error": "CSRF validation failed"}), 403
        return f(*args, **kwargs)
    return decorated

# ---------- МАРШРУТЫ ----------

@app.route('/api/data')
def api_data_route():
    # data api не требует авторизации, только CSRF для модифицирующих
    return api_data(settings)

@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings_route():
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
@login_required
@csrf_token_required
def update_settings_route():
    global settings
    try:
        new_s = request.json
        if not new_s:
            return jsonify({"success": False, "error": "Empty payload"}), 400
        if not (10 <= int(new_s.get("ui", {}).get("refresh_interval", 30)) <= 300):
            return jsonify({"success": False, "error": "Интервал: 10-300 сек"}), 400
        if not (60 <= int(new_s.get("dns", {}).get("default_ttl", 3600)) <= 86400):
            return jsonify({"success": False, "error": "TTL: 60-86400 сек"}), 400
        if not (1 <= int(new_s.get("network", {}).get("stats_port", 8053)) <= 65535):
            return jsonify({"success": False, "error": "Неверный порт"}), 400

        old_secret, old_log = settings["security"]["secret_key"], settings["paths"]["audit_log"]
        merged = deep_merge(settings, new_s)
        save_settings(merged)
        settings = merged

        app.config['SESSION_COOKIE_SAMESITE'] = settings["security"]["session_samesite"]
        app.config['SESSION_COOKIE_HTTPONLY'] = settings["security"]["session_httponly"]

        restart_needed = False
        if merged["security"]["secret_key"] != old_secret:
            app.secret_key = merged["security"]["secret_key"]
            restart_needed = True
        if merged["paths"]["audit_log"] != old_log:
            # переинициализируем логгер
            global logger
            logger = init_logging(merged["paths"]["audit_log"])
            restart_needed = True

        logger.info(f"SETTINGS UPDATED | IP:{request.remote_addr} | Restart: {restart_needed}")
        return jsonify({"success": True, "restart_needed": restart_needed})
    except Exception as e:
        logger.error(f"SETTINGS ERROR | IP:{request.remote_addr} | {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    pwd = request.json.get('password', '') if request.json else ''
    if check_password_hash(check_auth_struct(), pwd):
        session['authenticated'] = True
        # Генерируем CSRF токен после успешного входа
        session['csrf_token'] = secrets.token_hex(32)
        logger.info(f"LOGIN | IP:{request.remote_addr}")
        return jsonify({"success": True, "csrf_token": session['csrf_token']})
    return jsonify({"success": False, "error": "Неверный пароль"}), 401

@app.route('/api/logout', methods=['POST'])
@csrf_token_required
def api_logout():
    session.pop('authenticated', None)
    session.pop('csrf_token', None)
    return jsonify({"success": True})

@app.route('/api/add', methods=['POST'])
@login_required
@csrf_token_required
def api_add():
    return add_record(request.json, settings)

@app.route('/api/edit', methods=['POST'])
@login_required
@csrf_token_required
def api_edit():
    return edit_record(request.json, settings)

@app.route('/api/delete', methods=['POST'])
@login_required
@csrf_token_required
def api_delete():
    return delete_record(request.json, settings)

@app.route('/api/fix-missing-ptr', methods=['POST'])
@login_required
@csrf_token_required
def api_fix_ptr():
    return fix_missing_ptr(request.json, settings)

@app.route('/api/validate-zone', methods=['POST'])
@login_required
@csrf_token_required
def api_validate_zone():
    return validate_zone(request.json, settings)

@app.route('/api/reservations', methods=['GET'])
def api_reservations():
    return jsonify({"reservations": list_reservations()})

@app.route('/api/reservations', methods=['POST'])
@login_required
@csrf_token_required
def api_add_reservation():
    data = request.json
    mac = data.get('mac', '').strip().lower()
    ip = data.get('ip', '').strip()
    hostname = data.get('hostname', '').strip()
    if not mac or not ip:
        return jsonify({"success": False, "error": "MAC и IP обязательны"})
    ok, msg = add_reservation(mac, ip, hostname)
    if ok:
        # >>> ИСПРАВЛЕНИЕ: сброс кэша DNS после изменения резервации
        clear_dns_cache()
        logger.info(f"RESERVATION ADD | IP:{request.remote_addr} | {mac} -> {ip}")
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "error": msg})

@app.route('/api/reservations/<mac>', methods=['DELETE'])
@login_required
@csrf_token_required
def api_delete_reservation(mac):
    ok, msg = delete_reservation(mac)
    if ok:
        # >>> ИСПРАВЛЕНИЕ: сброс кэша
        clear_dns_cache()
        logger.info(f"RESERVATION DELETE | IP:{request.remote_addr} | {mac}")
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "error": msg})

@app.route('/api/reservations/<mac>', methods=['PUT'])
@login_required
@csrf_token_required
def api_update_reservation(mac):
    data = request.json
    new_mac = data.get('mac', '').strip().lower()
    ip = data.get('ip', '').strip()
    hostname = data.get('hostname', '').strip()
    if not new_mac or not ip:
        return jsonify({"success": False, "error": "MAC и IP обязательны"})
    ok, msg = update_reservation(mac, new_mac, ip, hostname)
    if ok:
        # >>> ИСПРАВЛЕНИЕ: сброс кэша
        clear_dns_cache()
        logger.info(f"RESERVATION UPDATE | {mac} -> {new_mac}, {ip}")
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "error": msg})

@app.route('/api/create-reservation', methods=['POST'])
@login_required
@csrf_token_required
def api_create_reservation():
    data = request.json
    zone = data.get('zone', '')
    name = data.get('name', '')
    ip = data.get('ip', '')
    mac = data.get('mac', '').strip().lower()
    hostname = data.get('hostname', name)
    if not mac or not ip:
        return jsonify({"success": False, "error": "MAC и IP обязательны"})
    from dns_api import ns_update
    ns_update(zone, name, 'DHCID', '', 'delete')
    ok, msg = add_reservation(mac, ip, hostname)
    if ok:
        # >>> ИСПРАВЛЕНИЕ: сброс кэша
        clear_dns_cache()
        logger.info(f"RESERVATION CREATED FROM DYNAMIC | {zone}/{name} -> {mac}/{ip}")
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "error": msg})

@app.route('/api/audit')
def get_audit():
    try:
        log_path = settings["paths"]["audit_log"]
        if not os.path.exists(log_path):
            return jsonify({"lines": []})
        with open(log_path, 'r') as f:
            return jsonify({"lines": [l.strip() for l in f.readlines()[-50:]]})
    except:
        return jsonify({"lines": []})

@app.route('/api/debug')
def debug_route():
    return api_debug(settings)

@app.route('/')
def index():
    with open(os.path.join(APP_DIR, 'templates', 'index.html'), 'r', encoding='utf-8') as f:
        return render_template('index.html', is_auth=session.get('authenticated', False))

@app.route('/api/csrf-token', methods=['GET'])
def get_csrf_token():
    if session.get('authenticated'):
        token = session.get('csrf_token')
        if not token:
            token = secrets.token_hex(32)
            session['csrf_token'] = token
        return jsonify({"authenticated": True, "csrf_token": token})
    return jsonify({"authenticated": False})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80)   # слушаем только на localhost для безопасности
