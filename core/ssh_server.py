import socket
import threading
from datetime import datetime
import paramiko

# ─────────────────────────────────────────────
# CLASSE : Comportement du faux serveur SSH
# ─────────────────────────────────────────────

class FakeSSHServer(paramiko.ServerInterface):
    """
    Simule un serveur SSH.
    - Accepte les connexions entrantes
    - Demande un mot de passe
    - Rejette TOUJOURS l'accès (on est un leurre, pas un vrai serveur)
    - Logue chaque tentative
    """

    def __init__(self, client_ip, log_callback):
        self.client_ip   = client_ip
        self.log_callback = log_callback  # fonction appelée à chaque tentative

    def check_auth_password(self, username, password):
        """
        Appelé automatiquement quand un attaquant essaie un mot de passe.
        On logue et on refuse.
        """
        self.log_callback({
            "type":      "ssh",
            "ip":        self.client_ip,
            "username":  username,
            "password":  password,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })
        # On refuse toujours — c'est un honeypot !
        return paramiko.AUTH_FAILED

    def check_auth_none(self, username):
        """Refuse les connexions sans mot de passe."""
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        """On annonce qu'on accepte seulement les mots de passe."""
        return "password"

    def check_channel_request(self, kind, chanid):
        """Refuse l'ouverture de canal (shell, etc.) — on ne va jamais jusque-là."""
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED


# ─────────────────────────────────────────────
# GESTION D'UNE CONNEXION INDIVIDUELLE
# ─────────────────────────────────────────────

def handle_connection(client_socket, client_ip, host_key, log_callback):
    """
    Gère une connexion SSH entrante dans son propre thread.
    Plusieurs attaquants peuvent se connecter en même temps.
    """
    try:
        # On crée une "session SSH" sur la connexion TCP brute
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(host_key)

        # On lance le faux serveur SSH sur cette session
        fake_server = FakeSSHServer(client_ip, log_callback)
        transport.start_server(server=fake_server)

        # On attend 20 secondes max qu'ils essaient quelque chose
        transport.accept(20)

    except Exception:
        # Connexions cassées, scans rapides, etc. — on ignore silencieusement
        pass
    finally:
        try:
            client_socket.close()
        except Exception:
            pass


# ─────────────────────────────────────────────
# DÉMARRAGE DU HONEYPOT SSH
# ─────────────────────────────────────────────

def start_ssh_honeypot(port, log_callback):
    """
    Lance le serveur honeypot SSH sur le port donné.
    Tourne en boucle infinie, accepte toutes les connexions.
    """

    # Génère une clé RSA aléatoire (comme un vrai serveur SSH)
    print("[SSH] Génération de la clé hôte RSA...")
    host_key = paramiko.RSAKey.generate(2048)

    # Création du socket serveur TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", port))  # écoute sur toutes les interfaces
    server_socket.listen(100)              # jusqu'à 100 connexions en attente

    print(f"[SSH] Honeypot actif sur le port {port} ✓")
    print(f"[SSH] Test local : ssh -p {port} root@localhost  (puis entre n'importe quel mdp)\n")

    # Boucle principale : on attend et accepte les connexions
    while True:
        client_socket, addr = server_socket.accept()
        client_ip = addr[0]

        # Chaque connexion est gérée dans un thread séparé
        t = threading.Thread(
            target=handle_connection,
            args=(client_socket, client_ip, host_key, log_callback),
            daemon=True,  # s'arrête quand le programme principal s'arrête
        )
        t.start()