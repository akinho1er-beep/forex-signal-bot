"""
=============================================================
MODULE TELEGRAM - ENVOI DE NOTIFICATIONS
=============================================================
Gère la connexion au Bot Telegram et l'envoi de messages
de signaux vers le canal/groupe configuré.

Inclut :
  - Retry automatique en cas d'échec réseau
  - Gestion du rate limiting Telegram
  - Timeouts configurables
  - Vérification de connexion
=============================================================
"""

import requests
import logging
import time
from typing import Optional

from config import config

logger = logging.getLogger(__name__)


class TelegramBot:
    """Client Telegram pour l'envoi de signaux de trading."""

    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 15,
    ):
        self.token = token or config.TELEGRAM_TOKEN
        self.chat_id = chat_id or config.TELEGRAM_CHAT_ID
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
        # Headers pour optimiser la connexion
        self.session.headers.update({
            "Connection": "keep-alive",
        })
        self._connected: bool = False

    def _url(self, method: str) -> str:
        """Construit l'URL de l'API Telegram."""
        return self.BASE_URL.format(token=self.token, method=method)

    def test_connection(self) -> bool:
        """
        Teste la connexion au Bot Telegram via getMe.
        Effectue plusieurs tentatives en cas d'échec réseau.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(self._url("getMe"), timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                if data.get("ok"):
                    bot_info = data.get("result", {})
                    self._connected = True
                    logger.info(
                        f"✅ Bot Telegram connecté : @{bot_info.get('username', 'N/A')} "
                        f"({bot_info.get('first_name', 'N/A')})"
                    )
                    return True
                else:
                    logger.error(f"❌ Erreur API Telegram : {data}")
                    return False

            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    f"⚠️ Connexion Telegram échouée (tentative {attempt}/{self.max_retries}) : {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

            except requests.exceptions.Timeout:
                logger.warning(
                    f"⚠️ Timeout Telegram (tentative {attempt}/{self.max_retries})"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Échec de connexion Telegram : {e}")
                return False

        self._connected = False
        logger.error(f"❌ Impossible de se connecter à Telegram après {self.max_retries} tentatives")
        return False

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Envoie un message texte au canal/groupe Telegram.
        Inclut retry automatique et gestion du rate limiting.
        """
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.post(
                    self._url("sendMessage"),
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("ok"):
                    logger.info("📤 Message Telegram envoyé avec succès")
                    self._connected = True
                    return True

                # Gestion du rate limiting (429 Too Many Requests)
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After", 30)
                    logger.warning(
                        f"⚠️ Rate limited Telegram. Retry après {retry_after}s"
                    )
                    time.sleep(int(retry_after) + 1)
                    continue

                # Autre erreur API
                error_code = data.get("error_code", "N/A")
                description = data.get("description", "N/A")
                logger.error(
                    f"❌ Erreur API Telegram : code={error_code} | {description}"
                )
                return False

            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    f"⚠️ Connexion perdue (tentative {attempt}/{self.max_retries}) : {e}"
                )
                self._connected = False
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

            except requests.exceptions.Timeout:
                logger.warning(
                    f"⚠️ Timeout envoi (tentative {attempt}/{self.max_retries})"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Échec envoi Telegram : {e}")
                return False

        logger.error(f"❌ Échec envoi après {self.max_retries} tentatives")
        return False

    @property
    def is_connected(self) -> bool:
        """Retourne l'état de la connexion."""
        return self._connected


# Instance globale
telegram_bot = TelegramBot()
