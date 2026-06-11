# ce fichier est le point d'entrée de TrapNet : 
# il charge la config, 
# initialise les logs, 
# démarre les services et le dashboard.

import threading
from config_loader   import load_config
from core.ssh_server  import start_ssh_honeypot
from core.http_server import start_http_honeypot
from core.ftp_server  import start_ftp_honeypot
from logger.logger    import setup_logger, log_event
from dashboard.dashboard import add_event, start_dashboard

# ── 1. Chargement de la config ──────────────────────────
config = load_config("config.yaml")

# ── 2. Initialisation des logs ──────────────────────────
setup_logger(path=config["logs"]["file"])

# ── 3. Callback commun (logs + dashboard) ───────────────
def on_event(event):
    log_event(event)
    add_event(event)

# ── 4. Dashboard ────────────────────────────────────────
live = None
if config["dashboard"]["enabled"]:
    live = start_dashboard(
        refresh_per_second=config["dashboard"]["refresh_rate"]
    )

# ── 5. Lancement des services selon la config ───────────
ssh_cfg  = config["services"]["ssh"]
http_cfg = config["services"]["http"]
ftp_cfg  = config["services"]["ftp"]

# SSH
if ssh_cfg["enabled"]:
    threading.Thread(
        target=start_ssh_honeypot,
        args=(ssh_cfg["port"], on_event),
        daemon=True,
    ).start()
else:
    print("[SSH]  Désactivé dans config.yaml")

# HTTP
if http_cfg["enabled"]:
    threading.Thread(
        target=start_http_honeypot,
        args=(http_cfg["port"], on_event),
        daemon=True,
    ).start()
else:
    print("[HTTP] Désactivé dans config.yaml")

# FTP
if ftp_cfg["enabled"]:
    threading.Thread(
        target=start_ftp_honeypot,
        args=(ftp_cfg["port"], on_event),
        daemon=True,
    ).start()
else:
    print("[FTP]  Désactivé dans config.yaml")

# ── 6. Maintien du programme ────────────────────────────
try:
    threading.Event().wait()
except KeyboardInterrupt:
    if live:
        live.stop()
    print(f"\n[TrapNet] Arrêté. Logs sauvegardés dans : {config['logs']['file']}")