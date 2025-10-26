import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_URL, CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult

# Wichtiger Import für die Standard-URL
from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, DEFAULT_API_URL
from .api import SpeisekammerAPI, SpeisekammerAPIError

_LOGGER = logging.getLogger(__name__)


# Schema für die Eingabemaske
# 1. CONF_API_URL ist jetzt optional mit dem vordefinierten Standardwert.
# 2. CONF_API_TOKEN ist weiterhin zwingend erforderlich.
DATA_SCHEMA = vol.Schema({
    vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
    vol.Required(CONF_API_TOKEN): str,
})

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validiert die Benutzer-Eingabe und testet die Verbindung zur API."""
    
    # Stellen Sie sicher, dass die URL mit https:// beginnt, da sie nur den Hostnamen liefern kann
    api_url = data[CONF_API_URL]
    if not api_url.startswith("http"):
         api_url = f"https://{api_url}"
    
    api = SpeisekammerAPI(hass, api_url, data[CONF_API_TOKEN])
    
    try:
        # Versucht, Community ID und Lagerorte abzurufen (Test der Verbindung)
        await api.async_fetch_initial_data()
    except SpeisekammerAPIError as err:
        # Fängt spezifische API-Fehler (DNS, Auth etc.) ab
        _LOGGER.error("Validierung fehlgeschlagen: %s", err)
        raise SpeisekammerConnectionError(f"Verbindungsfehler: {err}") from err

    # Rückgabe, wenn die Validierung erfolgreich war
    return {"title": "Speisekammer API", "community_id": api.community_id}


class SpeisekammerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Konfigurationsfluss für die Speisekammer API."""

    VERSION = 1
    # Erlaubt nur eine Instanz der Integration
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL 

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Behandelt den initialen Schritt des Konfigurationsflusses."""
        errors = {}

        if user_input is not None:
            # Überprüfen, ob diese Konfiguration bereits existiert
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except SpeisekammerConnectionError as err:
                # Zeigt spezifischen Fehler aus der Validierungsfunktion an
                errors["base"] = str(err)
                _LOGGER.error("Verbindungsfehler während des Config Flows: %s", err)
            except Exception: # Alle anderen unvorhergesehenen Fehler
                errors["base"] = "Unbekannter Fehler während der Einrichtung."
            else:
                # Erfolgreich: Erzeugt den Konfigurationseintrag
                return self.async_create_entry(
                    title=info["title"], 
                    data=user_input,
                    options={"community_id": info["community_id"]}
                )

        # Zeigt das Formular an, falls user_input None ist oder Fehler aufgetreten sind
        return self.async_show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA, 
            errors=errors
        )


class SpeisekammerConnectionError(Exception):
    """Wird ausgelöst, wenn die Verbindung nicht hergestellt werden kann."""
    pass
