import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN, 
    CONF_API_URL, 
    CONF_API_TOKEN, 
    SERVICE_SCAN_ITEM,
    SERVICE_UPDATE_STOCK,
    SERVICE_REFRESH_DATA,
    ACTION_ADD,
    ACTION_REMOVE
)
from .api import SpeisekammerAPI, SpeisekammerAPIError

_LOGGER = logging.getLogger(__name__)

# Dienst-Schema für SCAN_ITEM
SCAN_ITEM_SCHEMA = vol.Schema({
    vol.Required("barcode"): cv.string,
    vol.Required("action"): vol.In([ACTION_ADD, ACTION_REMOVE]),
    vol.Required("storage_id"): cv.positive_int,
    vol.Optional("quantity", default=1): cv.positive_int,
    vol.Optional("mhd_date"): cv.date, # Home Assistant's Datum-Validierung
})

# Dienst-Schema für REFRESH_DATA (einfach)
REFRESH_DATA_SCHEMA = vol.Schema({})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Richtet die Speisekammer API Integration von einem Konfigurationseintrag ein."""
    
    # 1. Daten aus dem Konfigurationseintrag abrufen
    config = entry.data
    options = entry.options
    
    api_url = config[CONF_API_URL]
    api_token = config[CONF_API_TOKEN]
    community_id = options.get("community_id")

    # 2. API-Instanz erstellen
    api = SpeisekammerAPI(hass, api_url, api_token)
    api.community_id = community_id # Community ID aus Optionen setzen
    
    # Speichern der API-Instanz im Home Assistant Datenobjekt
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api

    # 3. Initialdaten abrufen (Lagerorte) und die Services registrieren
    await _async_register_services(hass, entry)
    
    # Führt den ersten Abruf der Lagerorte aus, um die Datenstruktur zu füllen
    # Dies geschieht asynchron nach dem Start, um den Start nicht zu blockieren.
    hass.async_create_task(api.async_fetch_initial_data())

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entlädt den Konfigurationseintrag."""
    # Entfernt alle registrierten Dienste, falls die Integration entladen wird
    hass.services.async_remove(DOMAIN, SERVICE_SCAN_ITEM)
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_DATA)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


async def _async_register_services(hass: HomeAssistant, entry: ConfigEntry):
    """Registriert alle Dienste für die Integration."""
    
    api: SpeisekammerAPI = hass.data[DOMAIN][entry.entry_id]

    @callback
    async def handle_scan_item(call: ServiceCall):
        """Service zum Scannen und Hinzufügen/Entfernen von Artikeln."""
        barcode = call.data["barcode"]
        action = call.data["action"]
        storage_id = call.data["storage_id"]
        quantity = call.data.get("quantity", 1)
        mhd_date = call.data.get("mhd_date")
        
        # Konvertiert das Datum-Objekt (falls vorhanden) in einen API-String (YYYY-MM-DD)
        mhd_date_str = mhd_date.isoformat() if mhd_date else None

        try:
            await api.async_update_stock(
                storage_id=storage_id,
                barcode=barcode,
                action=action,
                quantity=quantity,
                mhd_date=mhd_date_str
            )
        except SpeisekammerAPIError as err:
            _LOGGER.error("Service-Fehler (scan_item): %s", err)
            hass.components.persistent_notification.async_create(
                f"Speisekammer Scan-Fehler: {err}",
                title="Speisekammer API Fehler"
            )

    @callback
    async def handle_refresh_data(call: ServiceCall):
        """Service zum Neuladen der Communities und Lagerorte."""
        try:
            await api.async_fetch_initial_data()
            _LOGGER.info("Lagerort-Daten erfolgreich aktualisiert.")
        except SpeisekammerAPIError as err:
            _LOGGER.error("Service-Fehler (refresh_data): %s", err)
            hass.components.persistent_notification.async_create(
                f"Speisekammer Aktualisierungs-Fehler: {err}",
                title="Speisekammer API Fehler"
            )

    # Dienste bei Home Assistant registrieren
    hass.services.async_register(
        DOMAIN, SERVICE_SCAN_ITEM, handle_scan_item, schema=SCAN_ITEM_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH_DATA, handle_refresh_data, schema=REFRESH_DATA_SCHEMA
    )
