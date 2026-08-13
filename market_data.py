"""
=============================================================
MODULE DE RÉCUPÉRATION DES DONNÉES DE MARCHÉ
=============================================================
Récupère les données OHLCV en temps réel (M5) via yfinance
ou OANDA, et les formate dans un DataFrame Pandas propre.

Support des paires OTC :
  - Les paires OTC utilisent les données de la paire réelle
    sous-jacente comme source de prix.
  - Le bot analyse les données réelles mais envoie le signal
    avec le nom de la paire OTC.
  - Cela permet de trader 24h/24 sur Olymp Trade, même les
    week-ends quand le marché réel est fermé.
=============================================================
"""

import logging
import time
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from config import config
from otc_simulator import otc_simulator

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """Récupère et gère les données de marché Forex en temps réel."""

    YF_INTERVAL_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
    }

    YF_PERIOD_MAP = {
        "1m": "7d",
        "5m": "5d",
        "15m": "15d",
        "30m": "30d",
        "1h": "60d",
    }

    def __init__(self, source: Optional[str] = None, max_retries: int = 3, retry_delay: float = 5.0):
        self.source = source or config.DATA_SOURCE
        self.interval = config.YF_INTERVAL
        self.period = config.YF_PERIOD
        self._cache: dict = {}  # Cache des données par paire RÉELLE
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    def fetch_yfinance(self, symbol: str, interval: str = "5m", period: str = "5d") -> Optional[pd.DataFrame]:
        """Récupère les données OHLCV via yfinance avec retry automatique."""
        import yfinance as yf

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(f"📥 Récupération yfinance : {symbol} | {interval} | {period}")

                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)

                if df is None or df.empty:
                    logger.warning(f"⚠️ Aucune donnée reçue pour {symbol} (tentative {attempt})")
                    if attempt < self._max_retries:
                        time.sleep(self._retry_delay)
                        continue
                    return None

                # Standardiser les noms de colonnes
                df = self._standardize_dataframe(df, symbol)

                # Vérifier que les données sont valides
                if df.empty or len(df) < 10:
                    logger.warning(f"⚠️ Données insuffisantes pour {symbol} ({len(df)} bougies)")
                    if attempt < self._max_retries:
                        time.sleep(self._retry_delay)
                        continue
                    return None

                # Mise en cache (toujours avec le symbole réel)
                self._cache[symbol] = {
                    "df": df,
                    "last_update": datetime.now(),
                    "last_candle_time": df.index[-1] if len(df) > 0 else None,
                }

                logger.info(
                    f"✅ {symbol} : {len(df)} bougies récupérées "
                    f"(dernière : {df.index[-1] if len(df) > 0 else 'N/A'})"
                )
                return df

            except Exception as e:
                logger.warning(
                    f"⚠️ Erreur yfinance pour {symbol} (tentative {attempt}/{self._max_retries}) : {e}"
                )
                if attempt < self._max_retries:
                    time.sleep(self._retry_delay * attempt)
                else:
                    logger.error(f"❌ Échec yfinance pour {symbol} après {self._max_retries} tentatives")
                    return None

        return None

    def fetch_oanda(self, symbol: str, count: int = 500) -> Optional[pd.DataFrame]:
        """Récupère les données OHLCV via l'API OANDA."""
        try:
            import oandapyV20
            import oandapyV20.endpoints.instruments as instruments

            client = oandapyV20.API(
                access_token=config.OANDA_API_KEY,
                environment=config.OANDA_BASE_URL,
            )

            oanda_instrument = symbol.replace("=X", "").replace("/", "_")

            params = {
                "granularity": "M5",
                "count": count,
                "price": "M",
            }

            r = instruments.InstrumentsCandles(instrument=oanda_instrument, params=params)
            client.request(r)

            candles = r.response.get("candles", [])
            if not candles:
                logger.warning(f"⚠️ Aucune bougie OANDA pour {symbol}")
                return None

            data = []
            for c in candles:
                if c.get("complete", False):
                    data.append(
                        {
                            "Open": float(c["mid"]["o"]),
                            "High": float(c["mid"]["h"]),
                            "Low": float(c["mid"]["l"]),
                            "Close": float(c["mid"]["c"]),
                            "Volume": int(c.get("volume", 0)),
                        }
                    )

            df = pd.DataFrame(data)
            df = self._standardize_dataframe(df, symbol)

            self._cache[symbol] = {
                "df": df,
                "last_update": datetime.now(),
                "last_candle_time": df.index[-1] if len(df) > 0 else None,
            }

            logger.info(f"✅ {symbol} : {len(df)} bougies OANDA récupérées")
            return df

        except ImportError:
            logger.error("❌ oandapyV20 non installé. Exécutez : pip install oandapyV20")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur OANDA pour {symbol} : {e}")
            return None

    def fetch(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Récupère les données selon la source configurée.
        Pour les paires OTC, récupère les données de la paire réelle.
        """
        # Si c'est une paire OTC, on récupère les données de la paire réelle
        if config.is_otc(symbol):
            real_pair = config.get_real_pair(symbol)
            logger.info(f"🔄 OTC : {symbol} → données de {real_pair}")
            return self.fetch(real_pair)

        # Paire réelle
        if self.source == "yfinance":
            return self.fetch_yfinance(symbol, self.interval, self.period)
        elif self.source == "oanda":
            return self.fetch_oanda(symbol)
        else:
            logger.error(f"❌ Source de données inconnue : {self.source}")
            return None

    def fetch_all_real(self) -> dict:
        """
        Récupère les données pour toutes les paires RÉELLES à scanner.
        C'est la seule méthode qui télécharge des données.
        Les paires OTC partageront les données de leur paire réelle.
        """
        # Obtenir la liste unique des paires réelles à télécharger
        real_pairs = config.get_all_scan_pairs()

        results = {}
        for pair in real_pairs:
            df = self.fetch(pair)
            if df is not None:
                results[pair] = df
            else:
                logger.warning(f"⚠️ Impossible de récupérer les données pour {pair}")
            time.sleep(0.5)
        return results

    def fetch_all(self) -> dict:
        """
        Récupère les données pour toutes les paires (réelles + OTC).
        Les paires OTC partagent les données de leur paire réelle.
        """
        # 1. Télécharger les données réelles (une seule fois par paire)
        real_data = self.fetch_all_real()

        # 2. Construire le dictionnaire complet (réelles + OTC)
        all_data = dict(real_data)  # Copier les données réelles

        # 3. Ajouter les paires OTC (réelles ou simulées)
        if config.OTC_ENABLED:
            market_open = otc_simulator.is_market_open()

            for otc_pair in config.OTC_PAIRS:
                real_pair = config.get_real_pair(otc_pair)
                if real_pair in real_data:
                    if market_open:
                        # Marché ouvert : OTC = mêmes données réelles
                        all_data[otc_pair] = real_data[real_pair]
                        logger.debug(f"🔄 OTC : {otc_pair} → données réelles")
                    else:
                        # Marché fermé : simuler les données OTC
                        sim_df = otc_simulator.get_or_generate(
                            otc_pair, real_data[real_pair], real_pair
                        )
                        if sim_df is not None:
                            all_data[otc_pair] = sim_df
                            logger.info(f"🌙 OTC : {otc_pair} → données simulées (marché fermé)")
                        else:
                            all_data[otc_pair] = real_data[real_pair]
                            logger.warning(f"⚠️ OTC : {otc_pair} → simulation échouée, données réelles")
                else:
                    logger.warning(f"⚠️ OTC : {otc_pair} → pas de données pour {real_pair}")

        return all_data

    def get_cached(self, symbol: str) -> Optional[pd.DataFrame]:
        """Retourne les données en cache pour une paire."""
        # Pour OTC, chercher dans le cache de la paire réelle
        if config.is_otc(symbol):
            real_pair = config.get_real_pair(symbol)
            cached = self._cache.get(real_pair)
        else:
            cached = self._cache.get(symbol)

        if cached:
            return cached["df"]
        return None

    def is_candle_closed(self, symbol: str) -> bool:
        """Vérifie si la dernière bougie M5 est clôturée."""
        if config.is_otc(symbol):
            symbol = config.get_real_pair(symbol)

        cached = self._cache.get(symbol)
        if not cached:
            return True

        fresh_df = self.fetch(symbol)
        if fresh_df is None or fresh_df.empty:
            return False

        last_cached_time = cached.get("last_candle_time")
        last_fresh_time = fresh_df.index[-1]

        if last_cached_time is None or last_fresh_time != last_cached_time:
            self._cache[symbol] = {
                "df": fresh_df,
                "last_update": datetime.now(),
                "last_candle_time": last_fresh_time,
            }
            return True

        return False

    def _standardize_dataframe(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Standardise le DataFrame : colonnes, types, index."""
        rename_map = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower == "open":
                rename_map[col] = "Open"
            elif col_lower == "high":
                rename_map[col] = "High"
            elif col_lower == "low":
                rename_map[col] = "Low"
            elif col_lower == "close":
                rename_map[col] = "Close"
            elif col_lower == "volume":
                rename_map[col] = "Volume"

        df = df.rename(columns=rename_map)

        required_cols = ["Open", "High", "Low", "Close"]
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"❌ Colonne manquante : {col}")
                return pd.DataFrame()

        for col in ["Open", "High", "Low", "Close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if "Volume" in df.columns:
            df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype(int)
        else:
            df["Volume"] = 0

        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)

        # Supprimer les lignes plates (données de week-end)
        price_range = df["High"] - df["Low"]
        df = df[price_range > 0].copy()

        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        df.sort_index(inplace=True)
        df = df[["Open", "High", "Low", "Close", "Volume"]]

        return df


# Instance globale
market_fetcher = MarketDataFetcher()
