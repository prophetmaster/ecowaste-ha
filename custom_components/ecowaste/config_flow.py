"""Écran de configuration (UI) de l'intégration EcoWaste."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import (
    EcoWasteApiClient,
    EcoWasteAuthError,
    EcoWasteConnectionError,
    async_fetch_clients,
)
from .communes import COMMUNES
from .const import CONF_CARD, CONF_CLIENT, CONF_CODE, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _fallback_options() -> list[SelectOptionDict]:
    """Options issues de la liste figée (repli hors ligne)."""
    return [
        SelectOptionDict(value=slug, label=name)
        for slug, name in sorted(COMMUNES.items(), key=lambda kv: kv[1].lower())
    ]


class EcoWasteConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gère l'ajout d'une commune/carte via l'interface."""

    VERSION = 1

    async def _commune_options(self) -> list[SelectOptionDict]:
        """Communes chargées EN DIRECT depuis le portail, sinon liste figée."""
        session = async_get_clientsession(self.hass)
        try:
            clients = await async_fetch_clients(session)
            options = [
                SelectOptionDict(
                    value=c["identifier"],
                    label=c.get("shortName") or c.get("name") or c["identifier"],
                )
                for c in clients
                if c.get("identifier") and c.get("status", "ACTIVE") == "ACTIVE"
            ]
            if options:
                return sorted(options, key=lambda o: o["label"].lower())
        except Exception:  # noqa: BLE001
            _LOGGER.debug(
                "Liste des communes en direct indisponible, repli sur la liste figée",
                exc_info=True,
            )
        return _fallback_options()

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

        schema = vol.Schema(
            {
                vol.Required(CONF_CLIENT): SelectSelector(
                    SelectSelectorConfig(
                        options=await self._commune_options(),
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                        sort=True,
                    )
                ),
                vol.Required(CONF_CARD): str,
                vol.Required(CONF_CODE): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
