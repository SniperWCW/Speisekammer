"""Konstanten für die Speisekammer API Integration."""

DOMAIN = "speisekammer_api"

# =====================================================================
# KONFIGURATION & API-DEFAULTS
# =====================================================================

# Standard-API-URL der Speisekammer-App.
# WICHTIG: Verwenden Sie die URL, mit der die Einrichtung erfolgreich war.
DEFAULT_API_URL = "https://app.speisekammer.app" 

# Konfigurationsfluss Schlüssel
CONF_API_URL = "api_url"
CONF_API_TOKEN = "api_token"
CONF_COMMUNITY_ID = "community_id" 

# =====================================================================
# SERVICES & ENDPUNKTE
# =====================================================================

# Services
SERVICE_SCAN_ITEM = "scan_item"
SERVICE_UPDATE_STOCK = "update_stock" # Optional, falls implementiert
SERVICE_REFRESH_DATA = "refresh_data"

# Standard-API-Pfade
API_PATH_COMMUNITIES = "/communities"
API_PATH_STORAGE_LOCATIONS = "/communities/{community_id}/storage-locations"
API_PATH_STOCK = "/stock" 

# Status-Codes für PUT /stock (gemäß Ihrer Node-RED Logik)
STATUS_ADD = 1      # Erfassung
STATUS_REMOVE = 2   # Ausgabe/Verbrauch

# Barcode-Aktionen für den Service
ACTION_ADD = "add"
ACTION_REMOVE = "remove"
