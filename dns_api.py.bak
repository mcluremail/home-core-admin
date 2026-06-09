import dns.query
import dns.update
import dns.zone
import dns.rdatatype
import dns.reversename
import dns.name
from flask import jsonify
import json, os, re, subprocess, html, time, urllib.request, logging, threading
from dhcp_api import get_dnsmasq_leases, get_lease_total
from reservations import list_reservations

logger = logging.getLogger('homecore')
def html_escape(s): return html.escape(s, quote=True)

def is_valid_hostname(name):
    if not name or len(name) > 253: return False
    if '..' in name or name.startswith('.') or name.endswith('.'): return False
    try:
        dns.name.from_text(name)
        return True
    except Exception:
        return False

def is_valid_ipv4(ip):
    try: return len(ip.split('.')) == 4 and all(0 <= int(p) <= 255 for p in ip.split('.'))
    except: return False

def ns_update(zone, name, rtype, data, action="add", ttl=3600):
    """Выполнение DNS-обновления через dnspython. Возвращает (успех, сообщение)."""
    def clean(s): return re.sub(r'[\r\n\x00]', '', str(s))
    if not is_valid_hostname(zone) or not is_valid_hostname(name):
        return False, "Invalid zone or name"
    if rtype not in ('A','CNAME','TXT','PTR','DHCID'):
        return False, "Invalid record type"
    if rtype == 'A' and not is_valid_ipv4(data):
        return False, "Invalid A record data"
    if rtype == 'CNAME' and not is_valid_hostname(data):
        return False, "Invalid CNAME data"

    zone = clean(zone).rstrip('.')
    name = clean(name).rstrip('.')
    rtype = clean(rtype).upper()

    zone_lower = zone.lower()
    name_lower = name.lower()
    if name_lower.endswith(f".{zone_lower}"):
        name = name[:-(len(zone)+1)]
    if not name or name_lower == zone_lower:
        name = "@"

    if name == "@":
        fqdn = dns.name.from_text(zone)
    else:
        fqdn = dns.name.from_text(f"{name}.{zone}.")

    try:
        update = dns.update.Update(zone)
        # >>> ИСПРАВЛЕНИЕ: корректное удаление DHCID без точного значения
        if action == "delete":
            if rtype == 'DHCID' and (not data or data.strip() == ''):
                # Удаляем весь RRset для DHCID
                update.delete(fqdn, rtype)
            else:
                if rtype == 'TXT' and data and not data.startswith('"'):
                    data = f'"{clean(data)}"'
                update.delete(fqdn, rtype, data)
        else:
            if rtype == 'TXT' and data and not data.startswith('"'):
                data = f'"{clean(data)}"'
            rdtype = dns.rdatatype.from_text(rtype)
            update.add(fqdn, ttl, rdtype, data)

        response = dns.query.tcp(update, '127.0.0.1', timeout=5)
        if response.rcode() != dns.rcode.NOERROR:
            return False, f"DNS update failed: {dns.rcode.to_text(response.rcode())}"
        return True, ""
    except dns.exception.Timeout:
        return False, "nsupdate timeout"
    except Exception as e:
        return False, str(e)

def find_ptr_zone(ip):
    try:
        rev = dns.reversename.from_address(ip)
        parts = str(rev).strip('.').split('.')
        if len(parts) >= 6 and parts[-2:] == ['in-addr', 'arpa']:
            return '.'.join(parts[1:]), parts[0]
    except:
        pass
    return None, None

# --- Сборщики зон ---
def get_zones_from_stats(settings):
    zones = {}
    host, port = settings["network"]["stats_host"], settings["network"]["stats_port"]
    for url in [f"http://{host}:{port}/json/v1/zones", f"http://{host}:{port}/json/v1", f"http://{host}:{port}/xml/v3/zones"]:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                raw = r.read().decode()
                if "json" in url:
                    data = json.loads(raw)
                    def extract(obj):
                        if isinstance(obj, dict):
                            if 'zones' in obj and isinstance(obj['zones'], list):
                                for item in obj['zones']:
                                    if isinstance(item, dict) and item.get('type') != 'forward':
                                        zones[item['name'].strip('.')] = True
                            for v in obj.values(): extract(v)
                    extract(data)
                else:
                    for blk in re.findall(r'<zone[^>]*>(.*?)</zone>', raw, re.DOTALL):
                        if 'type forward' not in blk:
                            m = re.search(r'<name[^>]*>(.*?)</name>', blk, re.DOTALL)
                            if m: zones[m.group(1).strip('.')] = True
                if zones: return list(zones.keys()), "Statistics channel"
        except: pass
    return [], None

def get_zones_from_checkconf():
    try:
        proc = subprocess.run(['/usr/sbin/named-checkconf', '-p'], capture_output=True, text=True, timeout=3)
        if proc.returncode != 0: return [], f"named-checkconf error: {proc.stderr.strip()}"
        found = []
        for m in re.finditer(r'zone\s+"([^"]+)"\s*(?:IN\s+)?{(.*?type\s+(master|slave|secondary).*?)};', proc.stdout, re.DOTALL):
            if 'type forward' not in m.group(2).lower(): found.append(m.group(1).strip('.'))
        return found, "named-checkconf"
    except FileNotFoundError: return [], "named-checkconf not found"
    except Exception as e: return [], str(e)

def get_zones_from_file(filename):
    if not os.path.exists(filename): return []
    try: content = open(filename).read()
    except: return []
    def expand(text, depth=0):
        if depth > 2: return text
        res = []
        for line in text.splitlines():
            m = re.match(r'\s*include\s+"([^"]+)"\s*;', line)
            if m:
                inc = m.group(1)
                if not inc.startswith('/'): inc = os.path.join(os.path.dirname(filename), inc)
                if os.path.exists(inc):
                    try: res.append(expand(open(inc).read(), depth+1))
                    except: pass
            else: res.append(line)
        return '\n'.join(res)
    expanded = expand(content)
    zones = []
    for m in re.finditer(r'zone\s+"([^"]+)"\s*(?:IN\s+)?{(.*?type\s+(master|slave|secondary).*?)};', expanded, re.DOTALL):
        if 'type forward' not in m.group(2).lower(): zones.append(m.group(1).strip('.'))
    return list(set(zones))

def get_zones_from_directory(zdir):
    if not os.path.isdir(zdir): return []
    return [f.rsplit('.',1)[0] for f in os.listdir(zdir) if f.endswith(('.zone','.db','.local','.rev')) and '.' in f.rsplit('.',1)[0]]

def get_bind_zones(settings):
    for desc, func in [
        ("статистический канал", get_zones_from_stats),
        ("named-checkconf", get_zones_from_checkconf),
        ("файлы конфигов", lambda: (get_zones_from_file(settings["paths"]["bind_conf"]), "named.conf.local")),
        ("сканирование директорий", lambda: (get_zones_from_directory(settings["paths"]["zones_dir"]), "directory"))
    ]:
        try: zones, src = func()
        except: continue
        if zones:
            ignored = set(settings["dns"]["ignored_zones"])
            filtered = sorted(z for z in zones if z and z not in ignored)
            if filtered: return filtered, src
    return ["mclure.ru"], "Static fallback"

# --- Кэш и API ---
_cache_lock = threading.Lock()
_cache = {"data": None, "timestamp": 0}
_CACHE_TTL = 30

def clear_dns_cache():
    with _cache_lock:
        _cache["data"] = None
        _cache["timestamp"] = 0

def api_data(settings):
    now = time.time()
    with _cache_lock:
        if _cache["data"] and (now - _cache["timestamp"]) < _CACHE_TTL:
            return jsonify(_cache["data"])

    zones = []
    b_src = "Statistics channel"
    b_info = {"source": b_src, "color": "var(--prim)"}
    try:
        host, port = settings["network"]["stats_host"], settings["network"]["stats_port"]
        with urllib.request.urlopen(f"http://{host}:{port}/json/v1", timeout=2) as r:
            js = json.loads(r.read().decode())
            cs = js.get('views',{}).get('_default',{}).get('resolver',{}).get('cachestats',{})
            h, m = cs.get('CacheHits',0), cs.get('CacheMisses',0)
            if h+m: b_info['cache_pct'] = round(h/(h+m)*100, 1)
            b_info['queries'] = js.get('nsstats',{}).get('Requestv4', 0)
            default_view = js.get('views', {}).get('_default', {})
            zones_json = default_view.get('zones', [])
            if zones_json:
                zones = [item['name'].strip('.') for item in zones_json if item.get('type') != 'forward']
                if zones:
                    ignored = set(settings["dns"]["ignored_zones"])
                    zones = sorted(z for z in zones if z and z not in ignored)
                else:
                    zones, b_src = get_bind_zones(settings)
            else:
                zones, b_src = get_bind_zones(settings)
            b_info.update({"source": b_src, "color": "var(--prim)" if "канал" in b_src else "#f59e0b"})
    except:
        zones, b_src = get_bind_zones(settings)
        b_info.update({"source": b_src, "color": "var(--prim)" if "канал" in b_src else "#f59e0b"})

    if not zones:
        zones, b_src = ["mclure.ru"], "Static fallback"
        b_info = {"source": b_src, "color": "#f59e0b"}

    recs, ptr_ips, raw_list, zone_stats = [], set(), [], {}
    pass  # импорт вынесен наверх
    lease_map = get_dnsmasq_leases(settings)
    dhcp_active = os.path.exists(settings["paths"]["dnsmasq_leases"])
    k_info = {"status": "АКТИВЕН" if dhcp_active else "ОТКЛЮЧЕН", "color": "var(--ok)" if dhcp_active else "var(--err)"}
    if dhcp_active: k_info['leases_total'] = len(lease_map)

    reservations = list_reservations()
    reserved_ips = {r['ip'] for r in reservations}

    for zone in zones:
        try:
            z_axfr = dns.zone.from_xfr(dns.query.xfr('127.0.0.1', zone, timeout=3))
            count = 0
            for name, node in z_axfr.nodes.items():
                fname = str(name.derelativize(z_axfr.origin)).strip('.')
                if fname == "@": fname = zone
                for rds in node.rdatasets:
                    rtype = dns.rdatatype.to_text(rds.rdtype)
                    if rtype == "SOA" and count > 0: continue
                    for rd in rds:
                        val = str(rd).strip('.')
                        if rtype == "PTR":
                            try: ptr_ips.add(str(dns.reversename.to_address(dns.name.from_text(str(name)+"."+zone+"."))))
                            except: pass
                        raw_list.append({"name": fname, "type": rtype, "data": val, "zone": zone, "ttl": rds.ttl, "dhcid": rtype=="DHCID"})
                        count += 1
            zone_stats[zone] = count
        except Exception as e:
            logger.warning(f"AXFR failed for {zone}: {e}")
            zone_stats[zone] = 0

    dynamic_hosts = {x['name'] for x in raw_list if x['dhcid']}
    for r in raw_list:
        if r['type'] == 'A' and r['data'] in reserved_ips:
            r['source'] = "Резервация"
        elif r['type'] == 'PTR':
            target_fqdn = r['data'].rstrip('.')
            r['source'] = "Динамическая" if target_fqdn in dynamic_hosts else "Статическая"
        else:
            r['source'] = "Динамическая" if r['name'] in dynamic_hosts else "Статическая"

        r['issue'] = "Нет PTR" if (r['type']=="A" and r['data'].startswith("192.168.") and r['data'] not in ptr_ips) else None
        r['mac'] = r['lease_progress'] = r['lease_remaining'] = r['lease_total'] = None

        if r['type'] == 'A' and r['data'] in lease_map:
            l = lease_map[r['data']]
            r['mac'] = l['mac']
            r['lease_remaining'] = int(l['remaining'])
            total = get_lease_total(r['data'], settings)
            if total:
                r['lease_total'] = total
                progress = max(0, min(100, int(((total - l['remaining']) / total) * 100))) if total > 0 else 0
                r['lease_progress'] = progress

        r['name_esc'], r['type_esc'], r['data_esc'], r['zone_esc'] = map(html_escape, [r['name'], r['type'], r['data'], r['zone']])
        if r.get('mac'): r['mac_esc'] = html_escape(r['mac'])
        recs.append(r)

    result = {"recs": recs, "kea": k_info, "bind": b_info, "zones": zone_stats}
    with _cache_lock:
        _cache["data"] = result
        _cache["timestamp"] = time.time()
    return jsonify(result)

def add_record(data, settings):
    if not all(k in data for k in ['zone','name','type','data']): return jsonify({"success": False, "error": "Missing fields"})
    ttl = int(data.get('ttl', settings["dns"]["default_ttl"]))
    if ttl < 0: return jsonify({"success": False, "error": "Invalid TTL"})
    ok, err = ns_update(data['zone'], data['name'], data['type'], data['data'], "add", ttl)
    if ok and data.get('ptr', settings["dns"]["auto_ptr"]) and data['type']=='A':
        try:
            pz, pn = find_ptr_zone(data['data'])
            if pz and pn:
                ok_ptr, err_ptr = ns_update(pz, pn, "PTR", f"{data['name']}.{data['zone']}.", "add", ttl)
                if not ok_ptr:
                    logger.warning(f"add_record: PTR creation failed for {data['data']}: {err_ptr}")
        except Exception as e:
            logger.warning(f"add_record: PTR exception for {data['data']}: {e}")
    clear_dns_cache()
    return jsonify({"success": ok, "error": err})

def edit_record(data, settings):
    if not all(k in data for k in ['zone','name','type','old_data','new_data']): return jsonify({"success": False, "error": "Missing fields"})
    ttl = int(data.get('ttl', settings["dns"]["default_ttl"]))
    if ttl < 0: return jsonify({"success": False, "error": "Invalid TTL"})
    ok_del, err_del = ns_update(data['zone'], data['name'], data['type'], data['old_data'], "delete")
    if not ok_del: return jsonify({"success": False, "error": f"Не удалось удалить старую запись: {err_del}"})
    ok_add, err_add = ns_update(data['zone'], data['name'], data['type'], data['new_data'], "add", ttl)
    if not ok_add:
        ns_update(data['zone'], data['name'], data['type'], data['old_data'], "add", ttl)
        return jsonify({"success": False, "error": f"Не удалось создать новую запись: {err_add}"})
    # обновление PTR при редактировании A-записи (всегда)
    if data['type'] == 'A':
        # удаляем старый PTR (если был) — только если IP изменился
        if data.get('old_data') and data['old_data'] != data['new_data']:
            try:
                old_ptr_zone, old_ptr_num = find_ptr_zone(data['old_data'])
                if old_ptr_zone and old_ptr_num:
                    ok_ptr, err_ptr = ns_update(old_ptr_zone, old_ptr_num, "PTR", f"{data['name']}.{data['zone']}.", "delete")
                    if not ok_ptr:
                        logger.warning(f"edit_record: old PTR delete failed for {data['old_data']}: {err_ptr}")
            except Exception as e:
                logger.warning(f"edit_record: old PTR exception for {data['old_data']}: {e}")
        # создаём новый PTR (если включено auto_ptr)
        if data.get('ptr', settings["dns"]["auto_ptr"]):
            try:
                pz, pn = find_ptr_zone(data['new_data'])
                if pz and pn:
                    ok_ptr, err_ptr = ns_update(pz, pn, "PTR", f"{data['name']}.{data['zone']}.", "add", ttl)
                    if not ok_ptr:
                        logger.warning(f"edit_record: new PTR creation failed for {data['new_data']}: {err_ptr}")
            except Exception as e:
                logger.warning(f"edit_record: new PTR exception for {data['new_data']}: {e}")
    clear_dns_cache()
    return jsonify({"success": True, "error": ""})

def delete_record(data, settings):
    if not all(k in data for k in ['zone','name','type','data']): return jsonify({"success": False, "error": "Missing fields"})
    ok, _ = ns_update(data['zone'], data['name'], data['type'], data['data'], "delete")
    if ok:
        # Если удаляется A-запись, пытаемся удалить и DHCID, чтобы убрать динамический хост
        if data['type'] == 'A':
            try:
                ns_update(data['zone'], data['name'], 'DHCID', '', "delete")
            except:
                pass
        clear_dns_cache()
    return jsonify({"success": ok})

def fix_missing_ptr(data, settings):
    if not all(k in data for k in ['zone','name','data']): return jsonify({"success": False, "error": "Missing fields"})
    pz, pn = find_ptr_zone(data['data'])
    if not pz or not pn: return jsonify({"success": False, "error": "Cannot determine reverse zone"})
    ok, err = ns_update(pz, pn, "PTR", f"{data['name']}.", "add", int(data.get('ttl', settings["dns"]["default_ttl"])))
    if ok:
        clear_dns_cache()
    else:
        logger.warning(f"fix_missing_ptr: PTR creation failed for {data['data']}: {err}")
    return jsonify({"success": ok, "error": err})

def validate_zone(data, settings):
    zone = data.get('zone','')
    if not zone: return jsonify({"success": False, "error": "Zone name required"})
    return jsonify({"success": True, "output": "Validation not implemented yet"})

def debug(settings):
    return jsonify({
        "Статистический канал": {"data": get_zones_from_stats(settings)[0], "source": "Stats"},
        "named-checkconf": {"data": get_zones_from_checkconf()[0], "source": "Checkconf"},
        "Файл named.conf": {"data": get_zones_from_file(settings["paths"]["bind_conf"]), "source": "File"},
        "Сканирование /var/named": {"data": get_zones_from_directory(settings["paths"]["zones_dir"]), "source": "Dir"}
    })
