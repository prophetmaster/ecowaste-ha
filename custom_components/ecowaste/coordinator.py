"""Coordinateur de données EcoWaste."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EcoWasteApiClient, EcoWasteAuthError, EcoWasteConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _process(items: list[dict]) -> dict:
    """Agrège les dépôts : totaux globaux, par carte, et dernier dépôt."""
    cards: dict[str, dict] = {}
    total_w = 0.0
    total_a = 0.0
    for it in items:
        weight = it.get("weight") or 0
        amount = it.get("amount") or 0
        label = (it.get("card") or {}).get("label", "?")
        card = cards.setdefault(label, {"weight": 0.0, "amount": 0.0, "count": 0})
        card["weight"] += weight
        card["amount"] += amount
        card["count"] += 1
        total_w += weight
        total_a += amount

    return {
        "count": len(items),
        "total_weight": round(total_w, 2),
        "total_amount": round(total_a, 2),
        "last": items[0] if items else None,  # l'API renvoie le plus récent en tête
        "cards": {
            label: {
                "weight": round(v["weight"], 2),
                "amount": round(v["amount"], 2),
                "count": v["count"],
            }
            for label, v in cards.items()
        },
    }


class EcoWasteCoordinator(DataUpdateCoordinator):
    """Interroge l'API WIPE à intervalle régulier."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: EcoWasteApiClient,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        try:
            items = await self.client.async_get_waste()
        except EcoWasteAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except EcoWasteConnectionError as err:
            raise UpdateFailed(str(err)) from err
        return _process(items)
