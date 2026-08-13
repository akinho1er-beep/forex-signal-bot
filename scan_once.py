"""
=============================================================
SCAN UNIQUE — Pour GitHub Actions
=============================================================
Ce script fait UN seul scan de toutes les paires,
envoie les signaux sur Telegram, puis s'arrete.

Concu pour etre execute par GitHub Actions toutes les 5 minutes.
=============================================================
"""

import sys
import logging
from datetime import datetime, timezone, timedelta

from config import config
from telegram_bot import telegram_bot
from market_data import market_fetcher
from analysis import analyzer, SignalType
from alert_engine import alert_engine

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("ScanOnce")


def main():
    """Execute un seul scan complet."""
    scan_start = datetime.now(timezone.utc)
    local_tz = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    local_time = scan_start.astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")

    logger.info("=" * 60)
    logger.info(f"Scan unique - {local_time} (GMT+{config.TIMEZONE_OFFSET})")
    logger.info("=" * 60)

    # 1. Verifier la configuration
    if not config.validate():
        logger.error("Configuration invalide")
        sys.exit(1)

    # 2. Recuperer les donnees de marche
    logger.info("Recuperation des donnees de marche...")
    market_data = market_fetcher.fetch_all()

    if not market_data:
        logger.warning("Aucune donnee disponible. Scan ignore.")
        sys.exit(0)

    # 3. Analyser chaque paire
    signals_sent = 0
    signals_blocked = 0
    neutral_count = 0
    error_count = 0

    for pair, df in market_data.items():
        if df is None or df.empty:
            continue

        try:
            # Analyser
            result = analyzer.analyze(df, pair)

            # Traiter le resultat
            if result.signal != SignalType.NEUTRE:
                sent = alert_engine.process_signal(result)
                if sent:
                    signals_sent += 1
                    pair_name = config.get_display_pair(pair)
                    otc_tag = " [OTC]" if config.is_otc(pair) else ""
                    logger.info(
                        f"SIGNAL ENVOYE : {pair_name}{otc_tag} | "
                        f"{result.direction} | {result.confidence}"
                    )
                else:
                    signals_blocked += 1
            else:
                neutral_count += 1

        except Exception as e:
            error_count += 1
            logger.error(f"Erreur analyse {pair} : {e}")

    # 4. Resume
    scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
    logger.info("=" * 60)
    logger.info(
        f"Scan termine en {scan_duration:.1f}s - "
        f"{signals_sent} signal(aux) envoye(s) | "
        f"{signals_blocked} doublon(s) | "
        f"{neutral_count} neutre(s) | "
        f"{error_count} erreur(s) | "
        f"{len(market_data)} paire(s)"
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
