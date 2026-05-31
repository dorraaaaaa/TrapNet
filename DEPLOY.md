# Guide de déploiement minimal — TrapNet

## Pré-requis
- VPS ou instance cloud (Ubuntu 22.04 recommandé)
- Accès SSH root ou utilisateur sudo
- Docker et docker-compose installés

## Étapes rapides
1. Cloner le dépôt sur le VPS
   git clone https://github.com/ton-compte/TrapNet.git
   cd TrapNet

2. Construire et lancer (docker-compose)
   docker-compose up -d --build

3. Configurer le firewall (exemple ufw)
   sudo ufw allow 2222/tcp
   sudo ufw allow 8080/tcp
   sudo ufw enable

4. Vérifier les logs
   docker logs -f trapnet

## Checklist sécurité avant exposition
- Isoler le conteneur (réseau bridge dédié ou VM séparée)
- Bloquer tout trafic sortant non nécessaire
- Mettre en place monitoring (fail2ban, alerting)
- Anonymiser ou ne pas stocker PII
- Vérifier les conditions d’utilisation du fournisseur cloud

## Nettoyage
- Arrêter et supprimer :
  docker-compose down
  docker image rm trapnet:latest
