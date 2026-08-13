"""
=============================================================
SCRIPT DE TEST — MODULE D'ANALYSE TECHNIQUE
=============================================================
Teste le moteur d'analyse avec des données de marché réelles
pour vérifier le bon fonctionnement des indicateurs et de la
logique de signaux.

Usage :
  python test_analysis.py
=============================================================
"""

import sys
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from config import config
from market_data import market_fetcher
from analysis import analyzer, SignalType

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)

logger = logging.getLogger("TestAnalysis")


def test_with_real_data():
    """Test avec des données de marché réelles."""
    print("=" * 60)
    print("📊 TEST D'ANALYSE TECHNIQUE — DONNÉES RÉELLES")
    print("=" * 60)

    # Récupérer les données
    pair = "EURUSD=X"
    print(f"\n📥 Récupération des données pour {pair}...")

    df = market_fetcher.fetch(pair)
    if df is None or df.empty:
        print(f"❌ Impossible de récupérer les données pour {pair}")
        return False

    print(f"✅ {len(df)} bougies récupérées")
    print(f"   Période : {df.index[0]} → {df.index[-1]}")
    print(f"\n   Dernières 5 bougies :")
    print(df.tail(5).to_string())

    # Analyser les données
    print(f"\n🔍 Analyse technique en cours...")
    result = analyzer.analyze(df, pair)

    print(f"\n📋 RÉSULTAT DE L'ANALYSE :")
    print(f"  Paire : {config.get_display_pair(result.pair)}")
    print(f"  Signal : {result.signal.value}")
    print(f"  Direction : {result.direction}")
    print(f"  Prix : {result.price:.5f}")
    print(f"  EMA 50 : {result.ema50:.5f}")
    print(f"  RSI 14 : {result.rsi:.2f}")
    print(f"  RSI 14 (précédent) : {result.rsi_prev:.2f}")
    print(f"  BB Supérieure : {result.bb_upper:.5f}")
    print(f"  BB Moyenne : {result.bb_middle:.5f}")
    print(f"  BB Inférieure : {result.bb_lower:.5f}")
    print(f"  Confiance : {result.confidence}")
    print(f"  Détails : {result.details}")

    return True


def test_with_simulated_data():
    """Test avec des données simulées pour vérifier chaque condition."""
    print("\n" + "=" * 60)
    print("🧪 TEST D'ANALYSE — DONNÉES SIMULÉES")
    print("=" * 60)

    # Créer un scénario de signal CALL (achat)
    print("\n🟢 Test scénario CALL (achat)...")
    dates = pd.date_range(end=datetime.now(), periods=120, freq="5min")

    # Tendance haussière avec pullback (pour EMA50 > prix puis rebond)
    np.random.seed(42)
    base = np.linspace(1.0800, 1.0900, 120)  # Tendance haussière
    noise = np.random.normal(0, 0.0005, 120)
    close_prices = base + noise

    # Forcer les dernières bougies pour simuler le signal
    # RSI oversold cross : on a besoin d'une baisse récente suivie d'un rebond
    close_prices[-5:] = [1.0860, 1.0845, 1.0830, 1.0845, 1.0865]

    df_call = pd.DataFrame(
        {
            "Open": close_prices - 0.0002,
            "High": close_prices + 0.0008,
            "Low": close_prices - 0.0008,
            "Close": close_prices,
            "Volume": np.random.randint(100, 1000, 120),
        },
        index=dates,
    )

    # Ajuster les 2 dernières bougies pour le signal
    # Dernière bougie : Low casse la BB inférieure, Close au-dessus (rejet)
    df_call.iloc[-2, df_call.columns.get_loc("Low")] = df_call.iloc[-2]["Close"] - 0.003
    df_call.iloc[-2, df_call.columns.get_loc("Close")] = df_call.iloc[-2]["Open"] + 0.001

    result_call = analyzer.analyze(df_call, "EURUSD=X")
    print(f"  Signal : {result_call.signal.value}")
    print(f"  Direction : {result_call.direction}")
    print(f"  Détails : {result_call.details}")

    # Créer un scénario de signal PUT (vente)
    print("\n🔴 Test scénario PUT (vente)...")
    base_put = np.linspace(1.0900, 1.0800, 120)  # Tendance baissière
    close_put = base_put + np.random.normal(0, 0.0005, 120)

    # Forcer les dernières bougies
    close_put[-5:] = [1.0840, 1.0855, 1.0870, 1.0855, 1.0835]

    df_put = pd.DataFrame(
        {
            "Open": close_put + 0.0002,
            "High": close_put + 0.0008,
            "Low": close_put - 0.0008,
            "Close": close_put,
            "Volume": np.random.randint(100, 1000, 120),
        },
        index=dates,
    )

    # Ajuster pour le signal PUT
    df_put.iloc[-2, df_put.columns.get_loc("High")] = df_put.iloc[-2]["Close"] + 0.003
    df_put.iloc[-2, df_put.columns.get_loc("Close")] = df_put.iloc[-2]["Open"] - 0.001

    result_put = analyzer.analyze(df_put, "GBPUSD=X")
    print(f"  Signal : {result_put.signal.value}")
    print(f"  Direction : {result_put.direction}")
    print(f"  Détails : {result_put.details}")

    # Test scénario neutre
    print("\n⚪ Test scénario NEUTRE...")
    base_neutral = np.ones(120) * 1.0850 + np.random.normal(0, 0.0003, 120)
    df_neutral = pd.DataFrame(
        {
            "Open": base_neutral - 0.0001,
            "High": base_neutral + 0.0003,
            "Low": base_neutral - 0.0003,
            "Close": base_neutral,
            "Volume": np.random.randint(100, 1000, 120),
        },
        index=dates,
    )

    result_neutral = analyzer.analyze(df_neutral, "AUDJPY=X")
    print(f"  Signal : {result_neutral.signal.value}")
    print(f"  Direction : {result_neutral.direction}")
    print(f"  Détails : {result_neutral.details}")

    return True


def test_indicators():
    """Test individuel de chaque indicateur."""
    print("\n" + "=" * 60)
    print("📈 TEST DES INDICATEURS TECHNIQUES")
    print("=" * 60)

    # Créer des données de test
    dates = pd.date_range(end=datetime.now(), periods=100, freq="5min")
    np.random.seed(123)
    prices = np.cumsum(np.random.normal(0, 0.001, 100)) + 1.0800

    df = pd.DataFrame(
        {
            "Open": prices - 0.0002,
            "High": prices + 0.0005,
            "Low": prices - 0.0005,
            "Close": prices,
            "Volume": np.random.randint(100, 500, 100),
        },
        index=dates,
    )

    # Ajouter les indicateurs
    df = analyzer.add_indicators(df)

    print(f"\n📊 Dernières valeurs des indicateurs :")
    last = df.iloc[-1]
    print(f"  Close : {last['Close']:.5f}")
    print(f"  EMA 50 : {last['EMA_50']:.5f}")
    print(f"  RSI 14 : {last['RSI_14']:.2f}")
    print(f"  RSI 14 (précédent) : {df.iloc[-2]['RSI_14']:.2f}")
    print(f"  BB Supérieure : {last['BB_Upper']:.5f}")
    print(f"  BB Moyenne : {last['BB_Middle']:.5f}")
    print(f"  BB Inférieure : {last['BB_Lower']:.5f}")
    print(f"  BB %B : {last['BB_Pct_B']:.4f}")

    # Vérifier les plages
    print(f"\n✅ Vérifications :")
    print(f"  RSI dans [0, 100] : {0 <= last['RSI_14'] <= 100}")
    print(f"  BB Lower < BB Middle : {last['BB_Lower'] < last['BB_Middle']}")
    print(f"  BB Middle < BB Upper : {last['BB_Middle'] < last['BB_Upper']}")

    return True


def main():
    """Exécute tous les tests d'analyse."""
    print("🧪 SUITE DE TESTS D'ANALYSE TECHNIQUE")
    print("=" * 60)

    # Test 1 : Indicateurs
    print("\n[1/3] Test des indicateurs...")
    test_indicators()

    # Test 2 : Données simulées
    print("\n[2/3] Test avec données simulées...")
    test_with_simulated_data()

    # Test 3 : Données réelles
    print("\n[3/3] Test avec données réelles...")
    try:
        test_with_real_data()
    except Exception as e:
        print(f"⚠️ Test avec données réelles échoué (connexion ?) : {e}")
        print("   Ce test nécessite une connexion internet et yfinance installé.")

    print("\n" + "=" * 60)
    print("🎉 TESTS D'ANALYSE TERMINÉS")
    print("=" * 60)


if __name__ == "__main__":
    main()
