# TrapNet — Honeypot Python expérimental

**TrapNet** est un honeypot expérimental écrit en Python. Il simule des services réseau (SSH, HTTP, FTP), collecte les tentatives de connexion et enregistre des logs pour analyse. Ce projet ma permis à apprendre la détection d’intrusions, l’analyse de trafic malveillant et l’automatisation en Python.

---

## Fonctionnalités
- **Simulation de services** : émulation basique de SSH, HTTP et FTP.  
- **Collecte de logs** : enregistrement des tentatives de connexion (timestamp, IP source, protocole, action).  
- **Configuration YAML** : paramètres centralisés et faciles à modifier.  
- **Dashboard terminal** : affichage en temps réel via Rich.  
- **Extensible** : architecture modulaire pour ajouter d’autres protocoles ou traitements.

---

## Architecture
- **Langage** : Python  
- **Librairies principales** : `paramiko`; `rich`; `pyyaml`  
- **Protocoles simulés** : SSH; HTTP; FTP  
- **Type** : Honeypot à basse interaction (simulation)

---

## Installation (développement local)
1. Cloner le dépôt  


## Perspectives et améliorations
Interface web pour visualiser incidents.
Support de plus de protocoles et interaction plus riche
Pipeline d’analyse (parsing, enrichissement IP, alerting).
déploiement.
