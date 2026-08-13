# 📘 GUIDE DÉBUTANT — Bot de Signaux Forex
## De zéro jusqu'au bot qui tourne 24h/24

---

# 🗺️ PLAN GLOBAL

On va faire **8 étapes**, dans cet ordre :

```
Étape 1 → Créer le Bot Telegram
Étape 2 → Créer le canal Telegram
Étape 3 → Récupérer le Chat ID
Étape 4 → Installer Python
Étape 5 → Installer le bot
Étape 6 → Configurer le bot
Étape 7 → Tester le bot
Étape 8 → Lancer le bot 24h/24
```

⚠️ **Ne saute aucune étape.** Chaque étape dépend de la précédente.

---

# ÉTAPE 1 : CRÉER LE BOT TELEGRAM

Le bot, c'est le "robot" qui va envoyer les messages sur Telegram.
On le crée une seule fois, ensuite il existe pour toujours.

### Ce que tu dois faire :

1. **Ouvre Telegram** sur ton téléphone ou ton ordinateur

2. **Cherche @BotFather** dans la barre de recherche Telegram
   - C'est le bot officiel de Telegram qui crée les autres bots
   - Il a un ✅ bleu à côté de son nom

3. **Clique sur DÉMARRER** (ou envoie `/start`)

4. **Envoie ce message** : `/newbot`

5. **Il te demande un nom** → Tape ce que tu veux, par exemple :
   ```
   Forex Signal Bot
   ```
   (C'est le nom affiché, pas besoin d'être unique)

6. **Il te demande un username** → Ça doit finir par "bot", par exemple :
   ```
   forex_signal_m5_bot
   ```
   Si ce nom est déjà pris, essaie un autre :
   ```
   mon_forex_signal_bot
   ```
   ou
   ```
   fx_signal_olymp_bot
   ```

7. **BotFather te répond** avec un message qui ressemble à ça :
   ```
   Done! Congratulations on your new bot...
   Use this token to access the HTTP API:
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Keep your token secure...
   ```

8. **COPIE LE TOKEN** → C'est la longue ligne qui ressemble à :
   ```
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### 📝 Où le garder ?

Ouvre le Bloc-notes (ou n'importe quel éditeur de texte) et colle le token.
Tu en auras besoin à l'étape 6.

```
Mon token : 7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

⚠️ **NE PARTAGE JAMAIS CE TOKEN** avec personne. C'est comme un mot de passe.

---

# ÉTAPE 2 : CRÉER LE CANAL TELEGRAM

Le canal, c'est l'endroit où les signaux seront envoyés.
Tu peux aussi utiliser un groupe, mais un canal c'est mieux.

### Ce que tu dois faire :

1. **Ouvre Telegram**

2. **Clique sur l'icône crayon ✏️** (ou le bouton "+") en bas à droite

3. **Choisis "Nouvelle chaîne"** (ou "New Channel")

4. **Donne un nom** au canal, par exemple :
   ```
   📊 Forex Signals M5
   ```

5. **Mets une description** (optionnel) :
   ```
   Signaux Forex automatiques - Timeframe M5
   ```

6. **Choisis "Canal public"** (c'est plus simple pour récupérer le chat_id)
   - Donne-lui un lien, par exemple : `forex_signals_m5`

   Si tu préfères un canal privé, c'est possible aussi (voir étape 3)

7. **Le canal est créé !** ✅

### Maintenant, ajoute le bot au canal :

1. **Ouvre le canal** que tu viens de créer

2. **Clique sur le nom du canal** en haut

3. **Clique sur "Administrateurs"** (ou "Add Admin")

4. **Cherche le username** de ton bot (celui de l'étape 1, par exemple `@forex_signal_m5_bot`)

5. **Sélectionne le bot** et **confirme** en lui donnant les droits d'administrateur

⚠️ **Important :** Le bot DOIT être administrateur du canal, sinon il ne peut pas envoyer de messages.

---

# ÉTAPE 3 : RÉCUPÉRER LE CHAT ID

Le Chat ID, c'est comme "l'adresse" de ton canal. Le bot a besoin de cette adresse pour savoir où envoyer les messages.

### Si ton canal est PUBLIC :

C'est très simple. Le chat_id, c'est le lien de ton canal.

Par exemple, si ton lien est `https://t.me/forex_signals_m5`, alors ton chat_id est :
```
@forex_signals_m5
```

✅ Tu peux passer à l'étape 4.

### Si ton canal est PRIVÉ :

C'est un peu plus technique. Voici comment faire :

1. **Envoie un message** dans ton canal (n'importe quoi, par exemple "test")

2. **Ouvre ton navigateur** (Chrome, Firefox, etc.)

3. **Tape cette URL** dans la barre d'adresse, en remplaçant `TON_TOKEN` par ton vrai token :
   ```
   https://api.telegram.org/botTON_TOKEN/getUpdates
   ```
   
   Par exemple :
   ```
   https://api.telegram.org/bot7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/getUpdates
   ```

4. **Tu vas voir un texte** qui ressemble à ça :
   ```json
   {"ok":true,"result":[{"message":{"chat":{"id":-1001234567890}}}] }
   ```

5. **Cherche le nombre** après `"id":` → C'est ton chat_id
   ```
   -1001234567890
   ```
   (Il commence toujours par -100 pour les canaux privés)

### 📝 Où le garder ?

Dans ton Bloc-notes, ajoute :
```
Mon token : 7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Mon chat_id : @forex_signals_m5
```

---

# ÉTAPE 4 : INSTALLER PYTHON

Python, c'est le langage de programmation du bot. Il faut l'installer sur ton ordinateur.

### Sur Windows :

1. **Va sur** : https://www.python.org/downloads/

2. **Clique sur "Download Python 3.11"** (ou la version la plus récente)

3. **Ouvre le fichier** téléchargé

4. ⚠️ **TRÈS IMPORTANT** : Coche la case **"Add Python to PATH"** en bas de la fenêtre d'installation !

5. **Clique sur "Install Now"**

6. **Attends** que l'installation se termine

7. **Vérifie** que ça marche :
   - Ouvre l'Invite de commandes (tape `cmd` dans la barre de recherche Windows)
   - Tape : `python --version`
   - Tu devrais voir : `Python 3.11.x`

### Sur Mac :

1. **Ouvre le Terminal** (dans Applications > Utilitaires)

2. **Tape** : `python3 --version`
   - Si Python est déjà installé, tu verras la version
   - Sinon, le Mac te proposera de l'installer automatiquement

3. **Sinon**, va sur https://www.python.org/downloads/ et télécharge Python pour Mac

### Sur Ubuntu/Linux :

Ouvre le terminal et tape :
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

---

# ÉTAPE 5 : INSTALLER LE BOT

Maintenant, on va installer le bot proprement dit.

### 5.1 — Récupérer les fichiers du bot

Si tu as les fichiers sur ton ordinateur, ouvre le dossier `forex_signal_bot`.

Sinon, ouvre l'Invite de commandes (Terminal) et tape :

```bash
cd Bureau
```
(Pour aller sur le Bureau, ou choisis le dossier que tu veux)

### 5.2 — Créer un environnement virtuel

L'environnement virtuel, c'est comme une "boîte" isolée où le bot va tourner sans perturber le reste de ton ordinateur.

**Ouvre l'Invite de commandes (Terminal) et tape** :

```bash
cd forex_signal_bot
python -m venv venv
```

### 5.3 — Activer l'environnement virtuel

**Sur Windows** :
```bash
venv\Scripts\activate
```

**Sur Mac / Linux** :
```bash
source venv/bin/activate
```

✅ Tu devrais voir `(venv)` apparaître au début de ta ligne de commande.

### 5.4 — Installer les dépendances

Les dépendances, ce sont les "bibliothèques" dont le bot a besoin pour fonctionner.

**Tape** :
```bash
pip install -r requirements.txt
```

⏳ Attends que tout s'installe (ça peut prendre 1-2 minutes).

Tu devrais voir beaucoup de lignes défiler, puis à la fin :
```
Successfully installed ...
```

✅ **Le bot est installé !**

---

# ÉTAPE 6 : CONFIGURER LE BOT

C'est ici que tu donnes au bot tes informations Telegram.

### 6.1 — Ouvrir le fichier de configuration

Dans le dossier `forex_signal_bot`, tu vas trouver un fichier appelé `.env`.

**Ouvre-le avec le Bloc-notes** (ou un éditeur de texte).

Tu vas voir ça :
```
TELEGRAM_TOKEN=VOTRE_TOKEN_BOT_TELEGRAM_ICI
TELEGRAM_CHAT_ID=VOTRE_CHAT_ID_ICI
```

### 6.2 — Remplir les informations

**Remplace** les valeurs par tes vraies informations :

```
TELEGRAM_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=@forex_signals_m5
```

⚠️ **Attention** :
- Pas d'espaces autour du signe `=`
- Pas de guillemets
- Le token est celui de l'étape 1
- Le chat_id est celui de l'étape 3

### 6.3 — Les autres paramètres

Tu peux laisser les autres paramètres comme ils sont. Ils sont déjà configurés pour le Forex M5.

Mais si tu veux, tu peux modifier :

```
# Les paires surveillées (séparées par des virgules)
FOREX_PAIRS=EURUSD=X,GBPUSD=X,AUDJPY=X,USDJPY=X,GBPJPY=X,EURGBP=X

# Les paramètres de la stratégie (ne change pas si tu n'es pas sûr)
EMA_PERIOD=50
RSI_PERIOD=14
BB_PERIOD=20
BB_STD=2
```

### 6.4 — Sauvegarder

**Enregistre le fichier** (Ctrl+S) et ferme-le.

---

# ÉTAPE 7 : TESTER LE BOT

Avant de lancer le bot pour de vrai, on va vérifier que tout fonctionne.

### 7.1 — Tester la connexion Telegram

**Dans l'Invite de commandes (Terminal)**, avec `(venv)` activé, tape :

```bash
python test_telegram.py
```

**Ce que tu devrais voir** :
```
✅ Bot Telegram connecté : @forex_signal_m5_bot
✅ Message de test envoyé !
✅ Signal CALL formaté envoyé !
✅ Signal PUT formaté envoyé !
🎉 TOUS LES TESTS TELEGRAM ONT RÉUSSI !
```

📱 **Vérifie ton canal Telegram** : Tu devrais voir 3 messages :
1. Un message de test simple
2. Un signal CALL (achat) 🟢
3. Un signal PUT (vente) 🔴

### ❌ Si ça ne marche pas :

| Problème | Solution |
|---|---|
| "❌ Échec de connexion Telegram" | Vérifie que le TOKEN est correct dans le fichier .env |
| "❌ Échec de l'envoi du message" | Vérifie que le CHAT_ID est correct et que le bot est admin du canal |
| "ModuleNotFoundError" | Vérifie que l'environnement virtuel est activé (tu dois voir `(venv)`) |

### 7.2 — Tester le moteur d'analyse

**Tape** :
```bash
python test_analysis.py
```

Tu devrais voir les indicateurs calculés avec des ✅ partout.

### 7.3 — Tester le moteur d'alerte

**Tape** :
```bash
python test_alert_engine.py
```

Tu devrais voir :
```
✅ TOUS LES TESTS DE DÉDOUBLONNAGE RÉUSSIS !
✅ TESTS DE SYNCHRONISATION RÉUSSIS !
✅ TESTS DE FORMATAGE RÉUSSIS !
🎉 TOUS LES TESTS DU MOTEUR D'ALERTE RÉUSSIS !
```

---

# ÉTAPE 8 : LANCER LE BOT 24h/24

Le bot fonctionne en continu. Il faut le laisser tourner tout le temps.

### Option A : Sur ton ordinateur (simple mais pas 24/7)

**Tape** :
```bash
python main.py
```

Le bot démarre et commence à scanner les marchés.

📱 **Vérifie ton canal Telegram** : Tu devrais voir un message de démarrage.

**Pour arrêter** : Appuie sur `Ctrl + C`

⚠️ **Problème** : Si tu éteins ton ordinateur, le bot s'arrête.
Ce n'est pas vraiment 24/7.

---

### Option B : Sur un VPS (recommandé pour 24/7) 🔥

Un VPS, c'est un ordinateur qui tourne en permanence sur internet, que tu loues pour quelques euros par mois.

#### B.1 — Choisir un VPS

Tu peux prendre un VPS à pas cher :

| Fournisseur | Prix | Lien |
|---|---|---|
| Contabo | ~5€/mois | contabo.com |
| Hetzner | ~4€/mois | hetzner.com |
| DigitalOcean | ~6€/mois | digitalocean.com |
| Oracle Cloud | **Gratuit** | cloud.oracle.com |

Le VPS doit être **Ubuntu 22.04 ou 24.04**.

#### B.2 — Se connecter au VPS

Après avoir créé ton VPS, tu reçois :
- Une **adresse IP** (ex: `192.168.1.100`)
- Un **nom d'utilisateur** (souvent `root`)
- Un **mot de passe**

**Sur ton ordinateur**, ouvre un Terminal et tape :

```bash
ssh root@192.168.1.100
```

(Remplace par ta vraie adresse IP)

Tape ton mot de passe quand on te le demande.

✅ Tu es maintenant connecté à ton VPS !

#### B.3 — Installer le bot sur le VPS

**Tape ces commandes une par une** :

```bash
# Mettre à jour le système
apt update && apt upgrade -y

# Installer Python
apt install python3 python3-pip python3-venv git -y

# Créer le dossier du bot
mkdir -p /opt/forex_signal_bot
cd /opt/forex_signal_bot
```

**Maintenant, transfère les fichiers du bot** :

Soit avec `git clone` (si le projet est sur GitHub), soit avec `scp` :

```bash
# Depuis ton ordinateur, envoie les fichiers :
scp -r /chemin/vers/forex_signal_bot/* root@192.168.1.100:/opt/forex_signal_bot/
```

**Puis sur le VPS** :

```bash
cd /opt/forex_signal_bot

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

#### B.4 — Configurer le fichier .env sur le VPS

```bash
nano .env
```

Ça ouvre un éditeur de texte. Remplis les mêmes informations qu'à l'étape 6 :

```
TELEGRAM_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=@forex_signals_m5
```

**Pour sauvegarder** : `Ctrl + X`, puis `Y`, puis `Entrée`

#### B.5 — Tester sur le VPS

```bash
python test_telegram.py
```

Si tu vois les ✅, tout est bon !

#### B.6 — Installer le bot comme service (pour qu'il tourne toujours)

Le service, c'est ce qui fait que le bot redémarre tout seul si le VPS redémarre.

**Tape** :

```bash
# Copier le fichier de service
cp deploy/forex-bot.service /etc/systemd/system/

# Activer le service
systemctl daemon-reload
systemctl enable forex-bot

# Démarrer le bot
systemctl start forex-bot
```

#### B.7 — Vérifier que le bot tourne

```bash
systemctl status forex-bot
```

Tu devrais voir :
```
Active: active (running)
```

✅ **Le bot tourne 24h/24 !**

📱 Vérifie ton canal Telegram : tu devrais voir le message de démarrage.

#### B.8 — Commandes utiles pour le VPS

```bash
# Voir les logs en temps réel
journalctl -u forex-bot -f

# Voir les logs de l'application
tail -f /opt/forex_signal_bot/forex_bot.log

# Redémarrer le bot
systemctl restart forex-bot

# Arrêter le bot
systemctl stop forex-bot

# Vérifier le statut
systemctl status forex-bot
```

---

### Option C : Sur Render (Cloud gratuit) ☁️

Pas besoin de VPS, c'est hébergé dans le cloud.

#### C.1 — Créer un compte

1. Va sur **https://render.com**
2. Crée un compte gratuit
3. Connecte ton compte GitHub

#### C.2 — Préparer le code sur GitHub

1. Crée un compte sur **https://github.com** si tu n'en as pas
2. Crée un nouveau dépôt (repository) appelé `forex-signal-bot`
3. Upload tous les fichiers du bot dans ce dépôt

#### C.3 — Déployer sur Render

1. Dans Render, clique **"New"** → **"Background Worker"**
2. Connecte ton dépôt GitHub `forex-signal-bot`
3. Configure :
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `python main.py`
4. Ajoute les **variables d'environnement** :
   - `TELEGRAM_TOKEN` = ton token
   - `TELEGRAM_CHAT_ID` = ton chat_id
   - `DATA_SOURCE` = yfinance
   - `FOREX_PAIRS` = EURUSD=X,GBPUSD=X,AUDJPY=X
5. Clique **"Create Background Worker"**

⏳ Render va installer et lancer le bot (environ 2-3 minutes).

✅ **Le bot tourne dans le cloud !**

⚠️ **Limites du plan gratuit Render** :
- 750 heures/mois (suffisant pour un bot qui tourne en continu)
- Le bot s'endort après 15 min d'inactivité (mais le nôtre scanne en continu, donc pas de problème)

---

# 🎯 RÉSUMÉ — Ce que fait le bot en pratique

```
Chaque 5 minutes, automatiquement :

1. 📥 Le bot télécharge les prix du Forex
   (EUR/USD, GBP/USD, AUD/JPY, etc.)

2. 📊 Il calcule les indicateurs techniques
   (EMA 50, RSI 14, Bollinger Bands)

3. 🔍 Il vérifie les conditions de signal :

   SIGNAL ACHAT (🟢) si :
   ✅ Prix au-dessus de l'EMA 50
   ✅ RSI sort de la zone de survente (< 30 → > 30)
   ✅ Rejet de la bande de Bollinger inférieure

   SIGNAL VENTE (🔴) si :
   ✅ Prix en dessous de l'EMA 50
   ✅ RSI sort de la zone de surachat (> 70 → < 70)
   ✅ Rejet de la bande de Bollinger supérieure

4. 📤 Si un signal est détecté → Envoi sur Telegram
   Si pas de signal → Attente de la prochaine bougie

5. 🔄 Le bot ne dort jamais (24/7)
```

---

# ❓ QUESTIONS FRÉQUENTES

### "Le bot n'envoie pas de signal, c'est normal ?"

**Oui, c'est normal !** Les 3 conditions sont très strictes. Le bot peut rester des heures sans envoyer de signal. C'est fait exprès pour ne recevoir que les signaux de haute qualité.

### "Combien de signaux par jour ?"

En moyenne : **2 à 5 signaux par jour** sur toutes les paires. Parfois plus, parfois moins, selon le marché.

### "Je peux changer les paires ?"

Oui ! Dans le fichier `.env`, modifie la ligne :
```
FOREX_PAIRS=EURUSD=X,GBPUSD=X,USDJPY=X
```
Les noms doivent être au format yfinance : `EURUSD=X`, `GBPUSD=X`, etc.

### "Le bot s'est arrêté, que faire ?"

Sur le VPS :
```bash
systemctl restart forex-bot
```

Ou vérifie les logs :
```bash
journalctl -u forex-bot -n 50
```

### "Comment voir les signaux envoyés ?"

Ouvre ton canal Telegram. Tous les signaux sont là.

### "C'est gratuit ?"

- Le bot lui-même : **gratuit**
- Telegram : **gratuit**
- Les données de marché (yfinance) : **gratuit**
- Le VPS (optionnel) : **4-6€/mois** (ou gratuit avec Oracle Cloud / Render)

### "Est-ce que les signaux sont sûrs à 100% ?"

**Non.** Aucun signal de trading n'est sûr à 100%. Le bot identifie des opportunités probables basées sur l'analyse technique, mais le marché peut toujours faire le contraire. **Ne risque jamais de l'argent que tu ne peux pas te permettre de perdre.**

---

# 📋 CHECKLIST DE DÉMARRAGE

Avant de lancer le bot, vérifie que tout est fait :

- [ ] J'ai créé un bot Telegram via @BotFather
- [ ] J'ai copié le TOKEN du bot
- [ ] J'ai créé un canal Telegram
- [ ] J'ai ajouté le bot comme administrateur du canal
- [ ] J'ai récupéré le CHAT_ID du canal
- [ ] J'ai installé Python sur mon ordinateur
- [ ] J'ai installé les dépendances (`pip install -r requirements.txt`)
- [ ] J'ai configuré le fichier `.env` avec mon TOKEN et mon CHAT_ID
- [ ] Le test Telegram fonctionne (`python test_telegram.py`)
- [ ] Le test d'analyse fonctionne (`python test_analysis.py`)
- [ ] Le test d'alerte fonctionne (`python test_alert_engine.py`)
- [ ] J'ai un VPS ou un service cloud pour le 24/7 (optionnel)

**Tout est coché ? Bravo ! 🎉 Tu es prêt à lancer le bot.**

```bash
python main.py
```

---

*Bon trading ! 📈 N'oublie pas : la discipline est plus importante que n'importe quel signal.*
