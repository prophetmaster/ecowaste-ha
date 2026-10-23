"""Client asynchrone pour l'API WIPE (EcoWaste).

Flux :
  1) POST /public/wipe/v1/authenticate  {client, card, code}  -> {access_token}
  2) GET  /wipe/v1/waste?year=AAAA   avec l'en-tête  X-Client-Token: <jwt>

Le jeton est un JWT valable ~12 h ; on le régénère automatiquement.
"""
from __future__ import annotations

import logging
from datetime import date

import aiohttp

from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)


class EcoWasteAuthError(Exception):
    """Identifiants refusés par le portail."""


class EcoWasteConnectionError(Exception):
    """Portail injoignable ou réponse invalide."""


class EcoWasteApiClient:
    """Petit client pour l'API client WIPE d'une commune."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        client: str,
        card: str,
        code: str,
    ) -> None:
        self._session = session
        self._client = client
        self._card = card
        self._code = code
        self._token: str | None = None

    async def authenticate(self) -> str:
        """Récupère un nouveau jeton et le mémorise."""
        payload = {"client": self._client, "card": self._card, "code": self._code}
        try:
            async with self._session.post(
                f"{BASE_URL}/public/wipe/v1/authenticate", json=payload
            ) as resp:
                if resp.status in (400, 401, 403):
                    raise EcoWasteAuthError(f"Auth refusée (HTTP {resp.status})")
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise EcoWasteConnectionError(str(err)) from err

        token = data.get("access_token")
        if not token:
            raise EcoWasteAuthError("Réponse sans access_token")
        self._token = token
        return token

    async def async_get_waste(self, year: int | None = None) -> list[dict]:
        """Retourne la liste des dépôts de l'année (la plus récente en tête)."""
        if year is None:
            year = date.today().year
        if not self._token:
            await self.authenticate()
        try:
            return await self._get_waste(year, retry=True)
        except aiohttp.ClientError as err:
            raise EcoWasteConnectionError(str(err)) from err

    async def _get_waste(self, year: int, retry: bool) -> list[dict]:
        headers = {"X-Client-Token": self._token, "Accept": "application/json"}
        async with self._session.get(
            f"{BASE_URL}/wipe/v1/waste", params={"year": year}, headers=headers
        ) as resp:
            if resp.status == 401 and retry:
                # Jeton expiré -> on ré-authentifie une seule fois.
                await self.authenticate()
                return await self._get_waste(year, retry=False)
            if resp.status == 401:
                raise EcoWasteAuthError("Jeton refusé (401)")
            resp.raise_for_status()
            return await resp.json()


async def async_fetch_clients(session: aiohttp.ClientSession) -> list[dict]:
    """Liste publique des communes/clients du portail.

    Utilisée par le config flow pour remplir le menu déroulant avec les vrais
    `identifier`. Endpoint public (pas d'authentification).
    """
    async with session.get(
        f"{BASE_URL}/public/api/clients",
        headers={"Accept": "application/json"},
        timeout=aiohttp.ClientTimeout(total=20),
    ) as resp:
        resp.raise_for_status()
        return await resp.json()
