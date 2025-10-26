import aiohttp
import logging

from homeassistant.exceptions import HomeAssistantError
from aiohttp import ClientConnectorError, ClientError

from .const import (
    API_PATH_COMMUNITIES,
    API_PATH_STORAGE_LOCATIONS,
    API_PATH_STOCK,
    STATUS_ADD,
    STATUS_REMOVE,
    DOMAIN, 
    SERVICE_REFRESH_DATA
)

_LOGGER = logging.getLogger(__name__)

# ==================================================================================
# API-KLASSE
# ==================================================================================

class SpeisekammerAPI:
    """Kapselt die Kommunikation mit der Speisekammer API (Smantry)."""

    def __init__(self, hass, api_url, api_token):
        """Initialisiert die API-Klasse."""
        self.hass = hass
        self.api_url = api_url.rstrip('/') 
        self.api_token = api_token
        self.community_id = None
        self.storage_locations = {}

    async def async_request(self, method, path, data=None):
        """Führt eine asynchrone HTTP-Anfrage aus und behandelt Fehler."""
        url = f"{self.api_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.request(
                    method, url, headers=headers, json=data, timeout=15
                )
                
                # Prüft auf 4xx/5xx HTTP-Statuscodes
                response.raise_for_status() 
                
                # Gibt die JSON-Antwort zurück
                return await response.json()
            
            except ClientConnectorError as err:
                # Fängt spezifische Verbindungsfehler (DNS, Host nicht gefunden, SSL) ab
                _LOGGER.error("API-Verbindungsfehler (DNS/Host/Timeout) für %s: %s", url, err)
                raise SpeisekammerAPIError(
                    f"Verbindungsfehler zum Host. Prüfen Sie die API-URL (Protokoll/Domain) oder die Netzwerk-/DNS-Einstellungen: {err}"
                ) from err
            
            except ClientError as err:
                # Fängt andere allgemeine Client-Fehler ab (z.B. ungültige Antwort)
                _LOGGER.error("API-Anfrage fehlgeschlagen für %s: %s", url, err)
                raise SpeisekammerAPIError(f"Allgemeiner Verbindungsfehler: {err}") from err
            
            except aiohttp.ContentTypeError:
                 # Fängt Fehler ab, wenn die Antwort kein gültiges JSON ist (z.B. HTML-Fehlerseite)
                _LOGGER.error("API-Antwort ist kein gültiges JSON von %s", url)
                raise SpeisekammerAPIError("Ungültige JSON-Antwort von der API.")
            
            except Exception as err:
                _LOGGER.error("Unerwarteter Fehler bei der API-Anfrage: %s", err)
                raise SpeisekammerAPIError(f"Unerwarteter Fehler: {err}") from err


    async def async_fetch_initial_data(self):
        """Ruft die Community ID und die Lagerorte ab (Validierung der Konfiguration)."""
        
        # 1. Community ID abrufen (GET /communities)
        _LOGGER.debug("Starte Abruf der Community ID.")
        data = await self.async_request("GET", API_PATH_COMMUNITIES)
        
        if not data or not data[0].get('id'):
            raise SpeisekammerAPIError("Community ID konnte nicht ermittelt werden. Prüfen Sie den API-Token.")

        self.community_id = data[0]['id']
        _LOGGER.info("Community ID ermittelt: %s", self.community_id)

        # 2. Lagerorte abrufen (GET /communities/{id}/storage-locations)
        path = API_PATH_STORAGE_LOCATIONS.format(community_id=self.community_id)
        data = await self.async_request("GET", path)

        if not data:
             _LOGGER.warning("Keine Lagerorte für Community %s gefunden.", self.community_id)
             self.storage_locations = {}
             return

        # Lagerorte im Format {id: name} speichern
        self.storage_locations = {item['id']: item['name'] for item in data}
        _LOGGER.debug("Lagerorte geladen: %s", self.storage_locations)
        
        # Benachrichtigt alle Listener (z.B. den Sensor) über die erfolgreiche Aktualisierung
        self.hass.bus.async_fire(f"call_service/{DOMAIN}/{SERVICE_REFRESH_DATA}")


    async def async_update_stock(self, storage_id, barcode, action, quantity, mhd_date=None):
        """Führt PUT /stock aus (Erfassung (1) oder Ausgabe (2))."""
        
        status = STATUS_ADD if action == "add" else STATUS_REMOVE
        
        if storage_id not in self.storage_locations:
            raise SpeisekammerAPIError(f"Lagerort ID {storage_id} unbekannt. Aktualisieren Sie die Daten über den Service '{DOMAIN}.{SERVICE_REFRESH_DATA}'.")

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
        result = await self.async_request("PUT", path, data=payload)
        
        _LOGGER.info("Bestand-Update erfolgreich: %s", result)
        return result


# ==================================================================================
# FEHLERKLASSEN
# ==================================================================================

class SpeisekammerAPIError(HomeAssistantError):
    """Generischer Fehler für die Speisekammer API Integration."""
    pass
