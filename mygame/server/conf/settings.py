r"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "mygame"
WEBSERVER_PORTS = [(4001, 4005)]

# Public self-registration and multi-character accounts for RP chat.
NEW_ACCOUNT_REGISTRATION_ENABLED = True
MULTISESSION_MODE = 2
AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False
MAX_NR_CHARACTERS = 5

# Reverse-proxy / CSRF config for Apache -> Evennia on homagemud.com.
SERVER_HOSTNAME = "homagemud.com"
ALLOWED_HOSTS = ["homagemud.com", "www.homagemud.com", "localhost", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = [
    "https://homagemud.com",
    "https://www.homagemud.com",
]
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Webclient must use the Apache-proxied wss:// URL (the raw ws://host:4002/ is
# blocked by browsers when loading the page over HTTPS).
WEBSOCKET_CLIENT_URL = "wss://homagemud.com/ws"
######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
