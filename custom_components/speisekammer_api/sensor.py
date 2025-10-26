"""Sensor-Plattform für die Speisekammer API Integration."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .api import SpeisekammerAPI # Die API-Klasse

_LOGGER = logging.getLogger(__name__)

# Diese Funktion wird beim Laden der Sensor-Plattform aufgerufen
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Richtet die Speisekammer Sensoren über einen Konfigurationseintrag ein."""
    api: SpeisekammerAPI = hass.data[DOMAIN][entry.entry_id]

    sensors = []
    
    # Fügt eine Entität hinzu, die die Anzahl der geladenen Lagerorte anzeigt
    sensors.append(SpeisekammerStorageCountSensor(api, entry))
    
    # ACHTUNG: Die Anzeige des gesamten Bestands erfordert einen 
    # separaten API-Aufruf (GET /stock/{community}/{storage}) und eine 
    # Coordinator-Klasse zur regelmäßigen Aktualisierung. 
    # Dies ist komplexer und muss separat implementiert werden.

    async_add_entities(sensors, True)

# Sensor für die Anzahl der Lagerorte (einfaches Beispiel)
class SpeisekammerStorageCountSensor(SensorEntity):
    """Sensor zur Anzeige der Anzahl der konfigurierten Lagerorte."""

    def __init__(self, api: SpeisekammerAPI, entry: ConfigEntry):
        """Initialisiert den Sensor."""
        self._api = api
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_storage_count"
        self._attr_name = "Speisekammer Lagerorte (Anzahl)"
        self._attr_icon = "mdi:warehouse"

    @property
    def native_value(self):
        """Gibt die aktuelle Anzahl der Lagerorte zurück."""
        return len(self._api.storage_locations)

    @property
    def extra_state_attributes(self):
        """Gibt die Liste der Lagerorte als Attribute zurück (ID: Name)."""
        return {"Lagerorte": self._api.storage_locations}
    
    @property
    def should_poll(self) -> bool:
        """Der Sensor wird manuell über den Refresh-Service aktualisiert."""
        return False
        
    async def async_update(self):
        """Aktualisiert den Sensor manuell durch API-Aufruf."""
        # Da wir bereits einen Service zum Neuladen haben, können wir diesen hier
        # aufrufen, um die Attribute zu aktualisieren.
        await self._api.async_fetch_initial_data()
