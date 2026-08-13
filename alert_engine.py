"""
=============================================================
MOTEUR D'ALERTE — GESTION DES SIGNAUX & DÉDOUBLONNAGE
=============================================================
Responsabilités :
  1. Déclencher l'alerte exactement à la clôture de la bougie M5
  2. Éviter les doublons (un signal unique par bougie clôturée)
  3. Formater le message Telegram selon le template requis
  4. Gérer les files d'attente et les retry

Template du message Telegram :
  🚨 SIGNAL OLYMP TRADE (M5)
  📊 Actif : [Ex: EUR/USD]
  📈 Action : [HAUT (🟢) / BAS (🔴)]
  ⏱️ Durée d'expiration : 5 Minutes
  🎯 Entrée : À l'ouverture immédiate de la bougie suivante
  💡 Raison : [Ex: RSI Sur-vendu + Rebond Bollinger + Tendance EMA 50]
=============================================================
"""

import logging
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Set
from dataclasses import dataclass

from config import config
from telegram_bot import telegram_bot
from analysis import SignalResult, SignalType

logger = logging.getLogger(__name__)


# ==========================================================
# GESTIONNAIRE DE DÉDOUBLONNAGE
# ==========================================================

class DeduplicationManager:
    """
    Gère le dédoublonnage des signaux pour éviter l'envoi
    multiple du même signal pour une même bougie.

    Principe : chaque signal est identifié par un hash unique
    composé de la paire + l'horodatage de la bougie clôturée.
    Un signal pour une bougie donnée n'est envoyé qu'une seule fois.
    """

    def __init__(self, max_history: int = 1000):
        self._sent_signals: Dict[str, datetime] = {}  # hash → timestamp d'envoi
        self._max_history = max_history

    def _generate_hash(self, pair: str, candle_time: str, direction: str) -> str:
        """Génère un hash unique pour un signal donné."""
        key = f"{pair}|{candle_time}|{direction}"
        return hashlib.md5(key.encode()).hexdigest()

    def is_duplicate(self, pair: str, candle_time: str, direction: str) -> bool:
        """Vérifie si un signal a déjà été envoyé pour cette bougie."""
        signal_hash = self._generate_hash(pair, candle_time, direction)
        return signal_hash in self._sent_signals

    def mark_sent(self, pair: str, candle_time: str, direction: str) -> None:
        """Marque un signal comme envoyé."""
        signal_hash = self._generate_hash(pair, candle_time, direction)
        self._sent_signals[signal_hash] = datetime.now()

        # Nettoyer l'historique si trop long
        if len(self._sent_signals) > self._max_history:
            self._cleanup()

    def _cleanup(self) -> None:
        """Supprime les entrées les plus anciennes."""
        sorted_keys = sorted(
            self._sent_signals.keys(),
            key=lambda k: self._sent_signals[k],
        )
        # Garder la moitié des entrées les plus récentes
        to_remove = sorted_keys[: len(sorted_keys) // 2]
        for k in to_remove:
            del self._sent_signals[k]
        logger.debug(f"🧹 Dédoublonnage : {len(to_remove)} entrées nettoyées")

    def get_stats(self) -> dict:
        """Retourne les statistiques de dédoublonnage."""
        return {
            "total_tracked": len(self._sent_signals),
            "max_history": self._max_history,
        }


# ==========================================================
# FORMATTEUR DE MESSAGE
# ==========================================================

class SignalFormatter:
    """
    Formate les signaux selon le template Telegram requis.

    Format attendu :
      🚨 SIGNAL OLYMP TRADE (M5)
      📊 Actif : [Ex: EUR/USD]
      📈 Action : [HAUT (🟢) / BAS (🔴)]
      ⏱️ Durée d'expiration : 5 Minutes
      🎯 Entrée : À l'ouverture immédiate de la bougie suivante
      💡 Raison : [Ex: RSI Sur-vendu + Rebond Bollinger + Tendance EMA 50]
    """

    @staticmethod
    def format_signal_message(result: SignalResult) -> str:
        """Formate le message de signal Telegram selon le template."""

        pair_display = config.get_display_pair(result.pair)

        # Direction et emoji
        if result.direction == "CALL":
            action = "HAUT (🟢)"
            signal_emoji = "🟢"
        else:
            action = "BAS (🔴)"
            signal_emoji = "🔴"

        # Raison détaillée (utilise les raisons du SignalResult si disponibles)
        reason = SignalFormatter._build_reason(result)

        # Stratégie utilisée
        strategy_label = f"({result.strategy}) " if result.strategy else ""

        # Horodatage formaté
        signal_time = SignalFormatter._format_timestamp(result.timestamp)

        # Marqueur OTC
        is_otc = config.is_otc(result.pair)
        otc_badge = " [OTC]" if is_otc else ""

        message = f"""🚨 <b>SIGNAL OLYMP TRADE (M5)</b> {signal_emoji}{otc_badge}

📊 <b>Actif :</b> {pair_display}

📈 <b>Action :</b> {action}

⏱️ <b>Durée d'expiration :</b> 5 Minutes

🎯 <b>Entrée :</b> À l'ouverture immédiate de la bougie suivante

💡 <b>Raison :</b> {strategy_label}{reason}

━━━━━━━━━━━━━━━━━━━━━━━━
📋 <b>Détails techniques</b>
━━━━━━━━━━━━━━━━━━━━━━━━

💰 Prix de clôture : <code>{result.price:.5f}</code>
📈 EMA {config.EMA_PERIOD} : <code>{result.ema:.5f}</code>
📉 RSI 14 : <code>{result.rsi_prev:.1f} → {result.rsi:.1f}</code>

🔵 Bollinger Sup : <code>{result.bb_upper:.5f}</code>
⚪ Bollinger Moy : <code>{result.bb_middle:.5f}</code>
🔴 Bollinger Inf : <code>{result.bb_lower:.5f}</code>

🎯 Confiance : <b>{result.confidence}</b>
🕐 Heure du signal : <code>{signal_time}</code>

⚠️ <i>Signal généré automatiquement — Tradez de manière responsable.</i>"""

        return message.strip()

    @staticmethod
    def _build_reason(result: SignalResult) -> str:
        """Construit la chaîne de raison du signal."""

        reasons = []

        if result.direction == "CALL":
            # Tendance EMA
            if result.price > result.ema:
                reasons.append("Tendance haussière EMA")

            # RSI Survente
            if result.rsi_prev < 40:
                reasons.append(f"RSI Sur-vendu ({result.rsi_prev:.1f}) → Rebond ({result.rsi:.1f})")

            # Bollinger
            if result.price > result.bb_lower:
                reasons.append("Rejet Bollinger Inférieur")

        elif result.direction == "PUT":
            # Tendance EMA
            if result.price < result.ema:
                reasons.append("Tendance baissière EMA")

            # RSI Surachat
            if result.rsi_prev > 60:
                reasons.append(f"RSI Sur-acheté ({result.rsi_prev:.1f}) → Retournement ({result.rsi:.1f})")

            # Bollinger
            if result.price < result.bb_upper:
                reasons.append("Rejet Bollinger Supérieur")

        return " + ".join(reasons) if reasons else "Conditions techniques réunies"

    @staticmethod
    def _format_timestamp(timestamp_str: str) -> str:
        """Formate un timestamp pour l'affichage en heure locale (GMT+1)."""
        try:
            # Essayer de parser le timestamp
            dt = None
            if isinstance(timestamp_str, str):
                # Formats possibles
                for fmt in [
                    "%Y-%m-%d %H:%M:%S%z",
                    "%Y-%m-%d %H:%M:%S",
                ]:
                    try:
                        dt = datetime.strptime(timestamp_str, fmt)
                        # Si pas de timezone, on suppose UTC
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue

            if dt is not None:
                # Convertir en heure locale (GMT+1)
                local_tz = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
                dt_local = dt.astimezone(local_tz)
                return dt_local.strftime("%Y-%m-%d %H:%M:%S GMT+1")

            return timestamp_str
        except Exception:
            return timestamp_str

    @staticmethod
    def format_startup_message(pairs: list) -> str:
        """Formate le message de démarrage."""
        pairs_display = [config.get_display_pair(p) for p in pairs if not config.is_otc(p)]
        otc_display = [config.get_display_pair(p) for p in pairs if config.is_otc(p)]
        now_utc = datetime.now(timezone.utc)
        local_tz = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
        now_local = now_utc.astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")

        # Section OTC
        otc_section = ""
        if otc_display:
            otc_section = f"""

📊 <b>Paires OTC (24h/24) :</b>
{chr(10).join(f'  • {p}' for p in otc_display)}"""

        message = f"""🤖 <b>Bot de Signaux Forex — ACTIF</b>

📡 <b>Paires réelles :</b>
{chr(10).join(f'  • {p}' for p in pairs_display)}{otc_section}

⏱ Timeframe : <b>M5</b>
📱 Plateforme cible : <b>Olymp Trade</b>
🔄 Mode : <b>Scan automatique à chaque clôture de bougie M5</b>

🕐 Démarré à : <code>{now_local} (GMT+{config.TIMEZONE_OFFSET})</code>

⚡ <i>Le bot détecte les signaux en temps réel et envoie les alertes instantanément.</i>"""

        return message.strip()

    @staticmethod
    def format_shutdown_message() -> str:
        """Formate le message d'arrêt."""
        now_utc = datetime.now(timezone.utc); local_tz = timezone(timedelta(hours=config.TIMEZONE_OFFSET)); now = now_utc.astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"""🛑 <b>Bot de Signaux Forex — ARRÊTÉ</b>

🕐 Arrêté à : <code>{now}</code>

<i>Le bot ne surveille plus les marchés. Redémarrez-le pour reprendre le scan.</i>"""

    @staticmethod
    def format_error_message(error_msg: str) -> str:
        """Formate le message d'erreur."""
        now_utc = datetime.now(timezone.utc); local_tz = timezone(timedelta(hours=config.TIMEZONE_OFFSET)); now = now_utc.astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"""🚨 <b>ERREUR BOT</b>

❌ <code>{error_msg}</code>
🕐 Heure : <code>{now}</code>

<i>Le bot tente de se reconnecter automatiquement.</i>"""

    @staticmethod
    def format_recovery_message(downtime_minutes: int) -> str:
        """Formate le message de reprise après erreur."""
        now_utc = datetime.now(timezone.utc); local_tz = timezone(timedelta(hours=config.TIMEZONE_OFFSET)); now = now_utc.astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"""🟢 <b>Bot de Signaux Forex — RECONNECTION</b>

✅ Le bot est de nouveau opérationnel.
⏱ Temps d'indisponibilité : <code>{downtime_minutes} min</code>
🕐 Heure : <code>{now}</code>

<i>Le scan des marchés a repris.</i>"""


# ==========================================================
# MOTEUR D'ALERTE PRINCIPAL
# ==========================================================

class AlertEngine:
    """
    Moteur d'alerte qui coordonne l'analyse, le dédoublonnage
    et l'envoi des signaux Telegram.

    Fonctionnalités :
    - Déclenchement précis à la clôture de chaque bougie M5
    - Dédoublonnage : un signal par bougie maximum
    - Retry automatique en cas d'échec d'envoi
    - Journalisation complète de toutes les alertes
    """

    def __init__(self):
        self.dedup = DeduplicationManager()
        self.formatter = SignalFormatter()
        self._signals_sent_count: int = 0
        self._signals_blocked_count: int = 0
        self._errors_count: int = 0
        self._last_candle_time: Dict[str, str] = {}  # paire → dernier timestamp de bougie
        self._last_error_time: Optional[datetime] = None
        self._max_retries: int = 3
        self._retry_delay: float = 2.0  # secondes entre les retry

    def process_signal(self, result: SignalResult) -> bool:
        """
        Traite un résultat d'analyse et envoie l'alerte si nécessaire.

        Étapes :
        1. Vérifier si c'est un signal (pas neutre)
        2. Vérifier le dédoublonnage
        3. Formater le message
        4. Envoyer avec retry

        Retourne True si le signal a été envoyé, False sinon.
        """
        # Ignorer les signaux neutres
        if result.signal == SignalType.NEUTRE:
            logger.debug(f"⚪ {result.pair} : Neutre, pas d'alerte")
            return False

        # Vérifier le dédoublonnage
        candle_time = result.timestamp
        if self.dedup.is_duplicate(result.pair, candle_time, result.direction):
            self._signals_blocked_count += 1
            logger.debug(
                f"🚫 Doublon bloqué : {result.pair} | {result.direction} | {candle_time}"
            )
            return False

        # Formater le message
        message = self.formatter.format_signal_message(result)

        # Envoyer avec retry
        sent = self._send_with_retry(message)

        if sent:
            # Marquer comme envoyé
            self.dedup.mark_sent(result.pair, candle_time, result.direction)
            self._signals_sent_count += 1
            self._last_candle_time[result.pair] = candle_time

            pair_display = config.get_display_pair(result.pair)
            logger.info(
                f"📤 ALERTE ENVOYÉE : {pair_display} | {result.direction} | "
                f"Prix={result.price:.5f} | Confiance={result.confidence}"
            )
        else:
            self._errors_count += 1
            self._last_error_time = datetime.now()
            logger.error(
                f"❌ ÉCHEC ENVOI : {result.pair} | {result.direction} | "
                f"Après {self._max_retries} tentatives"
            )

        return sent

    def _send_with_retry(self, message: str) -> bool:
        """Envoie un message Telegram avec retry automatique."""
        for attempt in range(1, self._max_retries + 1):
            try:
                success = telegram_bot.send_message(message)
                if success:
                    return True
                logger.warning(f"⚠️ Tentative {attempt}/{self._max_retries} échouée")
            except Exception as e:
                logger.warning(
                    f"⚠️ Tentative {attempt}/{self._max_retries} — Exception : {e}"
                )

            if attempt < self._max_retries:
                time.sleep(self._retry_delay * attempt)  # Backoff exponentiel

        return False

    def send_startup(self, pairs: list) -> bool:
        """Envoie le message de démarrage."""
        message = self.formatter.format_startup_message(pairs)
        return telegram_bot.send_message(message)

    def send_shutdown(self) -> bool:
        """Envoie le message d'arrêt."""
        message = self.formatter.format_shutdown_message()
        return telegram_bot.send_message(message)

    def send_error(self, error_msg: str) -> bool:
        """Envoie une notification d'erreur."""
        message = self.formatter.format_error_message(error_msg)
        return telegram_bot.send_message(message)

    def send_recovery(self, downtime_minutes: int) -> bool:
        """Envoie une notification de reprise."""
        message = self.formatter.format_recovery_message(downtime_minutes)
        return telegram_bot.send_message(message)

    def get_stats(self) -> dict:
        """Retourne les statistiques du moteur d'alerte."""
        return {
            "signals_sent": self._signals_sent_count,
            "signals_blocked": self._signals_blocked_count,
            "errors": self._errors_count,
            "last_error": str(self._last_error_time) if self._last_error_time else None,
            "last_candles": dict(self._last_candle_time),
            "dedup_stats": self.dedup.get_stats(),
        }


# ==========================================================
# SYNCHRONISATEUR DE BOUGIE M5
# ==========================================================

class CandleSync:
    """
    Synchronise le scan avec la clôture des bougies M5.

    Principe : Le Forex utilise des bougies de 5 minutes qui
    se clôturent aux minutes :00, :05, :10, :15, etc.

    Le synchronisateur calcule le temps exact restant avant
    la prochaine clôture et attend ce délai pour déclencher
    le scan à la seconde près.
    """

    CANDLE_DURATION_SECONDS = 300  # 5 minutes = 300 secondes

    def __init__(self, offset_seconds: int = 2):
        """
        Args:
            offset_seconds: Secondes d'attente après la clôture
                           théorique pour laisser le temps au broker
                           de publier la bougie. Défaut: 2s.
        """
        self.offset_seconds = offset_seconds

    def seconds_until_next_candle_close(self) -> int:
        """
        Calcule le nombre de secondes avant la prochaine clôture
        de bougie M5.

        Les bougies M5 se clôturent à :00, :05, :10, :15, etc.
        On ajoute l'offset pour laisser le temps au broker.
        """
        now = datetime.now(timezone.utc)
        current_minute = now.minute
        current_second = now.second

        # Calculer la minute de clôture suivante (multiple de 5)
        minutes_into_candle = current_minute % 5
        minutes_remaining = 5 - minutes_into_candle

        # Si on est exactement à la clôture (minutes multiples de 5)
        # et qu'on n'a pas encore attendu l'offset, on attend l'offset
        if minutes_into_candle == 0 and current_second < self.offset_seconds:
            return self.offset_seconds - current_second

        # Si on est à la minute de clôture mais après l'offset,
        # on attend la prochaine bougie
        if minutes_into_candle == 0 and current_second >= self.offset_seconds:
            minutes_remaining = 5

        # Calculer le temps total
        seconds_remaining = (minutes_remaining * 60) - current_second + self.offset_seconds

        # Si on est très proche de la clôture (moins de l'offset),
        # on attend la clôture + offset
        if seconds_remaining <= 0:
            seconds_remaining = self.CANDLE_DURATION_SECONDS + self.offset_seconds

        return seconds_remaining

    def get_next_candle_close_time(self) -> datetime:
        """Retourne l'heure exacte de la prochaine clôture de bougie."""
        seconds = self.seconds_until_next_candle_close()
        return datetime.now(timezone.utc) + timedelta(seconds=seconds)

    def get_current_candle_id(self) -> str:
        """Retourne un identifiant unique pour la bougie en cours."""
        now = datetime.now(timezone.utc)
        candle_minute = (now.minute // 5) * 5
        return f"{now.year}-{now.month:02d}-{now.day:02d}_{now.hour:02d}:{candle_minute:02d}"

    def wait_for_next_candle(self) -> None:
        """Attend jusqu'à la prochaine clôture de bougie M5."""
        seconds = self.seconds_until_next_candle_close()
        next_close = self.get_next_candle_close_time()

        logger.info(
            f"⏱ Prochaine clôture M5 dans {seconds}s "
            f"(à {next_close.strftime('%H:%M:%S')} UTC)"
        )

        # Attendre par tranches de 1 seconde pour pouvoir réagir à Ctrl+C
        for _ in range(seconds):
            time.sleep(1)


# Instances globales
alert_engine = AlertEngine()
candle_sync = CandleSync(offset_seconds=2)
