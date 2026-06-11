import socket
import threading
from datetime import datetime

# ─────────────────────────────────────────────
# BANNIÈRES FTP (comme un vrai serveur)
# ─────────────────────────────────────────────

# Message d'accueil envoyé dès la connexion
BANNER       = b"220 ProFTPD 1.3.5 Server (Debian) [::ffff:127.0.0.1]\r\n"

# Réponses FTP standard (codes officiels du protocole)
ASK_PASSWORD = b"331 Password required for {user}\r\n"
LOGIN_FAILED = b"530 Login incorrect.\r\n"
GOODBYE      = b"221 Goodbye.\r\n"
UNKNOWN_CMD  = b"500 Unknown command.\r\n"


# ─────────────────────────────────────────────
# GESTION D'UNE SESSION FTP
# ─────────────────────────────────────────────

def handle_ftp_connection(client_socket, client_ip, log_callback):
    """
    Gère une session FTP complète.

    Le protocole FTP fonctionne en mode texte ligne par ligne :
    - Client envoie une commande  ex: "USER root"
    - Serveur répond avec un code ex: "331 Password required"

    On simule ce dialogue pour capturer le nom d'utilisateur
    et le mot de passe avant de rejeter la connexion.
    """
    username = None  # on mémorise le USER entre les deux commandes

    try:
        # ── Étape 1 : on envoie la bannière d'accueil ──────────
        client_socket.sendall(BANNER)

        # ── Étape 2 : boucle de dialogue ───────────────────────
        while True:
            # Lit une ligne de commande (max 1024 octets)
            raw = client_socket.recv(1024)
            if not raw:
                break  # connexion fermée par le client

            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            # Sépare la commande de l'argument : "USER root" → ["USER", "root"]
            parts = line.split(" ", 1)
            cmd   = parts[0].upper()
            arg   = parts[1] if len(parts) > 1 else ""

            # ── Commande USER (nom d'utilisateur) ──────────────
            if cmd == "USER":
                username = arg
                response = ASK_PASSWORD.replace(b"{user}", username.encode())
                client_socket.sendall(response)

            # ── Commande PASS (mot de passe) → on logue et refuse
            elif cmd == "PASS":
                password = arg

                log_callback({
                    "type":      "ftp",
                    "ip":        client_ip,
                    "username":  username or "-",
                    "password":  password,
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                })

                client_socket.sendall(LOGIN_FAILED)
                # Après un échec, on reste connecté
                # (les vrais clients réessaient plusieurs fois)
                username = None  # reset pour la prochaine tentative

            # ── Commande QUIT (déconnexion propre) ─────────────
            elif cmd == "QUIT":
                client_socket.sendall(GOODBYE)
                break

            # ── Commande inconnue ───────────────────────────────
            else:
                client_socket.sendall(UNKNOWN_CMD)

    except Exception:
        pass
    finally:
        try:
            client_socket.close()
        except Exception:
            pass


# ─────────────────────────────────────────────
# DÉMARRAGE DU HONEYPOT FTP
# ─────────────────────────────────────────────

def start_ftp_honeypot(port, log_callback):
    """Lance le serveur honeypot FTP sur le port donné."""

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(100)

    print(f"[FTP]  Honeypot actif sur le port {port} ✓")
    print(f"[FTP]  Test local : ftp localhost {port}  (ou via FileZilla)\n")

    while True:
        client_socket, addr = server_socket.accept()
        t = threading.Thread(
            target=handle_ftp_connection,
            args=(client_socket, addr[0], log_callback),
            daemon=True,
        )
        t.start()