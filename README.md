# TrapNet
honeypot ?
Un leurre. on fait croire à un attaquant qu'il y a un vrai serveur SSH, HTTP, FTP sur une machine. Il essaie de se connecter, de deviner des mots de passe — toi tu enregistres tout sans jamais lui donner accès à quoi que ce soit de réel.


Attaquant                        TrapNet
   │                                │
   │──── tente SSH port 22 ────────►│  ← faux serveur SSH
   │◄─── "Password incorrect" ──────│  (simulé, pas réel)
   │                                │
   │                          LOG créé :
   │                          IP: 185.x.x.x
   │                          Login tenté: root/admin123
   │                          Timestamp: 2026-05-30 14:32
