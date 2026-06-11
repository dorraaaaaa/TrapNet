import json
import os
from datetime import datetime

# Chemin par défaut (peut être remplacé par la config)
LOG_FILE = "logs/trapnet.json"


def setup_logger(path=None):
    """Crée le dossier et le fichier de logs s'ils n'existent pas."""
    global LOG_FILE
    if path:
        LOG_FILE = path

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
    print(f"[LOGGER] Logs → {LOG_FILE} ✓")


def log_event(event):
    """Enregistre un événement dans le fichier JSON."""
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(event)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def get_all_logs():
    """Retourne tous les logs enregistrés."""
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []