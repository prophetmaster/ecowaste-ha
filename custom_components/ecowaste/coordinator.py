"""Coordinateur de données EcoWaste."""
from __future__ import annotations

import logging
from datetime import date, timedelta

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
    month_prefix = date.today().strftime("%Y-%m")
    month_w = 0.0
    month_a = 0.0
    month_c = 0
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
        if (it.get("timestamp") or "")[:7] == month_prefix:
            month_w += weight
            month_a += amount
            month_c += 1

    count = len(items)
    return {
        "count": count,
        "total_weight": round(total_w, 2),
        "total_amount": round(total_a, 2),
        "avg_weight": round(total_w / count, 2) if count else None,
        "avg_amount": round(total_a / count, 2) if count else None,
        "price_per_kg": round(total_a / total_w, 3) if total_w else None,
        "month_weight": round(month_w, 2),
        "month_amount": round(month_a, 2),
        "month_count": month_c,
        "last": items[0] if items else None,  # l'API renvoie le plus récent en tête
        "last_timestamp": items[0].get("timestamp") if items else None,
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
