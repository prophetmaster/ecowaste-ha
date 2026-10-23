"""Écran de configuration (UI) de l'intégration EcoWaste."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EcoWasteApiClient, EcoWasteAuthError, EcoWasteConnectionError
from .const import CONF_CARD, CONF_CLIENT, CONF_CODE, DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT): str,
        vol.Required(CONF_CARD): str,
        vol.Required(CONF_CODE): str,
    }
)


class EcoWasteConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gère l'ajout d'une commune/carte via l'interface."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            client = user_input[CONF_CLIENT].strip()
            card = user_input[CONF_CARD].strip()
            code = user_input[CONF_CODE].strip()

            session = async_get_clientsession(self.hass)
            api = EcoWasteApiClient(session, client, card, code)
            try:
                await api.authenticate()
            except EcoWasteAuthError:
                errors["base"] = "invalid_auth"
            except EcoWasteConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{client}_{card}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"EcoWaste {client} ({card})",
                    data={CONF_CLIENT: client, CONF_CARD: card, CONF_CODE: code},
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
