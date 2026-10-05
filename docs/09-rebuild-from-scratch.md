# 9 · Rebuild from scratch (and everything it depends on)

If everything were lost, this is the order I'd rebuild in. **First choice is always a
restore:** daily backups go to the Pi itself, the NAS and Home Assistant Cloud, and a full
restore brings back everything including the UI-only bits. This guide is for when there is no backup.

## 1. Core hardware
- Raspberry Pi 5 + Home Assistant OS. Boot from the SD card and **move the data disk to a USB
  SSD** (*Settings → System → Storage*). SD cards wear out under a database; an SSD (NVMe HAT or USB)
  for everything is even better.
- Ethernet for the Pi, a decent Wi-Fi network (2.4 GHz reachable everywhere for the cheap devices).

## 2. Add-ons (Settings → Add-ons)
| Add-on | Why |
|---|---|
| **ESPHome Device Builder** | Builds and updates all the DIY ESP32 devices. Compiles are offloaded to the ESPHome desktop builder on a mini-PC (much faster than the Pi) |
| **Matter Server** | Matter/Thread devices (IKEA BILRESA buttons, TIMMERFLOTTE sensor, a Govee strip) |
| **Music Assistant** | Local music library (SMB share on the NAS) + Spotify, played to Sonos |
| **openWakeWord** | Runs the custom "hey Pikachu" model (put the `.tflite` in `/share/openwakeword/`) |
| **Terminal & SSH** | Maintenance |
| File editor, Samba share | Optional |

## 3. Outside Home Assistant (another always-on box)
These deliberately live off the Pi, so the failover standby can use them too:
- **Mosquitto + Zigbee2MQTT** in Docker, with a **network Zigbee coordinator** (Sonoff Dongle-M)
  instead of a USB stick. Point HA's MQTT integration at that broker.
- **Caddy reverse proxy** (`lb_policy first`) in front of the primary and the standby. See [failover](08-failover-and-infrastructure.md).
- The failover **watchdog** (systemd service) and the nightly **news digest** job.
- NAS: Plex, the music share, a backups share (added in HA as *Network storage* for backups).

## 4. HACS and what it installs
Install [HACS](https://hacs.xyz), then:

**Integrations**
| Repository | Used for |
|---|---|
| [Moe8383/radar_map_manager](https://github.com/Moe8383/radar_map_manager) | Fuses the 3 LD2450 radars into room zones on the floorplan |
| [agittins/bermuda](https://github.com/agittins/bermuda) | Bluetooth room/home presence from the phone's beacon |
| [make-all/tuya-local](https://github.com/make-all/tuya-local) | Local control of Tuya devices (SL68 robot, blinds, a fan) with no cloud |
| [bremor/bureau_of_meteorology](https://github.com/bremor/bureau_of_meteorology) | Australian weather and warnings |
| [Python-roborock/RoborockCustomMap](https://github.com/Python-roborock/RoborockCustomMap) | Roborock map image |
| [thomasloven/hass-browser_mod](https://github.com/thomasloven/hass-browser_mod) | Browser control and popups for the fallback dashboards |
| [darinlarimore/neewer-ble-homeassistant](https://github.com/darinlarimore/neewer-ble-homeassistant) | A Bluetooth video light |
| [yyqclhy/Astrion-integration](https://github.com/yyqclhy/Astrion-integration) | Vendor integration for the remotes (disabled: my own app replaces it) |

**Dashboard cards** (only for the fallback dashboards, since day to day I don't use them):
Mushroom, Bubble Card, card-mod, layout-card, stack-in-card, swipe-navigation, clock-weather-card,
custom-sonos-card, HA-Firemote, RosCard, HA-hotkeys, cover-slider, light-card-hue-feature,
homeii-music-flow, xiaomi-vacuum-map-card, custom-brand-icons. Themes: Material You, Graphite, iOS themes, Bubble Theme.

## 5. Integrations
| Local (no internet needed) | Cloud (needs the vendor's servers) |
|---|---|
| ESPHome · MQTT/Zigbee2MQTT · Matter + Thread · Philips Hue · Sonos · Google Cast · WiZ · SwitchBot (Bluetooth) · Bermuda · iBeacon · tuya-local · Android TV Remote · Android Debug Bridge · Samsung TV · Plex (local server) · DLNA · Music Assistant · Radar Map Manager · System Monitor · Ping · Wyoming (openWakeWord) · go2rtc | Google Calendar · Google Gemini (conversation + AI tasks) · Home Assistant Cloud (remote access, speech) · Nest (camera) · SmartThings (washer, TV inputs) · Sensibo (aircon) · Roborock · Spotify · Bureau of Meteorology · Met.no |

Helpers that glue it together: template sensors, light groups and "switch as light" helpers.
They're exported in [`config/helpers/`](../config/helpers/).

## 6. Restore the config from this repo
1. Copy [`config/`](../config/) into `/config/` (`configuration.yaml`, `automations.yaml`,
   `scripts.yaml`, `scenes.yaml`, `packages/`).
2. Recreate the UI helpers from [`config/helpers/ui_helpers.yaml`](../config/helpers/ui_helpers.yaml)
   (paste them into a package, or recreate them in *Settings → Helpers*).
3. Look for placeholders like `<nas-ip>`, `<device-ip>`, `<nfc-tag-1>` and `<device-id>`, and fill in yours.
4. Entity IDs follow my device names (`light.kitchen`, `media_player.club`…). Rename your devices
   to match, or search and replace.
5. Check the config and restart.

## 7. Devices
- **ESPHome devices:** [`config/esphome/`](../config/esphome/) (copy `secrets.example.yaml` to `secrets.yaml`).
  The Apollo R PRO-1 uses Apollo's own package. The rotary knobs come from
  [esp-rotary-display-ha-hub](https://github.com/baes-cloud/esp-rotary-display-ha-hub).
- **Radar map:** load the floorplan in Radar Map Manager and redraw the zones from
  [`config/rmm/radar_map_manager.json`](../config/rmm/radar_map_manager.json) (points are % of the image).
- **Bermuda:** turn on the Companion app's *BLE transmitter*, add ESP32 Bluetooth proxies, and
  create the phone's Bermuda tracker.
- **Voice:** an ESP32-S3-Box-3 or any satellite, plus the "Piks" pipeline (openWakeWord custom model,
  HA Cloud speech, local intents first, Gemini as the conversation agent).
- **Remotes:** [astrion-dashboard](https://github.com/baes-cloud/astrion-dashboard).
- **Wall board + standby:** [rpi-departure-board](https://github.com/baes-cloud/rpi-departure-board),
  then the standby HA container on the same Pi 400 ([failover](08-failover-and-infrastructure.md)).

## 8. Recorder (database) settings
The exclusions in [`configuration.yaml`](../config/configuration.yaml) matter more than they look:
raw radar coordinates, Bluetooth distances and the TV's playback position were about **85%** of
all database writes. Keep them excluded and the database stays small and the SSD lasts.

---
[← Back to the overview](../README.md)
