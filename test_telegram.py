"""
=============================================================
SCRIPT DE TEST — CONNEXION TELEGRAM
=============================================================
Teste la connexion au Bot Telegram et l'envoi de messages
de test vers le canal/groupe configuré, en utilisant le
nouveau format de signaux.

Usage :
  python test_telegram.py
=============================================================
"""

import sys
import logging

from config import config
from telegram_bot import TelegramBot
from analysis import SignalResult, SignalType
from alert_engine import SignalFormatter

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)

logger = logging.getLogger("TestTelegram")


def main():
    """Test de la connexion et de l'envoi Telegram."""
    print("=" * 60)
    print("🧪 TEST DE CONNEXION TELEGRAM")
    print("=" * 60)

    # 1. Vérifier la configuration
    print("\n📋 Vérification de la configuration...")
    print(f"  TELEGRAM_TOKEN : {'✅ Défini' if config.TELEGRAM_TOKEN else '❌ Manquant'}")
    print(f"  TELEGRAM_CHAT_ID : {'✅ Défini' if config.TELEGRAM_CHAT_ID else '❌ Manquant'}")

    if not config.TELEGRAM_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("\n❌ ERREUR : Veuillez configurer TELEGRAM_TOKEN et TELEGRAM_CHAT_ID dans le fichier .env")
        print("   1. Créez un bot via @BotFather sur Telegram")
        print("   2. Récupérez le token du bot")
        print("   3. Ajoutez le bot à votre canal/groupe")
        print("   4. Récupérez le chat_id du canal/groupe")
        sys.exit(1)

    # 2. Créer l'instance du bot
    print("\n🤖 Création de l'instance du bot...")
    bot = TelegramBot()

    # 3. Tester la connexion
    print("\n📡 Test de connexion au Bot Telegram...")
    if not bot.test_connection():
        print("❌ Échec de connexion. Vérifiez votre TELEGRAM_TOKEN.")
        sys.exit(1)

    print("✅ Connexion réussie !")

    # 4. Envoyer un message de test simple
    print("\n📤 Envoi d'un message de test simple...")
    test_message = """
🧪 <b>TEST — Bot de Signaux Forex</b>

✅ Connexion réussie !
📡 Le bot est opérationnel.

📱 Plateforme cible : <b>Olymp Trade</b>
⏱ Timeframe : <b>M5</b>

<i>Test du système de notification.</i>
"""
    if bot.send_message(test_message.strip()):
        print("✅ Message de test simple envoyé !")
    else:
        print("❌ Échec de l'envoi du message simple.")
        sys.exit(1)

    # 5. Test d'un signal CALL formaté (nouveau template)
    print("\n📊 Test d'un signal CALL formaté (nouveau template)...")
    signal_call = SignalResult(
        pair="EURUSD=X",
        signal=SignalType.SIGNAL_ACHAT,
        direction="CALL",
        price=1.08520,
        ema50=1.08350,
        rsi=32.5,
        rsi_prev=28.3,
        bb_upper=1.08900,
        bb_middle=1.08500,
        bb_lower=1.08100,
        confidence="🟡 Moyenne",
        timestamp="2026-08-01 14:30:00",
        details="Test CALL",
    )
    msg_call = SignalFormatter.format_signal_message(signal_call)
    if bot.send_message(msg_call):
        print("✅ Signal CALL formaté envoyé !")
    else:
        print("❌ Échec de l'envoi du signal CALL.")

    # 6. Test d'un signal PUT formaté
    print("\n📊 Test d'un signal PUT formaté (nouveau template)...")
    signal_put = SignalResult(
        pair="GBPUSD=X",
        signal=SignalType.SIGNAL_VENTE,
        direction="PUT",
        price=1.27150,
        ema50=1.27350,
        rsi=67.8,
        rsi_prev=72.5,
        bb_upper=1.27500,
        bb_middle=1.27200,
        bb_lower=1.26900,
        confidence="🟢 Élevée",
        timestamp="2026-08-01 14:30:00",
        details="Test PUT",
    )
    msg_put = SignalFormatter.format_signal_message(signal_put)
    if bot.send_message(msg_put):
        print("✅ Signal PUT formaté envoyé !")
    else:
        print("❌ Échec de l'envoi du signal PUT.")

    # 7. Test du message de démarrage
    print("\n📊 Test du message de démarrage...")
    startup_msg = SignalFormatter.format_startup_message(config.FOREX_PAIRS)
    if bot.send_message(startup_msg):
        print("✅ Message de démarrage envoyé !")
    else:
        print("❌ Échec de l'envoi du message de démarrage.")

    print("\n" + "=" * 60)
    print("🎉 TOUS LES TESTS TELEGRAM ONT RÉUSSI !")
    print("=" * 60)
    print("\n💡 Vous pouvez maintenant lancer le bot avec : python main.py")


if __name__ == "__main__":
    main()
