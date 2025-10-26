"""Konstanten für die Speisekammer API Integration."""

DOMAIN = "speisekammer_api"

# Konfigurationsfluss Schlüssel
CONF_API_URL = "api_url"
CONF_API_TOKEN = "api_token"
CONF_COMMUNITY_ID = "community_id" # Wird automatisch ermittelt, aber hier zur Referenz

DEFAULT_API_URL = "https://app.speisekammer.app"

# Services
SERVICE_SCAN_ITEM = "scan_item"
SERVICE_UPDATE_STOCK = "update_stock"
SERVICE_REFRESH_DATA = "refresh_data"

# Standard-API-Pfade, abgeleitet von der Node-RED-Logik
API_PATH_COMMUNITIES = "/communities"
API_PATH_STORAGE_LOCATIONS = "/communities/{community_id}/storage-locations"
API_PATH_STOCK = "/stock" 

# Status-Codes für PUT /stock (gemäß Ihrer Node-RED Logik)
STATUS_ADD = 1 # Erfassung
STATUS_REMOVE = 2 # Ausgabe/Verbrauch

# Barcode-Aktionen für den Service
ACTION_ADD = "add"
ACTION_REMOVE = "remove"
