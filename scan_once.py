"""
SCAN UNIQUE - Pour GitHub Actions
Ce script fait UN seul scan de toutes les paires,
envoie les signaux sur Telegram, puis s'arrete.
Concu pour etre execute par GitHub Actions toutes les 5 minutes.
"""

import sys
import os
import logging
import traceback
from datetime import datetime, timezone, timedelta

# Debug: afficher les variables d'environnement (masque les secrets)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ScanOnce")

logger.info("=== ENV CHECK ===")
logger.info(f"TELEGRAM_TOKEN set: {bool(os.getenv('TELEGRAM_TOKEN'))}")
logger.info(f"TELEGRAM_CHAT_ID: {os.getenv('TELEGRAM_CHAT_ID', 'NON DEFINI')}")
logger.info(f"FOREX_PAIRS: {os.getenv('FOREX_PAIRS', 'NON DEFINI')}")
logger.info(f"OTC_ENABLED: {os.getenv('OTC_ENABLED', 'NON DEFINI')}")

try:
    from config import config
    from telegram_bot import telegram_bot
    from market_data import market_fetcher
    from analysis import analyzer, SignalType
    from alert_engine import alert_engine
    logger.info("Tous les imports OK")
except Exception as e:
    logger.error(f"ERREUR IMPORT: {e}")
    traceback.print_exc()
    sys.exit(1)


def main():
    scan_start = datetime.now(timezone.utc)
    local_tz = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    local_time = scan_start.astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")

    logger.info("=" * 60)
    logger.info(f"Scan unique - {local_time} (GMT+{config.TIMEZONE_OFFSET})")
    logger.info("=" * 60)

    if not config.validate():
        logger.error("Configuration invalide!")
        logger.error(f"TOKEN present: {bool(config.TELEGRAM_TOKEN)}")
        logger.error(f"CHAT_ID present: {bool(config.TELEGRAM_CHAT_ID)}")
        logger.error(f"PAIRS: {config.FOREX_PAIRS}")
        sys.exit(1)

    logger.info("Recuperation des donnees de marche...")
    market_data = market_fetcher.fetch_all()

    if not market_data:
        logger.warning("Aucune donnee disponible. Scan ignore.")
        sys.exit(0)

    signals_sent = 0
    signals_blocked = 0
    neutral_count = 0
    error_count = 0

    for pair, df in market_data.items():
        if df is None or df.empty:
            continue
        try:
            result = analyzer.analyze(df, pair)
            if result.signal != SignalType.NEUTRE:
                sent = alert_engine.process_signal(result)
                if sent:
                    signals_sent += 1
                    pair_name = config.get_display_pair(pair)
                    otc_tag = " [OTC]" if config.is_otc(pair) else ""
                    logger.info(f"SIGNAL ENVOYE: {pair_name}{otc_tag} | {result.direction} | {result.confidence}")
                else:
                    signals_blocked += 1
            else:
                neutral_count += 1
        except Exception as e:
            error_count += 1
            logger.error(f"Erreur analyse {pair}: {e}")

    scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
    logger.info("=" * 60)
    logger.info(f"Scan termine en {scan_duration:.1f}s - {signals_sent} envoye(s) | {signals_blocked} doublon(s) | {neutral_count} neutre(s) | {error_count} erreur(s) | {len(market_data)} paire(s)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()