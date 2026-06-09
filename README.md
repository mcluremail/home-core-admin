# Home Core Admin

Web-based administration interface for managing **BIND9 DNS** and **dnsmasq DHCP** in a local network.

## Features

### DNS Management (BIND9)
- View all DNS zones and records via AXFR
- Add, edit, and delete DNS records (A, AAAA, CNAME, TXT, PTR, MX, SRV, NS, SOA, DHCID)
- Automatic PTR record creation and cleanup on A record changes
- In-browser **DNS Lookup** tool — query any record type directly via BIND
- Wildcard record support
- Automatic zone discovery via BIND statistics channel, named-checkconf, or file scanning
- Zone validation

### DHCP Management (dnsmasq)
- View active DHCP leases with real-time color-coded progress bars
- Add, edit, and delete DHCP reservations with search/filter
- Create DHCP reservations directly from dynamic DNS entries
- Automatic dnsmasq reload on configuration changes
- Lease time parsing from dhcp-range directives (including tagged ranges)

### Monitoring
- BIND statistics: cache hit/miss ratio, total queries
- Active DHCP lease count with expiration indicators
- **Paginated audit log** with search and navigation
- Missing PTR detection and one-click creation

### Security
- Password-protected login (scrypt hashing via Werkzeug)
- Session-based authentication
- CSRF token protection for all modifying operations
- HTTP-only session cookies
- **Password change** via web interface (Settings → Security)
- Audit logging of all administrative actions

### UI/UX
- Responsive layout with sidebar navigation
- Zone grouping (forward/reverse) with **hover preview** showing record types
- **Search with text highlighting** across names and data
- Source filters (static, dynamic, reserved)
- Filter state preserved in localStorage
- **Dark/light/system theme** support with improved dark contrast
- Auto-refresh with configurable interval
- **Delete confirmation** dialogs, **Esc to close** / **Enter to submit** modals
- DNS record type indicators and PTR status badges
- Improved toast notifications with close button and hover-pause

## Dependencies

- **Python** 3.10+
- **Flask** — web framework
- **Werkzeug** — password hashing
- **dnspython** — DNS update, zone transfer (AXFR), and DNS lookups
- **uWSGI** — application server (production)

### System dependencies
- **BIND9** (named) with:
  - Statistics channel enabled (port 8053 recommended)
  - Zone transfer allowed from your app server IP
  - Dynamic DNS updates allowed from your app server IP
- **dnsmasq** (optional, for DHCP features) with:
  - Lease file at /var/lib/misc/dnsmasq.leases
  - dhcp-range configured with explicit lease times

## Installation

### 1. Install system packages

```bash
# Arch Linux
pacman -S python python-flask python-werkzeug python-dnspython nginx uwsgi uwsgi-plugin-python bind dnsmasq

# Debian/Ubuntu
apt install python3 python3-flask python3-werkzeug python3-dnspython nginx uwsgi uwsgi-plugin-python3 bind9 dnsmasq
```

### 2. Clone and setup

```bash
git clone https://github.com/mcluremail/home-core-admin.git /srv/http/dns_monitor
cd /srv/http/dns_monitor
```

### 3. Configure uWSGI

Create /etc/uwsgi/dns_monitor.ini:

```ini
[uwsgi]
chdir = /srv/http/dns_monitor
module = app:app
plugins = python

master = true
processes = 3
socket = /run/uwsgi/dns_monitor.sock
chmod-socket = 660
chown-socket = http:http
vacuum = true
die-on-term = true

uid = http
gid = http
```

Enable and start:

```bash
systemctl enable uwsgi@dns_monitor
systemctl start uwsgi@dns_monitor
```

### 4. Configure nginx

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/run/uwsgi/dns_monitor.sock;
    }

    location /static/ {
        alias /srv/http/dns_monitor/static/;
    }
}
```

### 5. Initial setup

On first startup, the application generates default credentials:

- **Password:** admin

Change it immediately via **Settings → Security → Сменить пароль** after logging in.

## Configuration

Settings are stored in settings.json and editable via the web interface. Key options:

| Section | Key | Default | Description |
|---|---|---|---|
| security | secret_key | auto-generated | Flask session signing key |
| security | session_samesite | Lax | SameSite cookie policy |
| security | session_httponly | true | HTTP-only session cookies |
| network | bind_host | 127.0.0.1 | BIND server for nsupdate and AXFR |
| network | stats_host | 127.0.0.1 | BIND statistics channel host |
| network | stats_port | 8053 | BIND statistics channel port |
| paths | bind_conf | /etc/named.conf.local | BIND configuration file |
| paths | zones_dir | /var/named/ | BIND zone files directory |
| paths | audit_log | audit.log | Audit log path |
| paths | dnsmasq_leases | /var/lib/misc/dnsmasq.leases | dnsmasq lease file |
| paths | dnsmasq_conf | /etc/dnsmasq.conf | dnsmasq configuration file |
| dns | default_ttl | 3600 | Default TTL for new records (seconds) |
| dns | auto_ptr | true | Auto-create PTR records for A records |
| dns | ignored_zones | [...] | Zones hidden from the UI |
| ui | refresh_interval | 30 | Auto-refresh interval (seconds) |
| ui | theme | system | UI theme: light, dark, or system |

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | / | No | Main page |
| GET | /api/data | No | All DNS records, zones, DHCP leases, stats |
| GET | /api/dns-lookup | No | DNS query via BIND (?name=&type=) |
| POST | /api/login | No | Authenticate and create session |
| POST | /api/logout | CSRF | End session |
| GET | /api/settings | Session | Get current settings |
| POST | /api/settings | Session+CSRF | Update settings |
| POST | /api/change-password | Session+CSRF | Change admin password |
| GET | /api/csrf-token | No | Get CSRF token |
| POST | /api/add | Session+CSRF | Add DNS record |
| POST | /api/edit | Session+CSRF | Edit DNS record |
| POST | /api/delete | Session+CSRF | Delete DNS record |
| POST | /api/fix-missing-ptr | Session+CSRF | Create missing PTR record |
| POST | /api/validate-zone | Session+CSRF | Validate zone |
| GET | /api/reservations | No | List DHCP reservations |
| POST | /api/reservations | Session+CSRF | Add DHCP reservation |
| DELETE | /api/reservations/<mac> | Session+CSRF | Delete DHCP reservation |
| PUT | /api/reservations/<mac> | Session+CSRF | Update DHCP reservation |
| POST | /api/create-reservation | Session+CSRF | Create reservation from dynamic DNS |
| GET | /api/audit | No | Audit log (supports ?offset=&limit=&q=) |
| GET | /api/debug | No | Zone source debug info |

## Remote BIND Setup

The application communicates with BIND via:

1. **Dynamic DNS updates** (nsupdate) — TCP port 53
2. **Zone transfers** (AXFR) — TCP port 53
3. **Statistics channel** — HTTP port (custom, default 8053)

Set the target BIND server IP in Settings → Network → `bind_host`, or directly in settings.json:

```json
{
  "network": {
    "bind_host": "192.168.1.4",
    "stats_host": "192.168.1.4",
    "stats_port": 8053
  }
}
```

### BIND configuration (on the remote DNS server)

```conf
options {
    listen-on { 127.0.0.1; 192.168.1.0/24; };
    allow-query { localhost; 192.168.1.0/24; };
    allow-update { localhost; 192.168.1.100; };  # app server IP
};

statistics-channels {
    inet 192.168.1.4 port 8053 allow { 192.168.1.100; };
};

zone "mclure.ru" IN {
    type master;
    file "/var/named/mclure.ru.zone";
    allow-transfer { localhost; 192.168.1.100; };  # app server IP
};
```

## License

This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](LICENSE) file for details.

## Author

**Taurus McLure** — taurus@mclure.ru