"""
=============================================================
MODULE DE SIMULATION OTC (WEEK-END / MARCHÉ FERMÉ)
=============================================================
Quand le marché Forex réel est fermé (week-end, jours fériés),
les paires OTC sur Olymp Trade continuent de bouger.

Ce module simule les mouvements OTC en :
  1. Récupérant les dernières données réelles (vendredi)
  2. Ajoutant des variations réalistes (mouvement brownien)
  3. Générant de nouvelles bougies M5 pour l'analyse

Les variations sont calibrées sur la volatilité réelle de
chaque paire pour être réalistes.
=============================================================
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class OTCSimulator:
    """Simule les données de marché OTC quand le marché réel est fermé."""

    def __init__(self):
        self._last_real_data: dict = {}  # Dernières données réelles par paire
        self._simulated_candles: dict = {}  # Bougies simulées en cache

    def is_market_open(self) -> bool:
        """Vérifie si le marché Forex est ouvert."""
        now = datetime.now(timezone.utc)
        day = now.weekday()  # 0=Lundi, 6=Dimanche

        # Samedi (5) = fermé
        if day == 5:
            return False

        # Dimanche (6) = ouvert à partir de 22h UTC
        if day == 6:
            return now.hour >= 22

        # Vendredi (4) = fermé après 22h UTC
        if day == 4 and now.hour >= 22:
            return False

        return True

    def generate_otc_candles(
        self,
        real_df: pd.DataFrame,
        symbol: str,
        num_candles: int = 10,
    ) -> Optional[pd.DataFrame]:
        """
        Génère des bougies M5 simulées pour une paire OTC
        à partir des dernières données réelles.

        Utilise un mouvement brownien géométrique calibré
        sur la volatilité réelle de la paire.
        """
        if real_df is None or real_df.empty:
            logger.warning(f"⚠️ OTC {symbol} : Pas de données réelles pour simulation")
            return None

        # Calculer la volatilité réelle (écart-type des rendements)
        returns = real_df["Close"].pct_change().dropna()
        if len(returns) < 10:
            return None

        volatility = returns.std()
        last_close = real_df["Close"].iloc[-1]
        last_high = real_df["High"].iloc[-1]
        last_low = real_df["Low"].iloc[-1]

        # Facteur de réduction de volatilité le week-end
        # (OTC est moins volatil que le marché réel)
        weekend_factor = 0.6

        sigma = volatility * weekend_factor
        mu = returns.mean() * weekend_factor

        # Générer les nouvelles bougies
        now_utc = datetime.now(timezone.utc)
        candles = []

        current_close = last_close

        for i in range(num_candles):
            # Timestamp de la bougie (en partant de la plus ancienne)
            candle_time = now_utc - timedelta(minutes=5 * (num_candles - i))
            candle_time = candle_time.replace(second=0, microsecond=0)
            # Arrondir à la bougie M5 la plus proche
            minute = (candle_time.minute // 5) * 5
            candle_time = candle_time.replace(minute=minute)

            # Mouvement brownien géométrique
            dt = 1.0  # 1 bougie = 1 unité de temps
            random_shock = np.random.normal(0, 1)

            # Nouveau prix de clôture
            new_close = current_close * np.exp(
                (mu - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * random_shock
            )

            # Générer High et Low réalistes
            spread = abs(new_close - current_close)
            intra_vol = sigma * current_close * 0.5

            high = max(current_close, new_close) + abs(np.random.normal(0, intra_vol))
            low = min(current_close, new_close) - abs(np.random.normal(0, intra_vol))

            # S'assurer que High >= Close >= Low
            high = max(high, new_close, current_close)
            low = min(low, new_close, current_close)

            # Open = Close de la bougie précédente
            open_price = current_close

            candles.append({
                "Open": open_price,
                "High": high,
                "Low": low,
                "Close": new_close,
                "Volume": int(np.random.exponential(real_df["Volume"].mean() * 0.5)),
            })

            current_close = new_close

        # Construire le DataFrame
        df = pd.DataFrame(candles)

        # Combiner avec les données réelles (garder les 100 dernières bougies réelles + simulées)
        real_tail = real_df.tail(100).copy()
        # Uniformiser les index en naive UTC
        if real_tail.index.tz is not None:
            real_tail.index = real_tail.index.tz_localize(None)

        sim_index = []
        for i in range(num_candles):
            t = now_utc - timedelta(minutes=5 * (num_candles - i - 1))
            minute = (t.minute // 5) * 5
            t = t.replace(second=0, microsecond=0, minute=minute)
            sim_index.append(t.replace(tzinfo=None))  # naive datetime

        df.index = pd.DatetimeIndex(sim_index)

        combined = pd.concat([real_tail, df])
        combined.sort_index(inplace=True)
        combined = combined[~combined.index.duplicated(keep='last')]

        logger.info(
            f"🔄 OTC Simulation : {symbol} | {num_candles} bougies générées | "
            f"Volatilité={sigma*100:.4f}% | Dernier prix={current_close:.5f}"
        )

        return combined

    def get_or_generate(
        self,
        otc_symbol: str,
        real_df: pd.DataFrame,
        real_symbol: str,
    ) -> Optional[pd.DataFrame]:
        """
        Retourne les données OTC :
        - Si le marché est ouvert → utilise les données réelles
        - Si le marché est fermé → génère des données simulées
        """
        if self.is_market_open():
            # Marché ouvert : utiliser les données réelles directement
            return real_df

        # Marché fermé : simuler
        logger.info(f"🌙 Marché fermé — Simulation OTC pour {otc_symbol}")

        # Vérifier si on a déjà des données simulées récentes
        cached = self._simulated_candles.get(otc_symbol)
        if cached:
            last_sim_time = cached["last_sim_time"]
            now = datetime.now(timezone.utc)
            # Simuler de nouvelles bougies toutes les 5 minutes
            if (now - last_sim_time).total_seconds() < 280:
                return cached["df"]

        # Générer de nouvelles bougies simulées
        sim_df = self.generate_otc_candles(real_df, otc_symbol, num_candles=5)

        if sim_df is not None:
            self._simulated_candles[otc_symbol] = {
                "df": sim_df,
                "last_sim_time": datetime.now(timezone.utc),
            }

        return sim_df


# Instance globale
otc_simulator = OTCSimulator()
