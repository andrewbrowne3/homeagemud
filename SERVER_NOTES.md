# HomageMUD Server Notes

> **Note on credentials.** The SSH password is deliberately *not* in this file.
> This repository has a GitHub remote, and a committed password is published to
> anyone with read access and stays in git history after it is deleted. The
> working copy of the credentials lives outside the repo at
> `~/homagemud_server_notes.md`. That password is also flagged there as needing
> to be changed, and it doubles as the sudo password.


## Server Details

| Field | Value |
|-------|-------|
| **Hostname** | `homagemud.com` |
| **IP** | `158.69.199.228` |
| **OS** | Ubuntu 24.04.4 LTS |
| **CPU** | 6 cores |
| **RAM** | 12 GB (~1 GB used) |
| **Disk** | 96 GB (7.3 GB used / 89 GB free) |
| **Web Server** | Apache 2.4.58 |
| **SSH** | OpenSSH on port 22 |

## Hosting Provider

- **Pocket MUD** (pocketmud.com) - CoffeeMUD / MUD hosting service
- **Owner:** Marisa Giancarla (username: `fstltna`)
- **Contact:** [Pocket MUD Support Portal](https://pocketmud.com/index.php/contact-us/support-portal/) or [Facebook](https://www.facebook.com/pocketmud/)
- **Account owner email:** garrettmosley@outlook.com

## SSH Access

```bash
ssh mudowner@158.69.199.228
# or
ssh mudowner@homagemud.com
```

- **Username:** mudowner
- **Password:** not stored here — see `~/homagemud_server_notes.md` (local, outside the repo).
- **Note:** the password is reused for sudo and is flagged as needing to be changed.

## MUD Engine — Evennia (NOT CoffeeMUD)

Despite being hosted on Pocket MUD (a CoffeeMUD hosting provider), this server is running **Evennia** — a Python/Django/Twisted-based MUD framework.

- **Evennia docs:** https://www.evennia.com/docs/latest/
- **Java is NOT installed** (CoffeeMUD is Java-based, Evennia is Python-based)

## Directory Layout

```
/home/mudowner/muddev/
├── evennia/     # Evennia engine source (394 MB)
├── evenv/       # Python 3.12 virtual environment (177 MB)
└── mygame/      # The actual game project (27 MB)
```

### mygame/ Structure

```
mygame/
├── README.md
├── commands/
│   ├── command.py              # Custom command definitions
│   └── default_cmdsets.py      # Command set configuration
├── server/
│   └── conf/
│       ├── settings.py         # Main config (SERVERNAME = "mygame", web port 4001)
│       ├── secret_settings.py  # Secret/override settings
│       ├── at_initial_setup.py
│       ├── at_server_startstop.py
│       ├── connection_screens.py
│       └── (other conf files)
├── typeclasses/
│   ├── accounts.py
│   ├── characters.py
│   ├── rooms.py
│   ├── exits.py
│   ├── objects.py
│   ├── channels.py
│   └── scripts.py
├── web/
│   ├── admin/
│   ├── webclient/
│   ├── website/
│   ├── static/
│   └── templates/
└── world/
    ├── help_entries.py
    ├── prototypes.py
    └── batch_cmds.ev
```

## Configuration

From `server/conf/settings.py`:
- **Server name:** `mygame`
- **Web port:** 4001 (maps to internal port 4005)
- **Default MUD telnet port:** 4000 (Evennia default)

## DNS & Domain

- **`homagemud.com`** resolves to `158.69.199.228` — yes, the domain is pointed at this server
- Registered via WHOIS privacy — actual owner behind Contact Privacy Inc.

## Apache Reverse Proxy Configuration

Apache 2.4.58 is the front-facing web server, acting as a **reverse proxy** to Evennia. SSL is handled via Let's Encrypt.

**Config file:** `/etc/apache2/sites-enabled/evennia.conf`

```apache
# HTTPS — reverse proxies to Evennia
<VirtualHost *:443>
    ServerName homagemud.com
    ServerAlias www.homagemud.com
    SSLEngine On
    SSLCertificateFile /etc/letsencrypt/live/homagemud.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/homagemud.com/privkey.pem
    Include /etc/letsencrypt/options-ssl-apache.conf

    ProxyPreserveHost On

    # WebSocket proxy for Evennia webclient
    ProxyPass        /ws ws://127.0.0.1:4002/
    ProxyPassReverse /ws ws://127.0.0.1:4002/

    # HTTP proxy to Evennia web service
    ProxyPass        / http://127.0.0.1:4001/
    ProxyPassReverse / http://127.0.0.1:4001/

    ErrorLog ${APACHE_LOG_DIR}/evennia_error.log
    CustomLog ${APACHE_LOG_DIR}/evennia_access.log combined
</VirtualHost>

# HTTP — redirects everything to HTTPS
<VirtualHost *:80>
    ServerName homagemud.com
    ServerAlias www.homagemud.com
    Redirect / https://homagemud.com/
</VirtualHost>
```

**Traffic flow:**
```
User → https://homagemud.com → Apache (SSL termination) → Evennia localhost:4001
                                                        → WebSocket localhost:4002 (/ws)
```

The site was down because Evennia wasn't running — Apache had nothing to proxy to.

## Docker

- **Docker is NOT installed** on this server
- `mudowner` HAS full sudo access (`(ALL : ALL) ALL`) — sudo password is same as login
- Docker can be installed at any time — TODO for later
- Current setup runs Evennia directly via Python virtual environment (no containerization)

## Current Server Status (as of 2026-04-07)

- **MUD server:** RUNNING (started 2026-04-07) — Portal PID 823359, Server PID 823364
- **Website:** Live at https://homagemud.com
- **Last login before today:** November 20, 2025 (~5 months dormant)
- **System needs restart** (kernel update pending)
- **20 pending package updates**
- **No sudo access** for `mudowner` account
  - ...but the Docker section above states `mudowner` HAS full sudo (`(ALL : ALL) ALL`).
    These notes contradict each other; verify before relying on either.
- **Game appears to be default/stock Evennia** — no significant customization observed in the code
  - Stale as of 2026-07-18: the game now has RP scenes, a score sheet, and a fief land system.

## How to Start the MUD

```bash
ssh mudowner@homagemud.com
cd ~/muddev
source evenv/bin/activate
cd mygame
evennia migrate    # (first time only, sets up database)
evennia start      # starts the MUD server
```

Then connect via:
- **Telnet/MUD client:** `homagemud.com` port `4000`
- **Web client:** `http://158.69.199.228:4001/`

## Local Backup

Full copy of `muddev/` downloaded to: `/Users/andrewbrowne/muddev/`
