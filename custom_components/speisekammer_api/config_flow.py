import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_URL, CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN
from .api import SpeisekammerAPI, SpeisekammerAPIError

# Schema für die Eingabemaske
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_API_URL): str,
    vol.Required(CONF_API_TOKEN): str,
})

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validiert die Benutzer-Eingabe und testet die Verbindung zur API."""
    
    api = SpeisekammerAPI(hass, data[CONF_API_URL], data[CONF_API_TOKEN])
    
    try:
        # Versucht, Community ID und Lagerorte abzurufen (Test der Verbindung)
        await api.async_fetch_initial_data()
    except SpeisekammerAPIError as err:
        # SpeisekammerAPIError wird aus der api.py geworfen
        raise SpeisekammerConnectionError("Die Verbindung zur API ist fehlgeschlagen.") from err

    # Rückgabe, wenn die Validierung erfolgreich war
    return {"title": "Speisekammer API", "community_id": api.community_id}


class SpeisekammerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Konfigurationsfluss für die Speisekammer API."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Behandelt den initialen Schritt des Konfigurationsflusses."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except SpeisekammerConnectionError as err:
                errors["base"] = "connection_failed"
                _LOGGER.error("Verbindungsfehler: %s", err)
            except Exception: # Alle anderen Fehler
                errors["base"] = "unknown"
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
