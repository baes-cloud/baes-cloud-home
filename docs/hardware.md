# Hardware

A mix of a few big brands, cheap DIY parts and hand-me-downs. Nothing has to be from one ecosystem.

| Role | What | Notes |
|---|---|---|
| **Brain** | Raspberry Pi 5, Home Assistant OS, USB drive for data | ~$100 |
| **Standby brain + wall calendar** | Raspberry Pi 400 (hand-me-down) + 14" ASUS ProArt bar display | Runs the departure board kiosk and a stopped HA container |
| **Zigbee/MQTT/proxy/watchdog** | Ex-business HP EliteBook laptop | Docker: Mosquitto, Zigbee2MQTT, Caddy |
| **Firmware builds, party lights** | 2013-era Intel i5 mini-PC | ESPHome desktop builder, beat-sync player |
| **NAS** | Unraid | Plex, music, backups |
| **Zigbee coordinator** | Sonoff Dongle-M (network) | No USB stick, so either HA can use it |
| **Radar** | Apollo R PRO-1 (LD2450 + LD2412, Ethernet) + 2× DIY ESP32 + LD2450 | ~$15 per DIY radar; hidden under a downlight cover, behind a canvas and inside a display box |
| **Bluetooth proxies** | 4–5 cheap ESP32 boards (one doubles as a camera board) | Bermuda presence, SwitchBot lock |
| **Motion** | IKEA VALLHORN, Xiaomi, Sonoff SNZB-06P | Instant-on |
| **Door** | SwitchBot Lock Pro + IKEA PARASOLL contact sensor + NFC tags | |
| **Leak** | IKEA BADRING | |
| **Lights** | Clipsal Wiser switches/dimmers (Zigbee), IKEA TRADFRI, Philips Hue (Play, Lightstrip, OmniGlow), WiZ, Govee (Matter), Tuya/Smart Life, IKEA TRETAKT plugs, USB light switches | |
| **Speakers** | Sonos Beam + 2× Play:3, plus bedroom, bathroom and office speakers | |
| **TVs** | Samsung The Serif (55" + 43") + Google TV Streamer | |
| **Robots** | Roborock Qrevo Master + Lubluelu SL68 (local via tuya-local) | |
| **Appliances** | Samsung washer (SmartThings), Sensibo (aircon) | |
| **Camera** | Nest (attic) | |
| **Controls** | 2× Sanytron Astrion HA100 remotes running my own app (the one remote), BæoRemote music knob + hub knob (DIY ESP32-S3 round displays), ESP32-S3-Box-3 (voice), IKEA BILRESA buttons | |
| **Phone** | Android + Home Assistant Companion app (GPS, BLE beacon, notifications) | |

---
[← Back to the overview](../README.md)
