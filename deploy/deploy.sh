#!/bin/bash
# ============================================================
# Script de déploiement du Bot de Signaux Forex
# Sur un serveur VPS Ubuntu (systemd)
# ============================================================

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}   BOT DE SIGNAUX FOREX — DÉPLOIEMENT VPS (Ubuntu)${NC}"
echo -e "${GREEN}============================================================${NC}"

# --- Configuration ---
BOT_DIR="/opt/forex_signal_bot"
BOT_USER="forexbot"
SERVICE_NAME="forex-bot"

# --- Vérifications préalables ---
echo -e "\n${YELLOW}[1/7] Vérifications préalables...${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Ce script doit être exécuté en root (sudo).${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}📦 Installation de Python 3...${NC}"
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
fi

echo -e "${GREEN}✅ Python $(python3 --version) détecté${NC}"

# --- Créer l'utilisateur ---
echo -e "\n${YELLOW}[2/7] Création de l'utilisateur système...${NC}"

if id "$BOT_USER" &>/dev/null; then
    echo -e "${GREEN}✅ Utilisateur $BOT_USER existe déjà${NC}"
else
    useradd -r -s /bin/false "$BOT_USER"
    echo -e "${GREEN}✅ Utilisateur $BOT_USER créé${NC}"
fi

# --- Copier les fichiers ---
echo -e "\n${YELLOW}[3/7] Installation des fichiers...${NC}"

# Créer le répertoire
mkdir -p "$BOT_DIR/logs"

# Copier le projet (si on est dans le répertoire source)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_DIR/main.py" ]; then
    cp -r "$PROJECT_DIR"/*.py "$PROJECT_DIR/requirements.txt" "$BOT_DIR/"
    if [ -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env" "$BOT_DIR/"
    fi
    echo -e "${GREEN}✅ Fichiers copiés vers $BOT_DIR${NC}"
else
    echo -e "${RED}❌ Fichiers du projet non trouvés dans $PROJECT_DIR${NC}"
    echo -e "   Assurez-vous que le script est dans le répertoire deploy/ du projet"
    exit 1
fi

# --- Créer le venv et installer les dépendances ---
echo -e "\n${YELLOW}[4/7] Installation des dépendances Python...${NC}"

python3 -m venv "$BOT_DIR/venv"
source "$BOT_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$BOT_DIR/requirements.txt"
deactivate

echo -e "${GREEN}✅ Dépendances installées${NC}"

# --- Vérifier le fichier .env ---
echo -e "\n${YELLOW}[5/7] Vérification de la configuration...${NC}"

if [ ! -f "$BOT_DIR/.env" ]; then
    echo -e "${RED}❌ Fichier .env non trouvé !${NC}"
    echo -e "   Créez le fichier .env dans $BOT_DIR avec vos variables"
    echo -e "   Voir .env.example pour le template"
    exit 1
fi

# Vérifier les variables critiques
if grep -q "VOTRE_TOKEN" "$BOT_DIR/.env" || grep -q "VOTRE_CHAT_ID" "$BOT_DIR/.env"; then
    echo -e "${RED}❌ Le fichier .env contient encore des valeurs par défaut !${NC}"
    echo -e "   Veuillez configurer TELEGRAM_TOKEN et TELEGRAM_CHAT_ID"
    exit 1
fi

echo -e "${GREEN}✅ Configuration validée${NC}"

# --- Installer le service systemd ---
echo -e "\n${YELLOW}[6/7] Installation du service systemd...${NC}"

# Adapter le chemin dans le service
sed -i "s|/opt/forex_signal_bot|$BOT_DIR|g" "$PROJECT_DIR/deploy/forex-bot.service"
sed -i "s|User=forexbot|User=$BOT_USER|g" "$PROJECT_DIR/deploy/forex-bot.service"
sed -i "s|Group=forexbot|Group=$BOT_USER|g" "$PROJECT_DIR/deploy/forex-bot.service"

cp "$PROJECT_DIR/deploy/forex-bot.service" "/etc/systemd/system/$SERVICE_NAME.service"

# Permissions
chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR"
chmod 600 "$BOT_DIR/.env"

# Activer et démarrer le service
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo -e "${GREEN}✅ Service systemd installé${NC}"

# --- Démarrer le bot ---
echo -e "\n${YELLOW}[7/7] Démarrage du bot...${NC}"

systemctl start "$SERVICE_NAME"

# Vérifier le statut
sleep 3
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Bot démarré avec succès !${NC}"
else
    echo -e "${RED}❌ Le bot n'a pas pu démarrer. Vérifiez les logs :${NC}"
    journalctl -u "$SERVICE_NAME" -n 20
    exit 1
fi

# --- Résumé ---
echo -e "\n${GREEN}============================================================${NC}"
echo -e "${GREEN}   DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !${NC}"
echo -e "${GREEN}============================================================${NC}"
echo -e ""
echo -e "📋 Commandes utiles :"
echo -e "   Statut :  systemctl status $SERVICE_NAME"
echo -e "   Logs :    journalctl -u $SERVICE_NAME -f"
echo -e "   Stop :    systemctl stop $SERVICE_NAME"
echo -e "   Restart : systemctl restart $SERVICE_NAME"
echo -e "   Logs app : tail -f $BOT_DIR/forex_bot.log"
echo -e ""
echo -e "📁 Répertoire : $BOT_DIR"
echo -e "👤 Utilisateur : $BOT_USER"
echo -e "🔧 Service : $SERVICE_NAME.service"
