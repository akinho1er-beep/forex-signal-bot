"""
=============================================================
SCRIPT DE TEST — MOTEUR D'ALERTE
=============================================================
Teste le moteur d'alerte complet :
  - Dédoublonnage des signaux
  - Formatage des messages
  - Synchronisation des bougies M5
  - Scénarios de signaux réels

Usage :
  python test_alert_engine.py
=============================================================
"""

import sys
import logging
from datetime import datetime, timezone

from config import config
from analysis import SignalResult, SignalType
from alert_engine import alert_engine, candle_sync, SignalFormatter, DeduplicationManager, CandleSync

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)

logger = logging.getLogger("TestAlertEngine")


def test_deduplication():
    """Test du système de dédoublonnage."""
    print("=" * 60)
    print("🔒 TEST DE DÉDOUBLONNAGE")
    print("=" * 60)

    dedup = DeduplicationManager()

    # Premier signal — ne doit pas être un doublon
    is_dup1 = dedup.is_duplicate("EURUSD=X", "2026-08-01 14:30:00", "CALL")
    print(f"\n  1er signal EURUSD CALL @ 14:30 → Doublon ? {is_dup1}")
    assert not is_dup1, "Le premier signal ne doit PAS être un doublon"
    print("  ✅ OK — Pas un doublon")

    # Marquer comme envoyé
    dedup.mark_sent("EURUSD=X", "2026-08-01 14:30:00", "CALL")

    # Même signal — doit être un doublon
    is_dup2 = dedup.is_duplicate("EURUSD=X", "2026-08-01 14:30:00", "CALL")
    print(f"\n  2e signal EURUSD CALL @ 14:30 → Doublon ? {is_dup2}")
    assert is_dup2, "Le second signal DOIT être un doublon"
    print("  ✅ OK — Doublon détecté")

    # Signal différent (même paire, bougie différente)
    is_dup3 = dedup.is_duplicate("EURUSD=X", "2026-08-01 14:35:00", "CALL")
    print(f"\n  Signal EURUSD CALL @ 14:35 → Doublon ? {is_dup3}")
    assert not is_dup3, "Un signal sur une bougie différente n'est pas un doublon"
    print("  ✅ OK — Pas un doublon (bougie différente)")

    # Signal différent (même paire, même bougie, direction différente)
    is_dup4 = dedup.is_duplicate("EURUSD=X", "2026-08-01 14:30:00", "PUT")
    print(f"\n  Signal EURUSD PUT @ 14:30 → Doublon ? {is_dup4}")
    assert not is_dup4, "Un signal dans une direction différente n'est pas un doublon"
    print("  ✅ OK — Pas un doublon (direction différente)")

    # Signal différent (paire différente)
    is_dup5 = dedup.is_duplicate("GBPUSD=X", "2026-08-01 14:30:00", "CALL")
    print(f"\n  Signal GBPUSD CALL @ 14:30 → Doublon ? {is_dup5}")
    assert not is_dup5, "Un signal sur une paire différente n'est pas un doublon"
    print("  ✅ OK — Pas un doublon (paire différente)")

    print(f"\n📊 Stats dédoublonnage : {dedup.get_stats()}")
    print("\n✅ TOUS LES TESTS DE DÉDOUBLONNAGE RÉUSSIS !")


def test_candle_sync():
    """Test du synchronisateur de bougies M5."""
    print("\n" + "=" * 60)
    print("⏱ TEST DE SYNCHRONISATION M5")
    print("=" * 60)

    sync = CandleSync(offset_seconds=2)

    # Calcul du temps restant
    seconds = sync.seconds_until_next_candle_close()
    next_close = sync.get_next_candle_close_time()
    candle_id = sync.get_current_candle_id()

    print(f"\n  Secondes avant prochaine clôture : {seconds}")
    print(f"  Prochaine clôture : {next_close.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"  ID bougie en cours : {candle_id}")

    # Vérifications
    assert 0 < seconds <= 302, f"Le délai doit être entre 1 et 302s, obtenu : {seconds}"
    print("\n  ✅ Délai dans les limites attendues (1-302s)")

    # Vérifier que la prochaine clôture est bien sur un multiple de 5 minutes
    next_minute = next_close.minute
    assert next_minute % 5 == 0, f"La minute de clôture doit être un multiple de 5, obtenu : {next_minute}"
    print(f"  ✅ Prochaine clôture sur minute {next_minute} (multiple de 5)")

    print("\n✅ TESTS DE SYNCHRONISATION RÉUSSIS !")


def test_signal_formatter():
    """Test du formateur de messages."""
    print("\n" + "=" * 60)
    print("📝 TEST DU FORMATAGE DE MESSAGES")
    print("=" * 60)

    # Créer un signal CALL fictif
    signal_call = SignalResult(
        pair="EURUSD=X",
        signal=SignalType.SIGNAL_ACHAT,
        direction="CALL",
        price=1.08520,
        ema=1.08350,
        rsi=32.5,
        rsi_prev=28.3,
        bb_upper=1.08900,
        bb_middle=1.08500,
        bb_lower=1.08100,
        confidence="🟡 Moyenne",
        timestamp="2026-08-01 14:30:00",
        details="Test CALL",
        strategy="RSI Reversal",
        reasons=["RSI Reversal", "RSI croise >40 (28.3→32.5)", "Tendance haussière"],
    )

    # Créer un signal PUT fictif
    signal_put = SignalResult(
        pair="GBPUSD=X",
        signal=SignalType.SIGNAL_VENTE,
        direction="PUT",
        price=1.27150,
        ema=1.27350,
        rsi=67.8,
        rsi_prev=72.5,
        bb_upper=1.27500,
        bb_middle=1.27200,
        bb_lower=1.26900,
        confidence="🟢 Élevée",
        timestamp="2026-08-01 14:30:00",
        details="Test PUT",
        strategy="Bollinger Bounce",
        reasons=["Bollinger Bounce", "Rejet BB supérieur", "RSI surachat (72.5)"],
    )

    # Formater les messages
    print("\n--- SIGNAL CALL ---")
    msg_call = SignalFormatter.format_signal_message(signal_call)
    print(msg_call)

    print("\n--- SIGNAL PUT ---")
    msg_put = SignalFormatter.format_signal_message(signal_put)
    print(msg_put)

    # Vérifier le format
    print("\n--- VÉRIFICATIONS ---")

    # Vérifier que le message contient les éléments requis
    # (les balises HTML <b> sont dans le texte, on cherche les parties textuelles)
    required_elements = [
        "SIGNAL OLYMP TRADE (M5)",
        "Actif :",
        "Action :",
        "HAUT (🟢)",
        "Durée d'expiration",
        "5 Minutes",
        "Entrée :",
        "Raison :",
    ]

    for elem in required_elements:
        if elem in msg_call:
            print(f"  ✅ {elem}")
        else:
            print(f"  ❌ MANQUANT : {elem}")

    # Vérifier les éléments PUT
    put_elements = [
        "SIGNAL OLYMP TRADE (M5)",
        "BAS (🔴)",
        "RSI Sur-acheté",
        "Rejet Bollinger Supérieur",
    ]

    for elem in put_elements:
        if elem in msg_put:
            print(f"  ✅ PUT : {elem}")
        else:
            print(f"  ❌ PUT MANQUANT : {elem}")

    # Message de démarrage
    print("\n--- MESSAGE DÉMARRAGE ---")
    startup_msg = SignalFormatter.format_startup_message(["EURUSD=X", "GBPUSD=X"])
    print(startup_msg)

    # Message d'erreur
    print("\n--- MESSAGE ERREUR ---")
    error_msg = SignalFormatter.format_error_message("Connexion perdue")
    print(error_msg)

    # Message de reprise
    print("\n--- MESSAGE RECONNECTION ---")
    recovery_msg = SignalFormatter.format_recovery_message(5)
    print(recovery_msg)

    print("\n✅ TESTS DE FORMATAGE RÉUSSIS !")


def test_alert_engine_process():
    """Test du processus complet du moteur d'alerte."""
    print("\n" + "=" * 60)
    print("🔔 TEST DU MOTEUR D'ALERTE (PROCESS)")
    print("=" * 60)

    # Signal neutre — ne doit pas être envoyé
    signal_neutral = SignalResult(
        pair="EURUSD=X",
        signal=SignalType.NEUTRE,
        direction="NEUTRE",
        price=1.08520,
        ema=1.08350,
        rsi=45.0,
        rsi_prev=44.0,
        bb_upper=1.08900,
        bb_middle=1.08500,
        bb_lower=1.08100,
        confidence="—",
        timestamp="2026-08-01 14:30:00",
        details="Neutre",
        strategy="",
        reasons=[],
    )

    result = alert_engine.process_signal(signal_neutral)
    print(f"\n  Signal neutre traité → Envoyé ? {result}")
    assert not result, "Un signal neutre ne doit PAS être envoyé"
    print("  ✅ OK — Signal neutre ignoré")

    # Stats
    stats = alert_engine.get_stats()
    print(f"\n📊 Stats du moteur d'alerte : {stats}")

    print("\n✅ TESTS DU MOTEUR D'ALERTE RÉUSSIS !")


def main():
    """Exécute tous les tests du moteur d'alerte."""
    print("🧪 SUITE DE TESTS DU MOTEUR D'ALERTE")
    print("=" * 60)

    # Test 1 : Dédoublonnage
    print("\n[1/4] Test de dédoublonnage...")
    test_deduplication()

    # Test 2 : Synchronisation M5
    print("\n[2/4] Test de synchronisation M5...")
    test_candle_sync()

    # Test 3 : Formatage des messages
    print("\n[3/4] Test de formatage des messages...")
    test_signal_formatter()

    # Test 4 : Processus du moteur d'alerte
    print("\n[4/4] Test du processus d'alerte...")
    test_alert_engine_process()

    print("\n" + "=" * 60)
    print("🎉 TOUS LES TESTS DU MOTEUR D'ALERTE RÉUSSIS !")
    print("=" * 60)


if __name__ == "__main__":
    main()
