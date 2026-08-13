# 🤖 Bot de Signaux Forex — Documentation Complète

## 📋 Présentation

Bot d'analyse technique en Python qui surveille les marchés Forex en temps réel, identifie des opportunités de trading selon une stratégie définie (EMA 50 + RSI 14 + Bollinger Bands), et envoie des signaux d'achat/vente instantanés sur Telegram.

- **Paires surveillées** : EUR/USD, GBP/USD, AUD/JPY, USD/JPY, GBP/JPY, EUR/GBP
- **Timeframe** : M5 (5 minutes)
- **Plateforme cible** : Olymp Trade (exécution manuelle par l'utilisateur)
- **Synchronisation** : Scan automatique à chaque clôture de bougie M5

---

## 🏗 Architecture du projet

```
forex_signal_bot/
├── .env                      # Variables d'environnement (token, chat_id, config)
├── .env.example              # Template du fichier .env
├── requirements.txt          # Dépendances Python
├── README.md                 # Documentation complète
├── Dockerfile                # Image Docker
├── docker-compose.yml        # Orchestration Docker Compose
│
├── config.py                 # Configuration centrale (env vars)
├── telegram_bot.py           # Module Telegram (envoi, retry, rate limiting)
├── market_data.py            # Récupération OHLCV M5 (yfinance / OANDA)
├── analysis.py               # Moteur d'analyse technique (EMA, RSI, BB)
├── alert_engine.py           # Moteur d'alerte (dédoublonnage, formatage, sync M5)
├── main.py                   # Point d'entrée principal (boucle synchronisée)
├── utils.py                  # Fonctions utilitaires
│
├── test_telegram.py          # Test de connexion Telegram
├── test_analysis.py          # Test du moteur d'analyse
├── deploy/
│   ├── test_alert_engine.py  # Test du moteur d'alerte
│   ├── deploy.sh             # Script de déploiement VPS Ubuntu
│   ├── forex-bot.service     # Service systemd
│   ├── ecosystem.config.js   # Configuration PM2
│   └── render.yaml           # Blueprint Render (Cloud)
└── logs/                     # Répertoire de logs
```

---

## 🚀 Installation

### 1. Prérequis

- Python 3.9+
- pip
- Connexion internet stable

### 2. Installer le projet

```bash
# Cloner ou copier le projet
cd forex_signal_bot

# Créer un environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Configurer le Bot Telegram

#### 3a. Créer le Bot via BotFather

1. Ouvrez Telegram et cherchez **@BotFather**
2. Envoyez `/newbot`
3. Choisissez un nom (ex: `Forex Signal Bot`)
4. Choisissez un username (ex: `forex_signal_m5_bot`)
5. **Copiez le Token API** fourni (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### 3b. Créer le canal/groupe de destination

1. Créez un **canal** ou **groupe** Telegram
2. Ajoutez le bot comme **administrateur** du canal/groupe
3. Récupérez le **chat_id** :
   - Pour un canal public : `@nom_du_canal`
   - Pour un canal/groupe privé :
     - Envoyez un message dans le canal
     - Accédez à : `https://api.telegram.org/bot<TOKEN>/getUpdates`
     - Cherchez le `chat_id` dans la réponse JSON

### 4. Configurer le fichier `.env`

```bash
cp .env.example .env
nano .env
```

Renseignez les variables :

```env
TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=@votre_canal_ou_-100123456789
DATA_SOURCE=yfinance
FOREX_PAIRS=EURUSD=X,GBPUSD=X,AUDJPY=X,USDJPY=X,GBPJPY=X,EURGBP=X
```

### 5. Tester le bot

```bash
# Test de connexion Telegram
python test_telegram.py

# Test du moteur d'analyse
python test_analysis.py

# Test du moteur d'alerte
python deploy/test_alert_engine.py
```

### 6. Lancer le bot

```bash
# Mode développement (foreground)
python main.py

# Mode production (background)
nohup python main.py > /dev/null 2>&1 &
```

---

## 📊 Stratégie de Trading

### Indicateurs utilisés

| Indicateur | Paramètres | Rôle |
|---|---|---|
| EMA 50 | Période 50 | Identification de la tendance |
| RSI 14 | Période 14 | Détection de survente/surachat |
| Bollinger Bands | Période 20, Std 2 | Identification des zones de rejet |

### Signal d'achat (HAUT / CALL) 🟢

3 conditions doivent être **simultanément** remplies :

1. **Tendance haussière** : Prix de clôture > EMA 50
2. **Rebond RSI** : RSI 14 était < 30 (survente) puis repasse au-dessus de 30
3. **Rejet BB inférieure** : La bougie touche/casse la bande de Bollinger inférieure puis rejette (Close au-dessus)

### Signal de vente (BAS / PUT) 🔴

3 conditions doivent être **simultanément** remplies :

1. **Tendance baissière** : Prix de clôture < EMA 50
2. **Retournement RSI** : RSI 14 était > 70 (surachat) puis repasse en dessous de 70
3. **Rejet BB supérieure** : La bougie touche/casse la bande de Bollinger supérieure puis rejette (Close en dessous)

### Niveaux de confiance

| Score | Confiance | Description |
|---|---|---|
| 4-5 | 🟢 Élevée | Conditions très fortes |
| 2-3 | 🟡 Moyenne | Conditions satisfaisantes |
| 0-1 | 🟠 Faible | Conditions minimales |

---

## 📱 Format des signaux Telegram

```
🚨 SIGNAL OLYMP TRADE (M5) 🟢

📊 Actif : EUR/USD

📈 Action : HAUT (🟢)

⏱️ Durée d'expiration : 5 Minutes

🎯 Entrée : À l'ouverture immédiate de la bougie suivante

💡 Raison : Tendance haussière EMA 50 + RSI Sur-vendu (28.3) → Rebond (32.5) + Rejet Bollinger Inférieur

━━━━━━━━━━━━━━━━━━━━━━━━
📋 Détails techniques
━━━━━━━━━━━━━━━━━━━━━━━━

💰 Prix de clôture : 1.08520
📈 EMA 50 : 1.08350
📉 RSI 14 : 28.3 → 32.5

🔵 Bollinger Sup : 1.08900
⚪ Bollinger Moy : 1.08500
🔴 Bollinger Inf : 1.08100

🎯 Confiance : 🟡 Moyenne
🕐 Heure du signal : 2026-08-01 14:30:00 UTC

⚠️ Signal généré automatiquement — Tradez de manière responsable.
```

---

## ⚙️ Configuration avancée

### Source de données

Par défaut, le bot utilise **yfinance** (gratuit, sans clé API). Vous pouvez aussi utiliser **OANDA** :

```env
DATA_SOURCE=oanda
OANDA_API_KEY=votre_cle
OANDA_ACCOUNT_ID=votre_compte
OANDA_BASE_URL=https://api-fxpractice.oanda.com
```

### Paires Forex

Modifiez la liste dans `.env` :

```env
FOREX_PAIRS=EURUSD=X,GBPUSD=X,USDJPY=X,AUDUSD=X
```

Formats yfinance : `EURUSD=X`, `GBPUSD=X`, `USDJPY=X`, etc.

### Paramètres de la stratégie

```env
EMA_PERIOD=50          # Période de l'EMA
RSI_PERIOD=14          # Période du RSI
BB_PERIOD=20           # Période des Bollinger Bands
BB_STD=2               # Écart-type des Bollinger Bands
```

### Paramètres d'alerte

```env
CANDLE_OFFSET_SECONDS=2    # Secondes d'attente après clôture M5
MAX_CONSECUTIVE_ERRORS=10  # Erreurs max avant arrêt automatique
BASE_RETRY_DELAY=30        # Délai de retry (secondes)
MAX_RETRY_DELAY=300        # Délai max de retry (secondes)
NOTIFY_AFTER_ERRORS=3      # Notifier Telegram après N erreurs
```

---

## 🔧 Moteur d'alerte (Mission 4)

### Synchronisation M5

Le bot se synchronise automatiquement sur les clôtures de bougies M5 :

- Les bougies M5 se clôturent aux minutes :00, :05, :10, :15, etc.
- Le bot calcule le temps exact restant avant la prochaine clôture
- Un offset de 2 secondes est ajouté après la clôture pour laisser le temps au broker de publier la bougie
- Le scan est déclenché à la seconde près

### Dédoublonnage

Chaque signal est identifié par un hash unique composé de :
- La paire (ex: `EURUSD=X`)
- L'horodatage de la bougie clôturée
- La direction (CALL ou PUT)

Un même signal pour une même bougie ne peut être envoyé qu'**une seule fois**.

### Format du message

Le message Telegram suit le template exact requis :

```
🚨 SIGNAL OLYMP TRADE (M5)
📊 Actif : [Ex: EUR/USD]
📈 Action : [HAUT (🟢) / BAS (🔴)]
⏱️ Durée d'expiration : 5 Minutes
🎯 Entrée : À l'ouverture immédiate de la bougie suivante
💡 Raison : [Ex: RSI Sur-vendu + Rebond Bollinger + Tendance EMA 50]
```

---

## 🖥 Déploiement 24/7 (Mission 5)

### Option 1 : VPS Ubuntu (systemd) — Recommandé

```bash
# Cloner le projet sur le VPS
git clone <repo> /opt/forex_signal_bot
cd /opt/forex_signal_bot

# Configurer le .env
cp .env.example .env
nano .env

# Lancer le script de déploiement
chmod +x deploy/deploy.sh
sudo ./deploy/deploy.sh
```

**Commandes de gestion :**

```bash
# Vérifier le statut
systemctl status forex-bot

# Voir les logs en temps réel
journalctl -u forex-bot -f

# Redémarrer
systemctl restart forex-bot

# Arrêter
systemctl stop forex-bot

# Voir les logs de l'application
tail -f /opt/forex_signal_bot/forex_bot.log
```

### Option 2 : PM2 (Node.js Process Manager)

```bash
# Installer PM2
npm install -g pm2

# Démarrer le bot
pm2 start deploy/ecosystem.config.js

# Gestion
pm2 status
pm2 logs forex-signal-bot
pm2 restart forex-signal-bot
pm2 stop forex-signal-bot

# Démarrage automatique au boot
pm2 startup
pm2 save
```

### Option 3 : Docker

```bash
# Construire et lancer
docker-compose up -d

# Voir les logs
docker-compose logs -f forex-bot

# Redémarrer
docker-compose restart forex-bot

# Arrêter
docker-compose down
```

### Option 4 : Render (Cloud gratuit)

1. Créez un compte sur [render.com](https://render.com)
2. Créez un nouveau **Background Worker**
3. Connectez votre repo Git
4. Configurez les variables d'environnement (identiques au `.env`)
5. Déployez

Ou utilisez le Blueprint `render.yaml` :

1. Poussez le projet sur GitHub
2. Dans Render : **New** → **Blueprint** → Sélectionnez le repo
3. Les services seront créés automatiquement

### Option 5 : Railway

1. Créez un compte sur [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub**
3. Configurez les variables d'environnement
4. Railway détecte automatiquement le `Dockerfile`

---

## 🛡 Gestion des erreurs

Le bot inclut un système robuste de gestion des erreurs :

| Situation | Comportement |
|---|---|
| Perte de connexion internet | Retry automatique avec backoff exponentiel (30s → 60s → 120s → 300s) |
| API Telegram indisponible | Retry 3 fois avec délai croissant, puis notification au retour |
| API yfinance indisponible | Retry 3 fois, puis skip du scan |
| Rate limiting Telegram (429) | Respect du délai `Retry-After` de l'API |
| Trop d'erreurs consécutives | Arrêt automatique après 10 erreurs, notification Telegram |
| Reconnexion après erreur | Notification Telegram de reprise avec durée d'indisponibilité |

### Logs

Le bot génère deux types de logs :

1. **Console** : `stdout` (visible en temps réel)
2. **Fichier** : `forex_bot.log` (rotation automatique)

```bash
# Voir les 50 dernières lignes
tail -50 forex_bot.log

# Suivre les logs en temps réel
tail -f forex_bot.log

# Chercher les erreurs
grep "❌" forex_bot.log
```

---

## 🔍 Maintenance

### Mise à jour du bot

```bash
cd /opt/forex_signal_bot
git pull
pip install -r requirements.txt
sudo systemctl restart forex-bot
```

### Monitoring

```bash
# Statut du service
systemctl status forex-bot

# Utilisation des ressources
ps aux | grep main.py

# Espace disque des logs
du -sh forex_bot.log
```

### Nettoyage des logs

```bash
# Rotation manuelle
mv forex_bot.log forex_bot.log.$(date +%Y%m%d)
sudo systemctl restart forex-bot
```

---

## ⚠️ Avertissement

Ce bot est un outil d'analyse technique. Les signaux générés ne constituent pas des conseils financiers. Le trading Forex comporte des risques importants de perte de capital. Tradez de manière responsable et n'investissez que ce que vous pouvez vous permettre de perdre.

---

## 📜 Licence

Projet privé — Usage personnel uniquement.
