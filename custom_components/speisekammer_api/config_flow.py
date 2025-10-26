import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import AbortFlow

from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, DEFAULT_API_URL
from .api import SpeisekammerAPI, SpeisekammerAPIError

_LOGGER = logging.getLogger(__name__)


# Schema für die Eingabemaske
DATA_SCHEMA = vol.Schema({
    # Die URL ist optional und hat einen Standardwert
    vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
    # Der Token ist weiterhin erforderlich
    vol.Required(CONF_API_TOKEN): str,
})

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validiert die Benutzer-Eingabe und testet die Verbindung zur API."""
    
    # URL-Verarbeitung: Stellt sicher, dass das Protokoll (https://) verwendet wird
    api_url = data[CONF_API_URL]
    if not api_url.startswith(("http://", "https://")):
         api_url = f"https://{api_url}"
    
    api = SpeisekammerAPI(hass, api_url, data[CONF_API_TOKEN])
    
    try:
        # Versucht, Community ID und Lagerorte abzurufen (Test der Verbindung)
        await api.async_fetch_initial_data()
    except SpeisekammerAPIError as err:
        _LOGGER.error("Validierung fehlgeschlagen: %s", err)
        # Die Fehlermeldung der API wird direkt an den Benutzer zurückgegeben
        raise SpeisekammerConnectionError(f"Verbindungsfehler: {err}") from err

    # Rückgabe, wenn die Validierung erfolgreich war
    return {"title": "Speisekammer API", "community_id": api.community_id}


class SpeisekammerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Konfigurationsfluss für die Speisekammer API."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL 

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Behandelt den initialen Schritt des Konfigurationsflusses."""
        errors = {}

        if user_input is not None:
            # Stellt sicher, dass nur eine Instanz konfiguriert werden kann
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except SpeisekammerConnectionError as err:
                # Setzt den Fehler im Formular
                errors["base"] = str(err)
            except Exception as err: 
                _LOGGER.exception("Unerwarteter Fehler während der Einrichtung.")
                errors["base"] = "Unbekannter Fehler während der Einrichtung."
            else:
                # Erfolgreich: Erzeugt den Konfigurationseintrag
                return self.async_create_entry(
                    title=info["title"], 
                    # Die URL muss im data-Dict mit dem bereinigten Wert gespeichert werden
                    data=user_input, 
                    options={"community_id": info["community_id"]}
                )

        # Zeigt das Formular an
        return self.async_show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA, 
            errors=errors
        )


class SpeisekammerConnectionError(Exception):
    """Wird ausgelöst, wenn die Verbindung nicht hergestellt werden kann."""
    pass
