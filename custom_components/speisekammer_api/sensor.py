"""Sensor-Plattform für die Speisekammer API Integration."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import DiscoveryInfoType

from .const import DOMAIN, SERVICE_REFRESH_DATA
from .api import SpeisekammerAPI 

_LOGGER = logging.getLogger(__name__)

# Die setup-Funktion wird von __init__.py aufgerufen
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Richtet die Speisekammer Sensoren über einen Konfigurationseintrag ein."""
    api: SpeisekammerAPI = hass.data[DOMAIN][entry.entry_id]

    # Fügt den Sensor hinzu, der die Lagerorte als Attribute anzeigt
    async_add_entities([SpeisekammerStorageCountSensor(api, entry)], True)


class SpeisekammerStorageCountSensor(SensorEntity):
    """Sensor zur Anzeige der Anzahl der konfigurierten Lagerorte und ihrer IDs."""

    def __init__(self, api: SpeisekammerAPI, entry: ConfigEntry):
        """Initialisiert den Sensor."""
        self._api = api
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_storage_count"
        self._attr_name = "Speisekammer Lagerorte Übersicht"
        self._attr_icon = "mdi:warehouse"
        
        # Registriert einen Listener, der diesen Sensor aktualisiert, wenn der 
        # REFRESH_DATA Service aufgerufen wird.
        entry.async_on_unload(
            self._api.hass.bus.async_listen(
                f"call_service/{DOMAIN}/{SERVICE_REFRESH_DATA}", self._handle_refresh_event
            )
        )

    # Wird aufgerufen, wenn der Service speisekammer_api.refresh_data ausgeführt wird
    async def _handle_refresh_event(self, event):
        """Behandelt das Service-Ereignis zur Aktualisierung der Entität."""
        self.async_schedule_update_ha_state(True)
        
    @property
    def native_value(self):
        """Gibt die aktuelle Anzahl der Lagerorte zurück."""
        # Zeigt die Anzahl als Hauptwert an
        return len(self._api.storage_locations)
    
    @property
    def unit_of_measurement(self):
        """Einheit des Zustands."""
        return "Lagerorte"

    @property
    def extra_state_attributes(self):
        """Gibt die Liste der Lagerorte als Attribute zurück (ID: Name)."""
        # Dies ist der entscheidende Teil, um die IDs und Namen sichtbar zu machen
        return {"storage_locations": self._api.storage_locations}
    
    @property
    def should_poll(self) -> bool:
        """Der Sensor wird manuell durch den Service-Aufruf aktualisiert."""
        return False
        
    async def async_update(self):
        """Stellt sicher, dass die Attribute aktualisiert werden."""
        # Der Wert wird direkt aus der API-Klasse gelesen, die durch den Service 
        # (oder den Initialisierungsprozess) aktualisiert wurde.
        pass
