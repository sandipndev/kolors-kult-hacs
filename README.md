# Kolors Kult - Home Assistant Integration

A custom [Home Assistant](https://www.home-assistant.io/) integration for [Kolors Kult](https://www.kolorsworld.com/automation/kult/) smart switches and fan regulators, installable via [HACS](https://hacs.xyz/).

## Supported Devices

| Device Type | HA Entity | Controls |
|---|---|---|
| Button (1/2/4-gang touch switches) | `switch` | On / Off |
| 8-Step Dimmer (fan regulator) | `fan` | On / Off + 8 speed levels |

Devices are grouped under their physical controller panel in the Home Assistant device registry.

## Prerequisites

- A working Kolors Kult setup with the **KULT HOME AUTOMATION** iOS/Android app
- Your Kolors Kult **username** and **password** (the same credentials you use to log in to the app)
- [HACS](https://hacs.xyz/) installed on your Home Assistant instance

## Installation

1. Open Home Assistant and go to **HACS → Integrations**
2. Click the **three-dot menu** (top right) → **Custom repositories**
3. Enter the repository URL: `sandipndev/kolors-kult-hacs`
4. Select category: **Integration**
5. Click **Add**
6. Find **Kolors Kult** in the HACS integration list and click **Download**
7. **Restart Home Assistant**

## Setup

1. After restarting, go to **Settings → Devices & Services**
2. Click **+ Add Integration**
3. Search for **Kolors Kult**
4. Enter your **username** and **password**
5. Your switches and fan regulators will appear as entities automatically

## How It Works

This integration communicates with the Kolors Kult cloud API (`api.kolorsworld.net`) — the same backend used by the mobile app. It polls for device state every 15 seconds and sends commands one at a time to ensure reliability.

- **Switches** map to Home Assistant `switch` entities with simple on/off control
- **Fan regulators** (8-step dimmers) map to `fan` entities with 8 discrete speed levels
- When you toggle a device, the UI will show a loading spinner until the confirmed state comes back from the API — no guessing

## Notes

- This is a **cloud polling** integration — it requires an internet connection to control your devices
- The integration uses the same API as the Kolors Kult mobile app, so both can be used simultaneously
- Fan regulators default to 100% (or the last used speed) when turned on without specifying a speed

## Troubleshooting

- **"Failed to connect to Kolors Kult servers"** — Check your internet connection. The API server (`api.kolorsworld.net`) may be temporarily down.
- **"Invalid username or password"** — Make sure you're entering your **username** (not email), the same one you use in the Kolors Kult app.
- **Device states are stale** — The integration polls every 15 seconds. If you control a device from the physical switch or the mobile app, it may take up to 15 seconds to reflect in Home Assistant.

## Credits

Built by reverse-engineering the Kolors Kult mobile app API. Kolors Kult is a product of [Kolors India Private Limited](https://www.kolorsworld.com/), with the smart home platform powered by [Falcon Control Systems / NUOS](https://nuos.in/).
