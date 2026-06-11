#ce fichier contient la fonction load_config() qui lit le fichier config.yaml
#et retourne un dict de configuration utilisable par le reste du programme.
import yaml
import sys

# Config par défaut si le fichier est absent ou incomplet
DEFAULT_CONFIG = {
    "services": {
        "ssh":  {"enabled": True,  "port": 2222},
        "http": {"enabled": True,  "port": 8080},
        "ftp":  {"enabled": True,  "port": 2121},
    },
    "dashboard": {
        "enabled":      True,
        "refresh_rate": 2,
    },
    "logs": {
        "file":       "logs/trapnet.json",
        "max_events": 50,
    },
}


def load_config(path="config.yaml"):
    """
    Charge la config depuis le fichier YAML.
    Si le fichier est absent → utilise les valeurs par défaut.
    Si une clé manque → complète avec les valeurs par défaut.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f)

        # Fusionne la config utilisateur avec les défauts
        # (les valeurs utilisateur écrasent les défauts)
        config = _deep_merge(DEFAULT_CONFIG, user_config or {})
        print(f"[CONFIG] Fichier chargé : {path} ✓")

    except FileNotFoundError:
        config = DEFAULT_CONFIG.copy()
        print(f"[CONFIG] {path} introuvable → valeurs par défaut utilisées")

    except yaml.YAMLError as e:
        print(f"[CONFIG] Erreur YAML dans {path} : {e}")
        print("[CONFIG] Abandon — corrige le fichier et relance.")
        sys.exit(1)

    # Affiche un résumé de ce qui est activé
    _print_summary(config)
    return config


def _deep_merge(base, override):
    """
    Fusionne deux dicts en profondeur.
    Les valeurs de `override` écrasent celles de `base`.
    """
    result = base.copy()
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def _print_summary(config):
    """Affiche un résumé lisible de la configuration."""
    print("[CONFIG] Services activés :")

    ssh  = config["services"]["ssh"]
    http = config["services"]["http"]
    ftp  = config["services"]["ftp"]
    dash = config["dashboard"]

    ssh_status  = f"port {ssh['port']}"  if ssh["enabled"]  else "désactivé"
    http_status = f"port {http['port']}" if http["enabled"] else "désactivé"
    ftp_status  = f"port {ftp['port']}"  if ftp["enabled"]  else "désactivé"
    dash_status = f"refresh {dash['refresh_rate']}x/s" if dash["enabled"] else "désactivé"

    print(f"         SSH       → {ssh_status}")
    print(f"         HTTP      → {http_status}")
    print(f"         FTP       → {ftp_status}")
    print(f"         Dashboard → {dash_status}")
    print(f"         Logs      → {config['logs']['file']}")