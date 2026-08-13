"""
=============================================================
CONFIGURATION CENTRALE DU BOT DE SIGNAUX FOREX
=============================================================
Charge les variables d'environnement et expose la config
sous forme d'objet structuré.

Inclut le support des paires OTC (Over The Counter)
disponibles 24h/24 sur Olymp Trade.
=============================================================
"""

import os
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv()


class Config:
    """Configuration globale du bot."""

    # --- Telegram ---
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # --- Source de données ---
    DATA_SOURCE: str = os.getenv("DATA_SOURCE", "yfinance").lower()

    # --- OANDA ---
    OANDA_API_KEY: str = os.getenv("OANDA_API_KEY", "")
    OANDA_ACCOUNT_ID: str = os.getenv("OANDA_ACCOUNT_ID", "")
    OANDA_BASE_URL: str = os.getenv("OANDA_BASE_URL", "https://api-fxpractice.oanda.com")

    # --- Paires Forex ---
    FOREX_PAIRS: list = [
        p.strip()
        for p in os.getenv("FOREX_PAIRS", "EURUSD=X,GBPUSD=X,AUDJPY=X").split(",")
        if p.strip()
    ]

    # --- Paires OTC (activées par défaut) ---
    OTC_ENABLED: bool = os.getenv("OTC_ENABLED", "true").lower() in ("true", "1", "yes")
    OTC_PAIRS: list = [
        p.strip()
        for p in os.getenv("OTC_PAIRS", "EURUSD=X,GBPUSD=X,USDJPY=X,AUDUSD=X,EURGBP=X,GBPJPY=X").split(",")
        if p.strip()
    ]

    # --- Paramètres de la stratégie ---
    TIMEFRAME: str = os.getenv("TIMEFRAME", "5m")
    EMA_PERIOD: int = int(os.getenv("EMA_PERIOD", "20"))
    RSI_PERIOD: int = int(os.getenv("RSI_PERIOD", "14"))
    BB_PERIOD: int = int(os.getenv("BB_PERIOD", "20"))
    BB_STD: float = float(os.getenv("BB_STD", "2"))

    # --- Paramètres d'exécution ---
    SCAN_INTERVAL: int = int(os.getenv("SCAN_INTERVAL", "300"))

    # --- Fuseau horaire ---
    TIMEZONE_OFFSET: int = int(os.getenv("TIMEZONE_OFFSET", "1"))

    # --- Dictionnaire de mapping des paires ---
    PAIR_DISPLAY: dict = {
        # Paires réelles
        "EURUSD=X": "EUR/USD",
        "GBPUSD=X": "GBP/USD",
        "AUDJPY=X": "AUD/JPY",
        "USDJPY=X": "USD/JPY",
        "GBPJPY=X": "GBP/JPY",
        "EURGBP=X": "EUR/GBP",
        "USDCHF=X": "USD/CHF",
        "AUDUSD=X": "AUD/USD",
        "NZDUSD=X": "NZD/USD",
        "USDCAD=X": "USD/CAD",
        # Paires OTC
        "OTC_EURUSD": "EUR/USD (OTC)",
        "OTC_GBPUSD": "GBP/USD (OTC)",
        "OTC_USDJPY": "USD/JPY (OTC)",
        "OTC_AUDUSD": "AUD/USD (OTC)",
        "OTC_EURGBP": "EUR/GBP (OTC)",
        "OTC_GBPJPY": "GBP/JPY (OTC)",
        "OTC_AUDJPY": "AUD/JPY (OTC)",
        "OTC_USDCHF": "USD/CHF (OTC)",
        "OTC_NZDUSD": "NZD/USD (OTC)",
        "OTC_USDCAD": "USD/CAD (OTC)",
    }

    # --- Mapping OTC → Paire réelle (source de données) ---
    OTC_TO_REAL: dict = {
        "OTC_EURUSD": "EURUSD=X",
        "OTC_GBPUSD": "GBPUSD=X",
        "OTC_USDJPY": "USDJPY=X",
        "OTC_AUDUSD": "AUDUSD=X",
        "OTC_EURGBP": "EURGBP=X",
        "OTC_GBPJPY": "GBPJPY=X",
        "OTC_AUDJPY": "AUDJPY=X",
        "OTC_USDCHF": "USDCHF=X",
        "OTC_NZDUSD": "NZDUSD=X",
        "OTC_USDCAD": "USDCAD=X",
    }

    # --- Mapping Paire réelle → OTC correspondante ---
    REAL_TO_OTC: dict = {v: k for k, v in OTC_TO_REAL.items()}

    # --- Mapping timeframe yfinance ---
    YF_INTERVAL: str = "5m"
    YF_PERIOD: str = "5d"

    @classmethod
    def validate(cls) -> bool:
        """Vérifie que les variables critiques sont définies."""
        errors = []
        if not cls.TELEGRAM_TOKEN:
            errors.append("TELEGRAM_TOKEN manquant dans .env")
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID manquant dans .env")
        if not cls.FOREX_PAIRS and not cls.OTC_PAIRS:
            errors.append("Aucune paire configurée (FOREX_PAIRS et OTC_PAIRS vides)")
        if errors:
            for e in errors:
                print(f"❌ ERREUR CONFIG : {e}")
            return False
        return True

    @classmethod
    def get_display_pair(cls, symbol: str) -> str:
        """Retourne le nom d'affichage d'une paire."""
        return cls.PAIR_DISPLAY.get(symbol, symbol.replace("=X", ""))

    @classmethod
    def is_otc(cls, symbol: str) -> bool:
        """Vérifie si une paire est OTC."""
        return symbol.startswith("OTC_")

    @classmethod
    def get_real_pair(cls, otc_symbol: str) -> str:
        """Retourne la paire réelle correspondant à une paire OTC."""
        return cls.OTC_TO_REAL.get(otc_symbol, otc_symbol)

    @classmethod
    def get_all_scan_pairs(cls) -> list:
        """
        Retourne toutes les paires à scanner (réelles + OTC).
        Les paires OTC utilisent les mêmes données que les paires réelles,
        donc on ne télécharge les données qu'une seule fois par paire réelle.
        """
        # Paires réelles uniques à télécharger
        real_pairs = set(cls.FOREX_PAIRS)

        # Ajouter les paires réelles sous-jacentes des OTC
        if cls.OTC_ENABLED:
            for otc_pair in cls.OTC_PAIRS:
                real_pair = cls.OTC_TO_REAL.get(otc_pair)
                if real_pair:
                    real_pairs.add(real_pair)

        return list(real_pairs)

    @classmethod
    def get_all_signal_pairs(cls) -> list:
        """
        Retourne toutes les paires pour lesquelles on génère des signaux.
        Inclut les paires réelles + les paires OTC.
        """
        pairs = list(cls.FOREX_PAIRS)
        if cls.OTC_ENABLED:
            pairs.extend(cls.OTC_PAIRS)
        return pairs


# Instance globale
config = Config()
