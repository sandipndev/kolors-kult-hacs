"""Constants for the Kolors Kult integration."""

DOMAIN = "kolors_kult"

API_BASE_URL = "https://api.kolorsworld.net/app/1.3"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Platforms supported
PLATFORMS = ["switch", "fan"]

# Update interval in seconds
UPDATE_INTERVAL = 15

# Device types from the API
DEVICE_TYPE_BUTTON = "button"
DEVICE_TYPE_STEP_DIMMER = "step_dimmer"

# Fan dimmer has 8 speed steps: 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100
DIMMER_8_STEPS = 8
DIMMER_STEP_SIZE = 100.0 / DIMMER_8_STEPS  # 12.5
