import aiohttp
import logging

from homeassistant.exceptions import HomeAssistantError

from .const import (
    API_PATH_COMMUNITIES,
    API_PATH_STORAGE_LOCATIONS,
    API_PATH_STOCK,
    STATUS_ADD,
    STATUS_REMOVE,
)

_LOGGER = logging.getLogger(__name__)

class SpeisekammerAPI:
    """Kapselt die Kommunikation mit der Speisekammer API."""

    def __init__(self, hass, api_url, api_token):
        """Initialisiert die API-Klasse."""
        self.hass = hass
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.community_id = None
        self.storage_locations = {}

    async def async_request(self, method, path, data=None):
        """Führt eine asynchrone HTTP-Anfrage aus."""
        url = f"{self.api_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.request(
                    method, url, headers=headers, json=data, timeout=10
                )
                response.raise_for_status() # Löst HTTPError für 4xx/5xx Fehler aus
                return await response.json()
            except aiohttp.ClientError as err:
                _LOGGER.error("API-Anfrage fehlgeschlagen für %s: %s", url, err)
                raise SpeisekammerAPIError(f"Verbindungsfehler: {err}") from err
            except Exception as err:
                _LOGGER.error("Unerwarteter Fehler bei der API-Anfrage: %s", err)
                raise SpeisekammerAPIError(f"Unerwarteter Fehler: {err}") from err


    async def async_fetch_initial_data(self):
        """Ruft die Community ID und die Lagerorte ab."""
        # 1. Community ID abrufen (GET /communities)
        _LOGGER.debug("Starte Abruf der Community ID.")
        data = await self.async_request("GET", API_PATH_COMMUNITIES)
        
        if not data or not data[0].get('id'):
            raise SpeisekammerAPIError("Community ID konnte nicht ermittelt werden.")

        self.community_id = data[0]['id']
        _LOGGER.info("Community ID ermittelt: %s", self.community_id)

        # 2. Lagerorte abrufen (GET /communities/{id}/storage-locations)
        path = API_PATH_STORAGE_LOCATIONS.format(community_id=self.community_id)
        data = await self.async_request("GET", path)

        if not data:
             _LOGGER.warning("Keine Lagerorte für Community %s gefunden.", self.community_id)
             return

        # Lagerorte im Format {id: name} speichern
        self.storage_locations = {item['id']: item['name'] for item in data}
        _LOGGER.debug("Lagerorte geladen: %s", self.storage_locations)


    async def async_update_stock(self, storage_id, barcode, action, quantity, mhd_date=None):
        """Führt PUT /stock aus (Erfassung oder Ausgabe)."""
        
        # Mapping der Action auf den API-Status-Code
        status = STATUS_ADD if action == "add" else STATUS_REMOVE
        
        if storage_id not in self.storage_locations:
            raise SpeisekammerAPIError(f"Lagerort ID {storage_id} unbekannt.")

        payload = {
            "status": status,
            "community": self.community_id,
            "storage": storage_id,
            "barcode": barcode,
            "mhd": mhd_date,
            "count": quantity 
        }

        _LOGGER.debug("Sende Bestand-Update Payload: %s", payload)

        path = API_PATH_STOCK
        # PUT Request ausführen (erzeugt den Eintrag oder aktualisiert ihn)
        result = await self.async_request("PUT", path, data=payload)
        
        _LOGGER.info("Bestand-Update erfolgreich: %s", result)
        return result


class SpeisekammerAPIError(HomeAssistantError):
    """Generischer Fehler für die Speisekammer API Integration."""
    pass
