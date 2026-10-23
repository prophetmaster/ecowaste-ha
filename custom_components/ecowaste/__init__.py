"""Intégration EcoWaste (WIPE) pour Home Assistant."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EcoWasteApiClient
from .const import CONF_CARD, CONF_CLIENT, CONF_CODE, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import EcoWasteCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure une entrée (une commune/carte)."""
    session = async_get_clientsession(hass)
    client = EcoWasteApiClient(
        session,
        entry.data[CONF_CLIENT],
        entry.data[CONF_CARD],
        entry.data[CONF_CODE],
    )
    coordinator = EcoWasteCoordinator(
        hass, client, timedelta(seconds=DEFAULT_SCAN_INTERVAL)
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une entrée."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
