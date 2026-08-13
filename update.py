"""
=============================================================
SCRIPT DE MISE À JOUR AUTOMATIQUE
=============================================================
Met à jour tous les fichiers modifiés du bot.
Exécutez : python update.py
=============================================================
"""

import os
import json

BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# CONTENU DES FICHIERS À METTRE À JOUR
# ============================================================

# --- .env ---
ENV_CONTENT = """# ============================================================
# Configuration du Bot de Signaux Forex
# ============================================================

# --- Telegram ---
TELEGRAM_TOKEN=VOTRE_TOKEN_BOT_TELEGRAM_ICI
TELEGRAM_CHAT_ID=VOTRE_CHAT_ID_ICI

# --- Source de donnees Forex ---
DATA_SOURCE=yfinance

# --- OANDA (optionnel, si DATA_SOURCE=oanda) ---
OANDA_API_KEY=VOTRE_CLE_OANDA_ICI
OANDA_ACCOUNT_ID=VOTRE_COMPTE_OANDA_ICI
OANDA_BASE_URL=https://api-fxpractice.oanda.com

# --- Paires Forex surveillees (separees par des virgules) ---
# 10 paires pour plus d'opportunites
FOREX_PAIRS=EURUSD=X,GBPUSD=X,AUDJPY=X,USDJPY=X,GBPJPY=X,EURGBP=X,USDCHF=X,AUDUSD=X,NZDUSD=X,USDCAD=X

# --- Parametres de la strategie ---
TIMEFRAME=5m
EMA_PERIOD=20
RSI_PERIOD=14
BB_PERIOD=20
BB_STD=2

# --- Parametres d'execution ---
SCAN_INTERVAL=300

# --- Fuseau horaire ---
# 1 = GMT+1 (Porto Novo, Cotonou, Lome, etc.)
TIMEZONE_OFFSET=1

# --- Moteur d'alerte ---
CANDLE_OFFSET_SECONDS=2

# --- Gestion des erreurs ---
MAX_CONSECUTIVE_ERRORS=10
BASE_RETRY_DELAY=30
MAX_RETRY_DELAY=300
NOTIFY_AFTER_ERRORS=3
"""


def update_env():
    """Met à jour le fichier .env en préservant le TOKEN et CHAT_ID."""
    env_path = os.path.join(BASE, ".env")

    # Lire le fichier .env actuel pour récupérer les valeurs sensibles
    existing = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    existing[key.strip()] = value.strip()

    # Écrire le nouveau .env
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(ENV_CONTENT)

    # Restaurer les valeurs existantes (TOKEN, CHAT_ID)
    if existing.get("TELEGRAM_TOKEN") and existing["TELEGRAM_TOKEN"] != "VOTRE_TOKEN_BOT_TELEGRAM_ICI":
        _replace_in_file(env_path, "VOTRE_TOKEN_BOT_TELEGRAM_ICI", existing["TELEGRAM_TOKEN"])

    if existing.get("TELEGRAM_CHAT_ID") and existing["TELEGRAM_CHAT_ID"] != "VOTRE_CHAT_ID_ICI":
        _replace_in_file(env_path, "VOTRE_CHAT_ID_ICI", existing["TELEGRAM_CHAT_ID"])

    print("  ✅ .env mis à jour (TOKEN et CHAT_ID préservés)")


def _replace_in_file(filepath, old, new):
    """Remplace une chaîne dans un fichier."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace(old, new)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def update_from_json():
    """Met à jour les fichiers Python depuis update_data.json."""
    json_path = os.path.join(BASE, "update_data.json")

    if not os.path.exists(json_path):
        print("  ⚠️ update_data.json non trouvé. Fichiers Python non mis à jour.")
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        files = json.load(f)

    updated = 0
    for filename, content in files.items():
        filepath = os.path.join(BASE, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✅ {filename} mis à jour ({len(content)} caractères)")
            updated += 1
        except Exception as e:
            print(f"  ❌ {filename} : {e}")

    return updated


def main():
    print("=" * 60)
    print("🔄 MISE À JOUR DES FICHIERS DU BOT")
    print("=" * 60)

    # 1. Mettre à jour .env (préserve TOKEN et CHAT_ID)
    print("\n📋 Mise à jour du fichier .env...")
    try:
        update_env()
    except Exception as e:
        print(f"  ❌ Erreur .env : {e}")

    # 2. Mettre à jour les fichiers Python
    print("\n📋 Mise à jour des fichiers Python...")
    updated = update_from_json()

    print("\n" + "=" * 60)
    print(f"✅ MISE À JOUR TERMINÉE ({updated} fichiers Python + .env)")
    print("=" * 60)
    print("\n💡 Prochaines étapes :")
    print("   1. Vérifie le fichier .env : cat .env")
    print("   2. Teste le bot : python test_alert_engine.py")
    print("   3. Lance le bot : python main.py")


if __name__ == "__main__":
    main()
