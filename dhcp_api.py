import os, time, re

def get_dnsmasq_leases(settings):
    lease_path = settings["paths"]["dnsmasq_leases"]
    leases = {}
    if not os.path.exists(lease_path):
        return leases
    now = time.time()
    try:
        with open(lease_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                parts = line.split()
                if len(parts) < 5: continue
                expire_ts = int(parts[0])
                mac = parts[1]
                ip = parts[2]
                remaining = max(0, expire_ts - now)
                leases[ip] = {'mac': mac, 'expire_ts': expire_ts, 'remaining': remaining}
    except Exception: pass
    return leases

def get_lease_total(ip, settings):
    """Определяет общую длительность аренды (в секундах) для подсети,
к которой принадлежит IP, на основе конфигурационного файла dnsmasq.
"""
    conf_path = settings.get("paths", {}).get("dnsmasq_conf", "/etc/dnsmasq.conf")
    if not os.path.exists(conf_path):
        return None
    try:
        with open(conf_path, "r") as f:
            config = f.read()
    except Exception:
        return None

    try:
        ip_parts = [int(x) for x in ip.split(".")]
        if len(ip_parts) != 4:
            return None
    except:
        return None

    for line in config.splitlines():
        line = line.strip()
        if not line.startswith("dhcp-range"):
            continue
        range_str = line[len("dhcp-range="):]
        parts = [p.strip() for p in range_str.split(",")]

        # static-диапазоны без lease time пропускаем
        if "static" in parts:
            continue

        # Сдвигаем индекс если есть тег set:/tag:
        idx = 0
        if parts[0].startswith("set:") or parts[0].startswith("tag:"):
            idx = 1

        if len(parts) < idx + 3:
            continue

        start_ip = parts[idx]
        end_ip = parts[idx + 1]

        # Третий элемент после IP: может быть маской или lease time
        if len(parts) > idx + 3 and "." in parts[idx + 2]:
            lease_idx = idx + 3
        else:
            lease_idx = idx + 2

        if lease_idx >= len(parts):
            continue

        time_str = parts[lease_idx]

        try:
            start_octets = [int(x) for x in start_ip.split(".")]
            end_octets = [int(x) for x in end_ip.split(".")]
            in_range = True
            for i in range(4):
                if ip_parts[i] < start_octets[i] or ip_parts[i] > end_octets[i]:
                    in_range = False
                    break
            if in_range:
                duration = parse_duration(time_str)
                if duration:
                    return duration
        except Exception:
            continue
    return None
def parse_duration(s):
    s = s.strip().lower()
    if s.endswith('h'):
        try:
            return int(s[:-1]) * 3600
        except:
            return None
    elif s.endswith('m'):
        try:
            return int(s[:-1]) * 60
        except:
            return None
    elif s.endswith('s'):
        try:
            return int(s[:-1])
        except:
            return None
    else:
        try:
            return int(s)
        except:
            return None
