import threading
from datetime import datetime
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

# ─────────────────────────────────────────────
# STOCKAGE EN MÉMOIRE (partagé entre threads)
# ─────────────────────────────────────────────

# Verrou pour éviter les conflits entre threads
_lock = threading.Lock()

# Liste des événements capturés (max 50 affichés)
_events   = []
MAX_ROWS  = 50

# Compteurs globaux
_stats = {
    "ssh":   0,
    "http":  0,
    "ftp":   0,
    "total": 0,
    "ips":   set(),
}


def add_event(event):
    """
    Ajoute un événement au dashboard.
    Appelé depuis n'importe quel thread (SSH, HTTP ou FTP).
    """
    with _lock:
        _events.append(event)
        proto = event.get("type", "?")
        _stats["total"] += 1
        _stats[proto]   = _stats.get(proto, 0) + 1
        _stats["ips"].add(event.get("ip", ""))

        # On garde seulement les MAX_ROWS derniers événements
        if len(_events) > MAX_ROWS:
            _events.pop(0)


# ─────────────────────────────────────────────
# CONSTRUCTION DU DASHBOARD
# ─────────────────────────────────────────────

def make_table():
    """Construit le tableau des événements récents."""
    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
        show_lines=False,
        expand=True,
    )

    table.add_column("Proto",       width=8,  justify="center")
    table.add_column("IP Source",   width=18)
    table.add_column("Path / Port", width=14)
    table.add_column("Utilisateur", width=16)
    table.add_column("Mot de passe",width=20)
    table.add_column("Heure",       width=10, justify="right")

    with _lock:
        # Affiche les événements du plus récent au plus ancien
        for evt in reversed(_events):
            proto = evt.get("type", "?").upper()

            # Couleur et icône selon le protocole
            if proto == "SSH":
                proto_text = Text("⬤ SSH",  style="bold red")
                path_text  = Text("port 2222", style="dim")

            elif proto == "FTP":
                proto_text = Text("⬤ FTP",  style="bold green")
                path_text  = Text("port 2121", style="dim")
            else:
                proto_text = Text("⬤ HTTP", style="bold blue")
                path_text  = Text(evt.get("path", "-"), style="yellow")

            table.add_row(
                proto_text,
                Text(evt.get("ip", "-"),       style="white"),
                path_text,
                Text(evt.get("username", "-"), style="green"),
                Text(evt.get("password", "-"), style="red"),
                Text(evt.get("timestamp", "-")[-8:], style="dim"),  # heure seule HH:MM:SS
            )

    return table


def make_stats_panel():
    """Construit le bandeau de statistiques en haut."""
    with _lock:
        ssh_count   = _stats.get("ssh",   0)
        http_count  = _stats.get("http",  0)
        ftp_count   = _stats.get("ftp",   0)
        total       = _stats.get("total", 0)
        unique_ips  = len(_stats.get("ips", set()))

    now = datetime.now().strftime("%H:%M:%S")

    content = (
        f"[bold red]⬤ SSH[/bold red]  {ssh_count:>5} tentatives   "
        f"[bold blue]⬤ HTTP[/bold blue] {http_count:>5} tentatives   "
        f"[bold green]⬤ FTP[/bold green]  {ftp_count:>5} tentatives   "
        f"[bold yellow]⬤ Total[/bold yellow] {total:>5}   "
        f"[bold cyan]⬤ IPs uniques[/bold cyan] {unique_ips:>4}   "
        f"[dim]Mis à jour : {now}[/dim]"
    )

    return Panel(
        content,
        title="[bold white]🪤  TrapNet v0.3 — Live Dashboard[/bold white]",
        border_style="cyan",
        padding=(0, 1),
    )


def make_dashboard():
    """Assemble le dashboard complet (stats + tableau)."""
    layout = Layout()

    layout.split_column(
        Layout(make_stats_panel(), name="stats", size=3),
        Layout(make_table(),       name="table"),
    )

    return layout


# ─────────────────────────────────────────────
# LANCEMENT DU DASHBOARD
# ─────────────────────────────────────────────

def start_dashboard(refresh_per_second=2):
    """
    Lance le dashboard en live dans le terminal.
    Se rafraîchit automatiquement toutes les 0.5 secondes.
    Retourne le contexte Live pour qu'il reste actif.
    """
    console = Console()

    live = Live(
        make_dashboard(),
        console=console,
        refresh_per_second=refresh_per_second,
        screen=True,          # prend tout le terminal
    )

    def _updater():
        """Thread qui pousse les mises à jour au dashboard."""
        while True:
            live.update(make_dashboard())
            threading.Event().wait(0.5)  # rafraîchit toutes les 0.5s

    live.start()

    t = threading.Thread(target=_updater, daemon=True)
    t.start()

    return live  # le main.py garde cette référence pour ne pas quitter