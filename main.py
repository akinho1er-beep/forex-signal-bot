"""
=============================================================
BOT DE SIGNAUX FOREX — POINT D'ENTRÉE PRINCIPAL
=============================================================
Boucle principale synchronisée sur les clôtures M5 :
  1. Attend la clôture exacte de la bougie M5
  2. Récupère les données de marché fraîches
  3. Analyse les conditions techniques
  4. Envoie les alertes via le moteur d'alertes
  5. Gère les erreurs avec retry automatique

Usage :
  python main.py
=============================================================
"""

import sys
import time
import logging
import traceback
from datetime import datetime, timezone

from config import config
from telegram_bot import telegram_bot
from market_data import market_fetcher
from analysis import analyzer, SignalType
from alert_engine import alert_engine, candle_sync

# ==========================================================
# CONFIGURATION DU LOGGING
# ==========================================================

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("forex_bot.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger("ForexBot")


# ==========================================================
# GESTION DES ERREURS ET RECONNECTION
# ==========================================================

class ErrorRecovery:
    """
    Gestionnaire d'erreurs avec retry automatique et
    notification Telegram.

    Fonctionnalités :
    - Retry automatique en cas d'erreur réseau ou API
    - Délai exponentiel entre les tentatives
    - Notification Telegram après un certain nombre d'échecs
    - Reprise automatique après reconnexion
    """

    def __init__(
        self,
        max_consecutive_errors: int = 5,
        base_retry_delay: int = 30,
        max_retry_delay: int = 300,
        notify_after: int = 3,
    ):
        self.max_consecutive_errors = max_consecutive_errors
        self.base_retry_delay = base_retry_delay
        self.max_retry_delay = max_retry_delay
        self.notify_after = notify_after

        self._consecutive_errors = 0
        self._error_start_time = None
        self._notified = False

    def handle_error(self, error: Exception) -> int:
        """
        Gère une erreur et retourne le délai de retry en secondes.

        Retourne -1 si le nombre max d'erreurs est atteint (arrêt requis).
        """
        self._consecutive_errors += 1

        if self._error_start_time is None:
            self._error_start_time = datetime.now(timezone.utc)

        logger.error(
            f"❌ Erreur #{self._consecutive_errors} : {type(error).__name__} — {error}"
        )

        # Notifier via Telegram après N erreurs
        if self._consecutive_errors >= self.notify_after and not self._notified:
            error_msg = (
                f"{type(error).__name__}: {error}\n"
                f"Erreurs consécutives : {self._consecutive_errors}"
            )
            try:
                alert_engine.send_error(error_msg)
            except Exception:
                pass  # Ne pas bloquer sur une erreur de notification
            self._notified = True

        # Vérifier si on doit arrêter
        if self._consecutive_errors >= self.max_consecutive_errors:
            logger.critical(
                f"🚨 {self.max_consecutive_errors} erreurs consécutives. "
                f"Arrêt du bot."
            )
            return -1

        # Calcul du délai exponentiel
        delay = min(
            self.base_retry_delay * (2 ** (self._consecutive_errors - 1)),
            self.max_retry_delay,
        )

        logger.info(f"⏱ Retry dans {delay}s (tentative {self._consecutive_errors})")
        return delay

    def reset(self) -> None:
        """Réinitialise le compteur d'erreurs après une récupération."""
        if self._consecutive_errors > 0:
            downtime = 0
            if self._error_start_time:
                delta = datetime.now(timezone.utc) - self._error_start_time
                downtime = int(delta.total_seconds() / 60)

            logger.info(
                f"✅ Reconnexion réussie après {self._consecutive_errors} erreurs "
                f"({downtime} min d'indisponibilité)"
            )

            # Notifier la reprise
            if self._notified:
                try:
                    alert_engine.send_recovery(downtime)
                except Exception:
                    pass

        self._consecutive_errors = 0
        self._error_start_time = None
        self._notified = False


# ==========================================================
# FONCTION DE SCAN PRINCIPAL
# ==========================================================

def scan_markets() -> bool:
    """
    Effectue un scan complet de toutes les paires et envoie
    les signaux via le moteur d'alertes.

    Retourne True si le scan a réussi, False sinon.
    """
    scan_start = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info(
        f"🔍 Début du scan — {scan_start.strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    logger.info("=" * 60)

    try:
        # Récupérer les données pour toutes les paires
        market_data = market_fetcher.fetch_all()

        if not market_data:
            logger.warning("⚠️ Aucune donnée de marché disponible. Scan ignoré.")
            return True  # Pas une erreur critique

        signals_sent = 0
        signals_blocked = 0
        neutral_count = 0

        for pair, df in market_data.items():
            if df is None or df.empty:
                logger.warning(f"⚠️ {pair} : DataFrame vide, analyse ignorée")
                continue

            # Analyser les données
            result = analyzer.analyze(df, pair)

            # Traiter le résultat via le moteur d'alertes
            if result.signal != SignalType.NEUTRE:
                sent = alert_engine.process_signal(result)
                if sent:
                    signals_sent += 1
                else:
                    # Soit doublon, soit échec d'envoi
                    if alert_engine.dedup.is_duplicate(
                        result.pair, result.timestamp, result.direction
                    ):
                        signals_blocked += 1
            else:
                neutral_count += 1

        scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
        logger.info(
            f"📊 Scan terminé en {scan_duration:.1f}s — "
            f"{signals_sent} signal(aux) envoyé(s) | "
            f"{signals_blocked} doublon(s) bloqué(s) | "
            f"{neutral_count} neutre(s) | "
            f"{len(market_data)} paire(s) analysée(s)"
        )

        return True

    except Exception as e:
        logger.error(f"❌ Erreur pendant le scan : {e}")
        logger.debug(traceback.format_exc())
        return False


# ==========================================================
# BOUCLE PRINCIPALE SYNCHRONISÉE M5
# ==========================================================

def main():
    """Point d'entrée principal du bot."""
    logger.info("=" * 60)
    logger.info("🤖 BOT DE SIGNAUX FOREX — DÉMARRAGE")
    logger.info("=" * 60)

    # 1. Valider la configuration
    logger.info("📋 Vérification de la configuration...")
    if not config.validate():
        logger.error("❌ Configuration invalide. Vérifiez le fichier .env")
        sys.exit(1)

    logger.info(f"  ✅ Source de données : {config.DATA_SOURCE}")
    logger.info(f"  ✅ Paires surveillées : {config.FOREX_PAIRS}")
    logger.info(f"  ✅ Timeframe : {config.TIMEFRAME}")
    logger.info(
        f"  ✅ EMA : {config.EMA_PERIOD} | RSI : {config.RSI_PERIOD} | "
        f"BB : {config.BB_PERIOD},{config.BB_STD}"
    )

    # 2. Tester la connexion Telegram
    logger.info("📡 Test de la connexion Telegram...")
    if not telegram_bot.test_connection():
        logger.error("❌ Impossible de se connecter au Bot Telegram. Vérifiez le token.")
        sys.exit(1)

    # 3. Envoyer le message de démarrage
    logger.info("📤 Envoi du message de démarrage...")
    alert_engine.send_startup(config.FOREX_PAIRS)

    # 4. Initialiser le gestionnaire d'erreurs
    error_recovery = ErrorRecovery(
        max_consecutive_errors=10,
        base_retry_delay=30,
        max_retry_delay=300,
        notify_after=3,
    )

    # 5. Premier scan immédiat
    logger.info("🔄 Premier scan immédiat...")
    scan_markets()
    error_recovery.reset()

    # 6. Boucle principale synchronisée sur les clôtures M5
    logger.info("🕐 Synchronisation sur les clôtures de bougies M5...")
    logger.info("💡 Appuyez sur Ctrl+C pour arrêter le bot.")

    try:
        while True:
            # Attendre la prochaine clôture de bougie M5
            next_close = candle_sync.get_next_candle_close_time()
            logger.info(
                f"⏱ En attente de la clôture M5 à "
                f"{next_close.strftime('%H:%M:%S')} UTC..."
            )
            candle_sync.wait_for_next_candle()

            # Effectuer le scan
            logger.info("🔔 Clôture de bougie M5 détectée ! Lancement du scan...")
            success = scan_markets()

            if success:
                error_recovery.reset()
            else:
                retry_delay = error_recovery.handle_error(
                    Exception("Échec du scan de marché")
                )
                if retry_delay == -1:
                    logger.critical("🚨 Trop d'erreurs consécutives. Arrêt du bot.")
                    alert_engine.send_error(
                        "Arrêt automatique : trop d'erreurs consécutives"
                    )
                    break

                # Attendre avant de réessayer
                logger.info(f"⏱ Attente de {retry_delay}s avant retry...")
                time.sleep(retry_delay)

            # Afficher les stats périodiquement
            stats = alert_engine.get_stats()
            logger.info(
                f"📈 Stats : {stats['signals_sent']} signaux envoyés | "
                f"{stats['signals_blocked']} doublons bloqués | "
                f"{stats['errors']} erreurs"
            )

    except KeyboardInterrupt:
        logger.info("🛑 Arrêt demandé par l'utilisateur (Ctrl+C)")
    except Exception as e:
        logger.critical(f"🚨 Erreur fatale : {e}")
        logger.debug(traceback.format_exc())
        try:
            alert_engine.send_error(f"Erreur fatale : {type(e).__name__} — {e}")
        except Exception:
            pass

    # 7. Arrêt propre
    logger.info("👋 Arrêt du bot...")
    alert_engine.send_shutdown()

    # Stats finales
    stats = alert_engine.get_stats()
    logger.info(f"📊 Statistiques finales : {stats}")


if __name__ == "__main__":
    main()
