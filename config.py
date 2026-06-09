import os
import json
import copy
import threading
import time
import logging
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "security": {"secret_key": "HomeCore-Secret-Key-Change-Me", "session_samesite": "Lax", "session_httponly": True},
    "network": {"stats_host": "127.0.0.1", "stats_port": 8053},
    "paths": {"bind_conf": "/etc/named.conf.local", "zones_dir": "/var/named/", "audit_log": os.path.join(BASE_DIR, "audit.log"), "dnsmasq_leases": "/var/lib/misc/dnsmasq.leases"},
    "dns": {"ignored_zones": ["localhost", "localhost.localdomain", "localhost.ip6", "127.in-addr.arpa", "0.in-addr.arpa", "255.in-addr.arpa", "0.0.127.in-addr.arpa", "127.0.0", "127.0.0.0", "127.0.0.1", "rpz.local", "rpz", "authors.bind", "hostname.bind", "version.bind", "id.server"], "default_ttl": 3600, "auto_ptr": True},
    "ui": {"refresh_interval": 30, "theme": "system"}
}

def deep_merge(base, override):
    out = copy.deepcopy(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out

_lock = threading.Lock()
_cached_settings = None
_cached_at = 0.0
_CACHE_TTL = 5.0

def get_settings():
    global _cached_settings, _cached_at
    now = time.time()
    with _lock:
        if _cached_settings and (now - _cached_at) < _CACHE_TTL:
            return copy.deepcopy(_cached_settings)
        
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    _cached_settings = deep_merge(DEFAULT_SETTINGS, json.load(f))
            except Exception as e:
                print(f"⚠ Ошибка чтения settings.json: {e}")
                _cached_settings = copy.deepcopy(DEFAULT_SETTINGS)
        else:
            _cached_settings = copy.deepcopy(DEFAULT_SETTINGS)
            
        _cached_at = now
        return copy.deepcopy(_cached_settings)

def save_settings(new_settings):
    global _cached_settings, _cached_at
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_settings, f, indent=2, ensure_ascii=False)
    os.chmod(SETTINGS_FILE, 0o600)
    with _lock:
        _cached_settings = copy.deepcopy(new_settings)
        _cached_at = time.time()

def init_logging(log_path=None):
    if log_path is None:
        log_path = get_settings()["paths"]["audit_log"]
    
    logger = logging.getLogger('homecore')
    # Удаляем старые обработчики, чтобы не дублировать
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
