# Hardware

A mix of a few big brands, cheap DIY parts and hand-me-downs. Nothing has to be from one ecosystem.

| Role | What | Notes |
|---|---|---|
| **Brain** | Raspberry Pi 5, Home Assistant OS, USB drive for data | ~$100 |
| **Standby brain + wall calendar** | Raspberry Pi 400 (hand-me-down) + 14" ASUS ProArt bar display | Runs the departure board kiosk and a stopped HA container |
| **Private cloud + Zigbee/MQTT/proxy/watchdog** | Ex-business HP EliteBook laptop (baelap) | My own local private cloud; Docker: Mosquitto, Zigbee2MQTT, Caddy |
| **NAS** | End-of-life QNAP, given a second life with Unraid | Plex, music, backups |
| **Zigbee coordinator** | Sonoff Dongle-M (network), POE | No USB stick, so either HA can use it |
| **Hue Bridge** | Philips Hue Bridge, second-hand for about $25 | Not essential: added to get the best out of Hue scenes and addressable strip lighting |
| **Radar** | Apollo R PRO-1 (LD2450 + LD2412, Ethernet) as main area/home sensor (~$120 and worth it) + 2× DIY ESP32 + LD2450 | ~$15 per DIY radar; hidden under a downlight cover, behind a canvas and inside a display box |
| **Bluetooth proxies** | 3-4 cheap ESP32 boards (can be run on rotary displays, apollo and voice box too but seperated for door lock stability) | Bermuda presence, SwitchBot lock |
| **Motion** | IKEA VALLHORN, Xiaomi, Sonoff SNZB-06P | Instant-on for Kitchen, Bedroom, Office, Bathroom (plus extra presence for Bathroom) |
| **Door** | SwitchBot Lock Pro + fingerprint keypad + IKEA PARASOLL contact sensor | The keypad is the main way in, with extra backup systems in place |
| **Leak** | IKEA BADRING | Cheap, essential |
| **Lights** | Clipsal Wiser switches/dimmers (Zigbee), IKEA TRADFRI, Philips Hue (Play, Lightstrip, OmniGlow), WiZ, Govee (Matter), Tuya/Smart Life, IKEA TRETAKT plugs, aliexpress USB light switches | Old, new, installed, added-on |
| **Speakers** | 11 Sonos: lounge Beam + Sub Mini + 2× ceiling One (rears) + 2× ceiling Play:3s (extra fronts); SYMFONISK lamp pair (bedroom); One + One SL pair (office & wardrobe); one Move (waterpoof) in the bathroom | System built over many years, some second hand, some free with wine promos |
| **TVs** | Samsung The Serif (55" + 43") + Google TV Streamer | ADB on google streamer is the game changer here |
| **Robots** | Roborock Qrevo Master + Lubluelu SL68 (local via tuya-local) | The SL68 is my old, cheap one: the backup and a final sweep |
| **Appliances** | Samsung washer (SmartThings), Sensibo (aircon) | Direct Fijutsu smart intergration possible, but complex and clunky. Tried sensibo on recommendation, and found it easy and hassle free |
| **Camera** | Nest (attic) | Only switches on while I'm away |
| **Controls** | 2× Sanytron Astrion HA100 remotes running my own app (the one remote), BæoRemote music knob + hub knob (DIY ESP32-S3 round displays), ESP32-S3-Box-3 (voice) | Leaving more than a dozen zigbee buttons from previous setup's sitting in a drawer awaiting their next purpose |
| **Phone** | Android + Home Assistant Companion app (GPS, BLE beacon, notifications) | |

---
[← Back to the overview](../README.md)
