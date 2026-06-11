import socket
import threading
from datetime import datetime
from urllib.parse import parse_qs, urlparse

# ─────────────────────────────────────────────
# FAUSSES PAGES HTML
# ─────────────────────────────────────────────

# Page de login qui ressemble à un vrai panneau d'admin
FAKE_LOGIN_PAGE = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html>
<head><title>Admin Panel</title></head>
<body style="background:#1a1a2e; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; font-family:Arial">
  <div style="background:#16213e; padding:40px; border-radius:8px; width:300px; box-shadow:0 0 20px rgba(0,0,0,0.5)">
    <h2 style="color:#e94560; text-align:center; margin-bottom:30px"> Admin Panel</h2>
    <form method="POST">
      <input name="username" placeholder="Username" style="width:100%; padding:10px; margin-bottom:15px; background:#0f3460; border:1px solid #e94560; color:white; border-radius:4px; box-sizing:border-box"><br>
      <input name="password" type="password" placeholder="Password" style="width:100%; padding:10px; margin-bottom:20px; background:#0f3460; border:1px solid #e94560; color:white; border-radius:4px; box-sizing:border-box"><br>
      <button type="submit" style="width:100%; padding:10px; background:#e94560; color:white; border:none; border-radius:4px; cursor:pointer; font-size:16px">Login</button>
    </form>
  </div>
</body>
</html>
"""

# Réponse après tentative de login (refusé toujours)
FAKE_LOGIN_FAILED = """HTTP/1.1 401 Unauthorized\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html>
<head><title>Admin Panel</title></head>
<body style="background:#1a1a2e; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; font-family:Arial">
  <div style="background:#16213e; padding:40px; border-radius:8px; width:300px; box-shadow:0 0 20px rgba(0,0,0,0.5)">
    <h2 style="color:#e94560; text-align:center; margin-bottom:30px"> Admin Panel</h2>
    <p style="color:#e94560; text-align:center"> Invalid credentials</p>
    <form method="POST">
      <input name="username" placeholder="Username" style="width:100%; padding:10px; margin-bottom:15px; background:#0f3460; border:1px solid #e94560; color:white; border-radius:4px; box-sizing:border-box"><br>
      <input name="password" type="password" placeholder="Password" style="width:100%; padding:10px; margin-bottom:20px; background:#0f3460; border:1px solid #e94560; color:white; border-radius:4px; box-sizing:border-box"><br>
      <button type="submit" style="width:100%; padding:10px; background:#e94560; color:white; border:none; border-radius:4px; cursor:pointer; font-size:16px">Login</button>
    </form>
  </div>
</body>
</html>
"""

# Page 404 pour les chemins inconnus (mais on logue quand même)
FAKE_404 = """HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n
<html><body><h1>404 Not Found</h1></body></html>
"""

# Chemins que les bots vérifient systématiquement
LOGIN_PATHS = [
    "/admin", "/admin/", "/login", "/wp-admin", "/wp-login.php",
    "/administrator", "/panel", "/dashboard", "/console",
    "/phpmyadmin", "/pma", "/cpanel", "/manager",
]


# ─────────────────────────────────────────────
# PARSING D'UNE REQUÊTE HTTP BRUTE
# ─────────────────────────────────────────────

def parse_http_request(raw):
    """
    Décompose une requête HTTP brute en :
    - méthode (GET, POST...)
    - chemin (/admin, /login...)
    - headers (User-Agent, Host...)
    - body (username=admin&password=123 pour les POST)
    """
    try:
        # Sépare les headers du body
        if b"\r\n\r\n" in raw:
            headers_part, body = raw.split(b"\r\n\r\n", 1)
        else:
            headers_part, body = raw, b""

        lines = headers_part.decode("utf-8", errors="replace").split("\r\n")

        # Première ligne : "POST /admin HTTP/1.1"
        method, path, *_ = lines[0].split(" ")

        # Les autres lignes sont les headers
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()

        return method, path, headers, body.decode("utf-8", errors="replace")

    except Exception:
        return "UNKNOWN", "/", {}, ""


# ─────────────────────────────────────────────
# GESTION D'UNE CONNEXION HTTP
# ─────────────────────────────────────────────

def handle_http_connection(client_socket, client_ip, log_callback):
    """Gère une connexion HTTP entrante."""
    try:
        # Lit la requête (max 4096 octets)
        raw = client_socket.recv(4096)
        if not raw:
            return

        method, path, headers, body = parse_http_request(raw)
        timestamp = datetime.now().isoformat(timespec="seconds")
        user_agent = headers.get("user-agent", "-")

        # --- Cas 1 : POST sur une page de login → tentative de connexion ---
        if method == "POST" and path in LOGIN_PATHS:
            # Parse les credentials du body : "username=admin&password=123"
            params = parse_qs(body)
            username = params.get("username", ["-"])[0]
            password = params.get("password", ["-"])[0]

            log_callback({
                "type":       "http",
                "ip":         client_ip,
                "method":     method,
                "path":       path,
                "username":   username,
                "password":   password,
                "user_agent": user_agent,
                "timestamp":  timestamp,
            })
            client_socket.sendall(FAKE_LOGIN_FAILED.encode())

        # --- Cas 2 : GET sur une page de login → affiche le formulaire ---
        elif method == "GET" and path in LOGIN_PATHS:
            log_callback({
                "type":       "http",
                "ip":         client_ip,
                "method":     method,
                "path":       path,
                "user_agent": user_agent,
                "timestamp":  timestamp,
            })
            client_socket.sendall(FAKE_LOGIN_PAGE.encode())

        # --- Cas 3 : Autre chemin → 404 mais on logue quand même ---
        else:
            log_callback({
                "type":       "http",
                "ip":         client_ip,
                "method":     method,
                "path":       path,
                "user_agent": user_agent,
                "timestamp":  timestamp,
            })
            client_socket.sendall(FAKE_404.encode())

    except Exception:
        pass
    finally:
        try:
            client_socket.close()
        except Exception:
            pass


# ─────────────────────────────────────────────
# DÉMARRAGE DU HONEYPOT HTTP
# ─────────────────────────────────────────────

def start_http_honeypot(port, log_callback):
    """Lance le serveur honeypot HTTP sur le port donné."""

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(100)

    print(f"[HTTP] Honeypot actif sur le port {port} ✓")
    print(f"[HTTP] Test local : ouvre http://localhost:{port}/admin dans ton navigateur\n")

    while True:
        client_socket, addr = server_socket.accept()
        t = threading.Thread(
            target=handle_http_connection,
            args=(client_socket, addr[0], log_callback),
            daemon=True,
        )
        t.start()