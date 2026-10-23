"""Constantes de l'intégration EcoWaste (WIPE)."""
from __future__ import annotations

DOMAIN = "ecowaste"

CONF_CLIENT = "client"
CONF_CARD = "card"
CONF_CODE = "code"

# Base de l'API publique WIPE (éditeur : OptiWaste SA)
BASE_URL = "https://wipe.ecowaste.ch/ipServer/wise"

# Intervalle de rafraîchissement par défaut (secondes). 6 h = 4 relèves/jour.
DEFAULT_SCAN_INTERVAL = 21600
