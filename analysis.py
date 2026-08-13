"""
=============================================================
MOTEUR D'ANALYSE TECHNIQUE & STRATÉGIE DE TRADING
=============================================================
Calcule les indicateurs techniques et génère les signaux
d'achat/vente selon 4 stratégies indépendantes.

Chaque paire est analysée individuellement.

Stratégies :
  A - RSI Reversal : RSI sort d'une zone extrême
  B - Bollinger Bounce : Rejet d'une bande de Bollinger
  C - EMA Crossover : Croisement du prix avec l'EMA
  D - RSI Extreme : RSI en zone extrême profonde

Condition d'entrée : 2 conditions sur 3 au minimum
  (Tendance EMA + RSI) OU (Tendance EMA + Bollinger) OU (RSI + Bollinger)
=============================================================
"""

import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List

import numpy as np
import pandas as pd

from config import config

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types de signaux possibles."""
    SIGNAL_ACHAT = "SIGNAL_ACHAT"
    SIGNAL_VENTE = "SIGNAL_VENTE"
    NEUTRE = "NEUTRE"


@dataclass
class SignalResult:
    """Résultat de l'analyse d'une paire."""
    pair: str
    signal: SignalType
    direction: str  # "CALL" ou "PUT"
    price: float
    ema: float
    rsi: float
    rsi_prev: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    confidence: str
    timestamp: str
    details: str
    strategy: str = ""  # Nom de la stratégie qui a déclenché
    reasons: List[str] = field(default_factory=list)  # Liste des raisons


class TechnicalAnalyzer:
    """Moteur d'analyse technique et génération de signaux."""

    def __init__(self):
        self.ema_period = config.EMA_PERIOD
        self.rsi_period = config.RSI_PERIOD
        self.bb_period = config.BB_PERIOD
        self.bb_std = config.BB_STD
        self.rsi_oversold = 40      # Zone de survente (élargie de 30 → 40)
        self.rsi_overbought = 60    # Zone de surachat (élargie de 70 → 60)
        self.rsi_extreme_low = 25   # Survente extrême
        self.rsi_extreme_high = 75  # Surachat extrême
        self.bb_near_threshold = 0.10  # Proximité des bandes BB (10% de la bande)

    # ==========================================================
    # CALCUL DES INDICATEURS
    # ==========================================================

    def calculate_ema(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calcule l'EMA (Exponential Moving Average)."""
        return df["Close"].ewm(span=period, adjust=False).mean()

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calcule le RSI (Relative Strength Index)."""
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        # Moyenne exponentielle (méthode Wilder)
        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi

    def calculate_bollinger_bands(
        self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0
    ) -> tuple:
        """Calcule les Bandes de Bollinger. Retourne (upper, middle, lower)."""
        middle = df["Close"].rolling(window=period).mean()
        std = df["Close"].rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return upper, middle, lower

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute tous les indicateurs au DataFrame."""
        df = df.copy()

        # EMA
        df["EMA"] = self.calculate_ema(df, self.ema_period)

        # RSI 14
        df["RSI_14"] = self.calculate_rsi(df, self.rsi_period)
        df["RSI_14_Prev"] = df["RSI_14"].shift(1)
        df["RSI_14_Prev2"] = df["RSI_14"].shift(2)

        # Bandes de Bollinger
        df["BB_Upper"], df["BB_Middle"], df["BB_Lower"] = self.calculate_bollinger_bands(
            df, self.bb_period, self.bb_std
        )

        # %B de Bollinger (0 = bande inf, 1 = bande sup, 0.5 = milieu)
        df["BB_Pct_B"] = (df["Close"] - df["BB_Lower"]) / (df["BB_Upper"] - df["BB_Lower"])

        # Largeur des bandes de Bollinger (volatilité)
        df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Middle"]

        # Distance du prix par rapport à l'EMA (en %)
        df["EMA_Dist_Pct"] = ((df["Close"] - df["EMA"]) / df["EMA"]) * 100

        # Croisement EMA : le prix croise l'EMA
        df["Close_Prev"] = df["Close"].shift(1)
        df["EMA_Cross_Up"] = (df["Close_Prev"] <= df["EMA"]) & (df["Close"] > df["EMA"])
        df["EMA_Cross_Down"] = (df["Close_Prev"] >= df["EMA"]) & (df["Close"] < df["EMA"])

        return df

    # ==========================================================
    # CONDITIONS INDIVIDUELLES
    # ==========================================================

    def _check_trend_bullish(self, row: pd.Series) -> bool:
        """Vérifie si la tendance est haussière (prix > EMA)."""
        return row["Close"] > row["EMA"]

    def _check_trend_bearish(self, row: pd.Series) -> bool:
        """Vérifie si la tendance est baissière (prix < EMA)."""
        return row["Close"] < row["EMA"]

    def _check_rsi_oversold(self, row: pd.Series) -> bool:
        """Vérifie si le RSI est en zone de survente (< 40)."""
        return row["RSI_14"] < self.rsi_oversold

    def _check_rsi_overbought(self, row: pd.Series) -> bool:
        """Vérifie si le RSI est en zone de surachat (> 60)."""
        return row["RSI_14"] > self.rsi_overbought

    def _check_rsi_oversold_cross_up(self, row: pd.Series) -> bool:
        """RSI sort de la zone de survente (croise à la hausse)."""
        rsi = row["RSI_14"]
        rsi_prev = row["RSI_14_Prev"]
        if pd.isna(rsi) or pd.isna(rsi_prev):
            return False
        return rsi_prev < self.rsi_oversold and rsi >= self.rsi_oversold

    def _check_rsi_overbought_cross_down(self, row: pd.Series) -> bool:
        """RSI sort de la zone de surachat (croise à la baisse)."""
        rsi = row["RSI_14"]
        rsi_prev = row["RSI_14_Prev"]
        if pd.isna(rsi) or pd.isna(rsi_prev):
            return False
        return rsi_prev > self.rsi_overbought and rsi <= self.rsi_overbought

    def _check_rsi_extreme_oversold(self, row: pd.Series) -> bool:
        """RSI en survente extrême (< 25)."""
        return row["RSI_14"] < self.rsi_extreme_low

    def _check_rsi_extreme_overbought(self, row: pd.Series) -> bool:
        """RSI en surachat extrême (> 75)."""
        return row["RSI_14"] > self.rsi_extreme_high

    def _check_rsi_bounce_up(self, row: pd.Series) -> bool:
        """RSI rebondit à la hausse (était < 40 et remonte de 3+ points)."""
        rsi = row["RSI_14"]
        rsi_prev = row["RSI_14_Prev"]
        if pd.isna(rsi) or pd.isna(rsi_prev):
            return False
        return rsi_prev < self.rsi_oversold and (rsi - rsi_prev) >= 3

    def _check_rsi_bounce_down(self, row: pd.Series) -> bool:
        """RSI rebondit à la baisse (était > 60 et redescend de 3+ points)."""
        rsi = row["RSI_14"]
        rsi_prev = row["RSI_14_Prev"]
        if pd.isna(rsi) or pd.isna(rsi_prev):
            return False
        return rsi_prev > self.rsi_overbought and (rsi_prev - rsi) >= 3

    def _check_bb_near_lower(self, row: pd.Series) -> bool:
        """Prix proche de la bande de Bollinger inférieure (dans les 10% de la bande)."""
        pct_b = row["BB_Pct_B"]
        if pd.isna(pct_b):
            return False
        return pct_b <= self.bb_near_threshold

    def _check_bb_near_upper(self, row: pd.Series) -> bool:
        """Prix proche de la bande de Bollinger supérieure (dans les 10% de la bande)."""
        pct_b = row["BB_Pct_B"]
        if pd.isna(pct_b):
            return False
        return pct_b >= (1.0 - self.bb_near_threshold)

    def _check_bb_touch_lower(self, df: pd.DataFrame, idx: int) -> bool:
        """Bougie touche ou casse la bande BB inférieure puis rejette."""
        row = df.iloc[idx]
        if pd.isna(row["BB_Lower"]):
            return False
        return row["Low"] <= row["BB_Lower"] and row["Close"] > row["BB_Lower"]

    def _check_bb_touch_upper(self, df: pd.DataFrame, idx: int) -> bool:
        """Bougie touche ou casse la bande BB supérieure puis rejette."""
        row = df.iloc[idx]
        if pd.isna(row["BB_Upper"]):
            return False
        return row["High"] >= row["BB_Upper"] and row["Close"] < row["BB_Upper"]

    def _check_ema_cross_up(self, row: pd.Series) -> bool:
        """Prix croise l'EMA à la hausse."""
        return row["EMA_Cross_Up"]

    def _check_ema_cross_down(self, row: pd.Series) -> bool:
        """Prix croise l'EMA à la baisse."""
        return row["EMA_Cross_Down"]

    # ==========================================================
    # 4 STRATÉGIES INDÉPENDANTES
    # ==========================================================

    def _strategy_a_rsi_reversal(self, row: pd.Series, df: pd.DataFrame, idx: int) -> Optional[SignalResult]:
        """
        Stratégie A - RSI Reversal :
        Le RSI sort d'une zone extrême, indiquant un retournement.

        CALL : RSI sort de la zone de survente (< 40) à la hausse
               + Tendance haussière (prix > EMA) OU proximité BB inférieure
        PUT  : RSI sort de la zone de surachat (> 60) à la baisse
               + Tendance baissière (prix < EMA) OU proximité BB supérieure
        """
        # --- CALL ---
        rsi_cross_up = self._check_rsi_oversold_cross_up(row)
        rsi_bounce_up = self._check_rsi_bounce_up(row)
        rsi_oversold = self._check_rsi_oversold(row)

        if rsi_cross_up or rsi_bounce_up or rsi_oversold:
            bullish = self._check_trend_bullish(row)
            bb_near = self._check_bb_near_lower(row) or self._check_bb_touch_lower(df, idx)

            # Au moins 1 condition confirmatoire sur 2
            if bullish or bb_near:
                reasons = ["RSI Reversal"]
                if rsi_cross_up:
                    reasons.append(f"RSI croise >{self.rsi_oversold} ({row['RSI_14_Prev']:.1f}→{row['RSI_14']:.1f})")
                elif rsi_bounce_up:
                    reasons.append(f"RSI rebond ({row['RSI_14_Prev']:.1f}→{row['RSI_14']:.1f})")
                else:
                    reasons.append(f"RSI survente ({row['RSI_14']:.1f}<{self.rsi_oversold})")
                if bullish:
                    reasons.append("Tendance haussière")
                if bb_near:
                    reasons.append("Proximité BB inférieur")

                return self._build_signal(row, df, idx, "CALL", "RSI Reversal", reasons)

        # --- PUT ---
        rsi_cross_down = self._check_rsi_overbought_cross_down(row)
        rsi_bounce_down = self._check_rsi_bounce_down(row)
        rsi_overbought = self._check_rsi_overbought(row)

        if rsi_cross_down or rsi_bounce_down or rsi_overbought:
            bearish = self._check_trend_bearish(row)
            bb_near = self._check_bb_near_upper(row) or self._check_bb_touch_upper(df, idx)

            if bearish or bb_near:
                reasons = ["RSI Reversal"]
                if rsi_cross_down:
                    reasons.append(f"RSI croise <{self.rsi_overbought} ({row['RSI_14_Prev']:.1f}→{row['RSI_14']:.1f})")
                elif rsi_bounce_down:
                    reasons.append(f"RSI retournement ({row['RSI_14_Prev']:.1f}→{row['RSI_14']:.1f})")
                else:
                    reasons.append(f"RSI surachat ({row['RSI_14']:.1f}>{self.rsi_overbought})")
                if bearish:
                    reasons.append("Tendance baissière")
                if bb_near:
                    reasons.append("Proximité BB supérieur")

                return self._build_signal(row, df, idx, "PUT", "RSI Reversal", reasons)

        return None

    def _strategy_b_bollinger_bounce(self, row: pd.Series, df: pd.DataFrame, idx: int) -> Optional[SignalResult]:
        """
        Stratégie B - Bollinger Bounce :
        Le prix touche une bande de Bollinger et rebondit.

        CALL : Rejet BB inférieure + Tendance haussière OU RSI survendu
        PUT  : Rejet BB supérieure + Tendance baissière OU RSI suracheté
        """
        # --- CALL ---
        bb_touch_lower = self._check_bb_touch_lower(df, idx)
        bb_near_lower = self._check_bb_near_lower(row)

        if bb_touch_lower or bb_near_lower:
            bullish = self._check_trend_bullish(row)
            rsi_oversold = self._check_rsi_oversold(row)

            if bullish or rsi_oversold:
                reasons = ["Bollinger Bounce"]
                if bb_touch_lower:
                    reasons.append("Rejet BB inférieur")
                else:
                    reasons.append("Proximité BB inférieur")
                if bullish:
                    reasons.append("Tendance haussière")
                if rsi_oversold:
                    reasons.append(f"RSI survente ({row['RSI_14']:.1f})")

                return self._build_signal(row, df, idx, "CALL", "Bollinger Bounce", reasons)

        # --- PUT ---
        bb_touch_upper = self._check_bb_touch_upper(df, idx)
        bb_near_upper = self._check_bb_near_upper(row)

        if bb_touch_upper or bb_near_upper:
            bearish = self._check_trend_bearish(row)
            rsi_overbought = self._check_rsi_overbought(row)

            if bearish or rsi_overbought:
                reasons = ["Bollinger Bounce"]
                if bb_touch_upper:
                    reasons.append("Rejet BB supérieur")
                else:
                    reasons.append("Proximité BB supérieur")
                if bearish:
                    reasons.append("Tendance baissière")
                if rsi_overbought:
                    reasons.append(f"RSI surachat ({row['RSI_14']:.1f})")

                return self._build_signal(row, df, idx, "PUT", "Bollinger Bounce", reasons)

        return None

    def _strategy_c_ema_crossover(self, row: pd.Series, df: pd.DataFrame, idx: int) -> Optional[SignalResult]:
        """
        Stratégie C - EMA Crossover :
        Le prix croise l'EMA, indiquant un changement de tendance.

        CALL : Prix croise l'EMA à la hausse + RSI > 40 OU proche BB inférieure
        PUT  : Prix croise l'EMA à la baisse + RSI < 60 OU proche BB supérieure
        """
        # --- CALL ---
        if self._check_ema_cross_up(row):
            rsi_ok = row["RSI_14"] > self.rsi_oversold or self._check_rsi_oversold(row)
            bb_near = self._check_bb_near_lower(row)

            if rsi_ok or bb_near:
                reasons = ["EMA Crossover", f"Prix croise EMA à la hausse"]
                if rsi_ok:
                    reasons.append(f"RSI {row['RSI_14']:.1f}")
                if bb_near:
                    reasons.append("Proximité BB inférieur")

                return self._build_signal(row, df, idx, "CALL", "EMA Crossover", reasons)

        # --- PUT ---
        if self._check_ema_cross_down(row):
            rsi_ok = row["RSI_14"] < self.rsi_overbought or self._check_rsi_overbought(row)
            bb_near = self._check_bb_near_upper(row)

            if rsi_ok or bb_near:
                reasons = ["EMA Crossover", f"Prix croise EMA à la baisse"]
                if rsi_ok:
                    reasons.append(f"RSI {row['RSI_14']:.1f}")
                if bb_near:
                    reasons.append("Proximité BB supérieur")

                return self._build_signal(row, df, idx, "PUT", "EMA Crossover", reasons)

        return None

    def _strategy_d_rsi_extreme(self, row: pd.Series, df: pd.DataFrame, idx: int) -> Optional[SignalResult]:
        """
        Stratégie D - RSI Extreme :
        Le RSI est en zone extrême, indiquant un fort potentiel de retournement.

        CALL : RSI < 25 (survente extrême) + Prix proche BB inférieure
        PUT  : RSI > 75 (surachat extrême) + Prix proche BB supérieure
        """
        # --- CALL ---
        if self._check_rsi_extreme_oversold(row):
            bb_near = self._check_bb_near_lower(row) or self._check_bb_touch_lower(df, idx)
            if bb_near:
                reasons = [
                    "RSI Extreme",
                    f"RSI très survendu ({row['RSI_14']:.1f}<{self.rsi_extreme_low})",
                    "Proximité BB inférieur",
                ]
                return self._build_signal(row, df, idx, "CALL", "RSI Extreme", reasons)

        # --- PUT ---
        if self._check_rsi_extreme_overbought(row):
            bb_near = self._check_bb_near_upper(row) or self._check_bb_touch_upper(df, idx)
            if bb_near:
                reasons = [
                    "RSI Extreme",
                    f"RSI très suracheté ({row['RSI_14']:.1f}>{self.rsi_extreme_high})",
                    "Proximité BB supérieur",
                ]
                return self._build_signal(row, df, idx, "PUT", "RSI Extreme", reasons)

        return None

    # ==========================================================
    # CONSTRUCTION DU SIGNAL
    # ==========================================================

    def _build_signal(
        self, row: pd.Series, df: pd.DataFrame, idx: int,
        direction: str, strategy: str, reasons: List[str]
    ) -> SignalResult:
        """Construit un SignalResult à partir des données."""

        if direction == "CALL":
            signal = SignalType.SIGNAL_ACHAT
        else:
            signal = SignalType.SIGNAL_VENTE

        confidence = self._calculate_confidence(signal, row, direction)
        timestamp = str(df.index[idx]) if idx < 0 else str(df.index[-1])

        details = f"✅ {direction} [{strategy}] : {' | '.join(reasons)}"
        logger.info(f"{'🟢' if direction == 'CALL' else '🔴'} {row.get('pair', '???')} : {details}")

        return SignalResult(
            pair=row.get("pair", ""),
            signal=signal,
            direction=direction,
            price=row["Close"],
            ema=row["EMA"],
            rsi=row["RSI_14"],
            rsi_prev=row["RSI_14_Prev"] if not pd.isna(row["RSI_14_Prev"]) else 0,
            bb_upper=row["BB_Upper"],
            bb_middle=row["BB_Middle"],
            bb_lower=row["BB_Lower"],
            confidence=confidence,
            timestamp=timestamp,
            details=details,
            strategy=strategy,
            reasons=reasons,
        )

    def _calculate_confidence(self, signal_type: SignalType, row: pd.Series, direction: str) -> str:
        """Évalue le niveau de confiance du signal."""
        if signal_type == SignalType.NEUTRE:
            return "—"

        score = 0

        if direction == "CALL":
            # Tendance haussière
            if row["Close"] > row["EMA"]:
                score += 1
            # RSI très bas
            if row["RSI_14"] < 30:
                score += 2
            elif row["RSI_14"] < 40:
                score += 1
            # BB %B très bas
            if not pd.isna(row["BB_Pct_B"]) and row["BB_Pct_B"] < 0.05:
                score += 2
            elif not pd.isna(row["BB_Pct_B"]) and row["BB_Pct_B"] < 0.15:
                score += 1

        elif direction == "PUT":
            # Tendance baissière
            if row["Close"] < row["EMA"]:
                score += 1
            # RSI très haut
            if row["RSI_14"] > 70:
                score += 2
            elif row["RSI_14"] > 60:
                score += 1
            # BB %B très haut
            if not pd.isna(row["BB_Pct_B"]) and row["BB_Pct_B"] > 0.95:
                score += 2
            elif not pd.isna(row["BB_Pct_B"]) and row["BB_Pct_B"] > 0.85:
                score += 1

        if score >= 4:
            return "🟢 Élevée"
        elif score >= 2:
            return "🟡 Moyenne"
        else:
            return "🟠 Faible"

    # ==========================================================
    # ANALYSE PRINCIPALE
    # ==========================================================

    def analyze(self, df: pd.DataFrame, pair: str) -> SignalResult:
        """
        Analyse les données d'une paire et génère un signal.
        Teste les 4 stratégies dans l'ordre de priorité.
        Chaque paire est analysée indépendamment.
        """
        # Ajouter les indicateurs
        df = self.add_indicators(df)

        # Ajouter le nom de la paire dans le DataFrame pour le logging
        df["pair"] = pair

        # Vérifier qu'on a assez de données
        min_required = max(self.ema_period, self.bb_period, self.rsi_period) + 3
        if len(df) < min_required:
            logger.warning(f"⚠️ {pair} : Données insuffisantes ({len(df)} < {min_required})")
            return self._neutral_result(pair, df)

        # Dernière bougie clôturée
        idx = -2 if len(df) > 2 else -1
        row = df.iloc[idx]

        # Vérifier que les indicateurs ne sont pas NaN
        if pd.isna(row["EMA"]) or pd.isna(row["RSI_14"]) or pd.isna(row["BB_Upper"]):
            logger.warning(f"⚠️ {pair} : Indicateurs non calculés (NaN)")
            return self._neutral_result(pair, df)

        # ==========================================================
        # TESTER LES 4 STRATÉGIES DANS L'ORDRE DE PRIORITÉ
        # ==========================================================

        # Stratégie D - RSI Extreme (priorité haute : signaux les plus forts)
        result = self._strategy_d_rsi_extreme(row, df, idx)
        if result is not None:
            return result

        # Stratégie A - RSI Reversal (signal de retournement)
        result = self._strategy_a_rsi_reversal(row, df, idx)
        if result is not None:
            return result

        # Stratégie B - Bollinger Bounce (signal de rebond)
        result = self._strategy_b_bollinger_bounce(row, df, idx)
        if result is not None:
            return result

        # Stratégie C - EMA Crossover (signal de tendance)
        result = self._strategy_c_ema_crossover(row, df, idx)
        if result is not None:
            return result

        # ==========================================================
        # NEUTRE - Aucune condition remplie
        # ==========================================================
        timestamp = str(df.index[idx]) if idx < 0 else str(df.index[-1])
        details = (
            f"⚪ NEUTRE : Prix={row['Close']:.5f} EMA={row['EMA']:.5f} | "
            f"RSI={row['RSI_14']:.1f} | BB%={row.get('BB_Pct_B', 0):.2f}"
        )
        logger.debug(f"⚪ {pair} : {details}")

        return SignalResult(
            pair=pair,
            signal=SignalType.NEUTRE,
            direction="NEUTRE",
            price=row["Close"],
            ema=row["EMA"],
            rsi=row["RSI_14"],
            rsi_prev=row["RSI_14_Prev"] if not pd.isna(row["RSI_14_Prev"]) else 0,
            bb_upper=row["BB_Upper"],
            bb_middle=row["BB_Middle"],
            bb_lower=row["BB_Lower"],
            confidence="—",
            timestamp=timestamp,
            details=details,
            strategy="",
            reasons=[],
        )

    def _neutral_result(self, pair: str, df: pd.DataFrame) -> SignalResult:
        """Crée un résultat neutre par défaut."""
        last_close = df["Close"].iloc[-1] if len(df) > 0 else 0.0
        return SignalResult(
            pair=pair,
            signal=SignalType.NEUTRE,
            direction="NEUTRE",
            price=last_close,
            ema=0.0,
            rsi=0.0,
            rsi_prev=0.0,
            bb_upper=0.0,
            bb_middle=0.0,
            bb_lower=0.0,
            confidence="—",
            timestamp=str(datetime.now()),
            details="Données insuffisantes",
            strategy="",
            reasons=[],
        )


# Instance globale
analyzer = TechnicalAnalyzer()
