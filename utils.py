"""
=============================================================
UTILITAIRES — FONCTIONS AUXILIAIRES
=============================================================
Fonctions d'aide pour le bot : formatage, conversions, etc.
=============================================================
"""

from datetime import datetime
from typing import Optional


def format_price(price: float, pair: str) -> str:
    """Formate un prix selon la paire (5 décimales pour Forex majeur)."""
    return f"{price:.5f}"


def format_timestamp(dt: datetime) -> str:
    """Formate un timestamp pour l'affichage."""
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def get_market_status() -> str:
    """Retourne le statut actuel du marché Forex."""
    now = datetime.utcnow()
    day = now.weekday()  # 0=Lundi, 6=Dimanche
    hour = now.hour

    # Le Forex est ouvert du dimanche soir au vendredi soir (UTC)
    if day == 6:  # Dimanche
        return "🟡 Ouverture" if hour >= 22 else "🔴 Fermé"
    elif day == 5:  # Samedi
        return "🔴 Fermé"
    elif day == 4 and hour >= 22:  # Vendredi soir
        return "🔴 Fermé"
    else:
        return "🟢 Ouvert"


def calculate_pips(entry: float, current: float, pair: str) -> float:
    """Calcule la différence en pips entre deux prix."""
    # Paires JPY : 2 décimales → 1 pip = 0.01
    # Autres paires : 4 décimales → 1 pip = 0.0001
    if "JPY" in pair:
        return round((current - entry) * 100, 1)
    else:
        return round((current - entry) * 10000, 1)


def get_pip_value(pair: str) -> float:
    """Retourne la valeur d'un pip selon la paire."""
    if "JPY" in pair:
        return 0.01
    else:
        return 0.0001
