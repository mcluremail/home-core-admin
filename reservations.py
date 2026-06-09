import os, re, logging, subprocess, threading
logger = logging.getLogger('homecore')
RESERVATIONS_FILE = "/etc/dnsmasq.d/reservations.conf"

# Блокировка для синхронизации операций чтения/записи
_file_lock = threading.Lock()

def _read_file():
    with _file_lock:
        if not os.path.exists(RESERVATIONS_FILE):
            return []
        with open(RESERVATIONS_FILE, 'r') as f:
            return f.readlines()

def _write_file(lines):
    with _file_lock:
        with open(RESERVATIONS_FILE, 'w') as f:
            f.writelines(lines)
    _reload_dnsmasq()

def _reload_dnsmasq():
    """Перезагрузить dnsmasq через systemctl reload, без сигналов."""
    try:
        subprocess.run(['systemctl', 'reload', 'dnsmasq'], check=True, capture_output=True, text=True)
        logger.info("dnsmasq перезагружен через systemctl")
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Не удалось перезагрузить dnsmasq через systemctl")
        # Альтернатива: попытка SIGHUP, но только после проверки
        pid_file = "/run/dnsmasq/dnsmasq.pid"
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
            try:
                pid = int(pid)
                with open(f'/proc/{pid}/comm', 'r') as f:
                    proc_name = f.read().strip()
                if proc_name.startswith('dnsmasq'):
                    os.kill(pid, 1)
                    logger.info(f"dnsmasq перезагружен через SIGHUP (PID {pid})")
                else:
                    logger.warning(f"PID {pid} принадлежит процессу {proc_name}, не dnsmasq")
            except Exception as e:
                logger.error(f"Не удалось перезагрузить dnsmasq по PID: {e}")

def list_reservations():
    lines = _read_file()
    reservations = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'): continue
        m = re.match(r'dhcp-host\s*=\s*(.+)', line)
        if not m: continue
        parts = [p.strip() for p in m.group(1).split(',')]
        if len(parts) < 2: continue
        mac = parts[0].lower()
        ip = parts[1]
        hostname = parts[2] if len(parts) > 2 and parts[2].lower() != 'infinite' else ''
        reservations.append({"mac": mac, "ip": ip, "hostname": hostname})
    return reservations

def add_reservation(mac, ip, hostname=""):
    mac = mac.lower()
    current = list_reservations()
    for r in current:
        if r['mac'] == mac:
            return False, f"MAC-адрес {mac} уже зарезервирован"
    line = f"dhcp-host={mac},{ip}"
    if hostname:
        line += f",{hostname}"
    line += "\n"
    lines = _read_file()
    lines.append(line)
    _write_file(lines)
    return True, "Резервация добавлена"

def delete_reservation(mac):
    mac = mac.lower()
    lines = _read_file()
    new_lines = []
    found = False
    for line in lines:
        if re.match(r'dhcp-host\s*=\s*' + re.escape(mac) + r'[,\s]', line.strip()):
            found = True
            continue
        new_lines.append(line)
    if not found:
        return False, f"Резервация для {mac} не найдена"
    _write_file(new_lines)
    return True, "Резервация удалена"

def update_reservation(old_mac, new_mac, ip, hostname=""):
    old_mac = old_mac.lower()
    new_mac = new_mac.lower()
    lines = _read_file()
    updated = False
    for i, line in enumerate(lines):
        if re.match(r'dhcp-host\s*=\s*' + re.escape(old_mac) + r'[,\s]', line.strip()):
            new_line = f"dhcp-host={new_mac},{ip}"
            if hostname:
                new_line += f",{hostname}"
            new_line += "\n"
            lines[i] = new_line
            updated = True
            break
    if not updated:
        return False, f"Резервация с MAC {old_mac} не найдена"
    _write_file(lines)
    return True, "Резервация обновлена"
