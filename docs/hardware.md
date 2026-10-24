# Hardware

A mix of a few big brands, cheap DIY parts and hand-me-downs. Nothing has to be from one ecosystem.

About 90 physical devices from 25 brands. Most of the "real" lighting is on proper in-wall
switches or Philips Hue; everything else is added on, from IKEA plugs to a few dollars' worth of
USB switch.

## The brains and the bits behind the scenes

| Role | What | Notes |
|---|---|---|
| **Brain** | Raspberry Pi 5, Home Assistant OS, USB drive for data | ~$100 |
| **Standby brain + wall calendar** | Raspberry Pi 400 (hand-me-down) + 14" ASUS ProArt bar display | Runs the departure board kiosk; an HA container is created from a pinned image only when it takes over |
| **Private cloud + Zigbee/MQTT/proxy/watchdog** | Ex-business HP EliteBook laptop (baelap) | My own local private cloud; Docker: Mosquitto, Zigbee2MQTT, Caddy |
| **Screen server** | Ex-office HP mini PC, plugged into the lounge TV | My admin PC. It also serves the TV screensaver and the Nest Hub pages (see [Screens and controls](#screens-and-controls)) |
| **NAS** | End-of-life QNAP, given a second life with Unraid | Plex, music, backups |
| **Zigbee coordinator** | Sonoff Dongle-M (network), PoE | No USB stick, so either HA can use it |
| **Hue Bridge** | Philips Hue Bridge, second-hand for about $25 | Not essential: added to get the best out of Hue scenes and addressable strip lighting |

## Lights

**The ceiling lights are on Clipsal Iconic Wiser push-button switches and dimmers** (Zigbee),
installed in the wall in place of the old switches. That matters more than anything else on this
page: guests press the switch on the wall like they would anywhere else, the lights still work if
Home Assistant is down, and because they're mains powered, every one of them is also a Zigbee
router that strengthens the mesh for the battery sensors.

**Philips Hue** does the colour and the scenes: three Hue Play bars, a Lightstrip, an OmniGlow
strip and a Flux strip.

Everything else is added on, room by room:

| Room | On the wall (Clipsal Iconic Wiser) | Added on |
|---|---|---|
| **Lounge** | Downlights (dimmer) | TV art lights (Tuya 2-channel USB switch), couch underglow (WiZ + Govee), accent chair lights and bar spotlights (IKEA TRETAKT plugs), Lasco fairy lights (Tuya Wi-Fi), a Neewer RGB530 panel, and a mirror ball spun by a DIY ESP32-C3 |
| **Kitchen + dining** | Kitchen lights (switch), art pendants over the table (dimmer) | Kitchen art (IKEA TRADFRI 30 W driver on a Tuya USB switch), above-fridge lights (Tuya 3-channel USB switch), console candles, kitchen floor and kitchen LEDs (TRETAKT plugs) |
| **Bedroom** | Bedroom lights (dimmer), ceiling fan (switch) | Bed lamps (IKEA TRADFRI bulbs), candles (Tuya USB switch), two LED strips (TRETAKT plugs), cupboard lights (Tuya 3-channel USB switch) |
| **Bathroom** | Downlights (switch) | Vanity lights (Tuya 2-channel USB switch), mirror LED (WiZ) |
| **Office + wardrobe** | Office lights (dimmer), wardrobe (switch) | Wardrobe LEDs (TRETAKT plug) |

The cheap AliExpress Tuya Zigbee USB switches are the unsung heroes: any USB-powered lamp, candle
or strip becomes a smart light for a few dollars, and the multi-channel ones are grouped so each
shows up as one light.

## Presence and sensors

| Role | What | Notes |
|---|---|---|
| **Radar** | Apollo R PRO-1 (LD2450 + LD2412, Ethernet) as main area/home sensor (~$120 and worth it) + 2× DIY ESP32 + LD2450 | ~$15 per DIY radar; hidden under a downlight cover, behind a canvas and inside a display box. Each radar tracks up to 3 people, so up to 9 across the flat |
| **Bluetooth proxies** | 3-4 cheap ESP32 boards (they could run on the rotary displays, Apollo and voice box too, but are kept separate for door lock stability) | Bermuda presence, SwitchBot lock |
| **Motion** | IKEA VALLHORN (bedroom, office), Xiaomi (kitchen), Sonoff SNZB-06P (bathroom), Tuya PIR (wardrobe) | Instant-on for Kitchen, Bedroom, Office, Bathroom (plus extra presence for Bathroom) |
| **Doors** | IKEA PARASOLL (front door), a Zigbee contact sensor (balcony door) | |
| **Leak** | IKEA BADRING | Cheap, essential |
| **Climate sensor** | IKEA TIMMERFLOTTE | Temperature and humidity in the lounge |
| **Camera** | Nest (attic) | Only switches on while I'm away |

## Door

| What | Notes |
|---|---|
| SwitchBot Lock Pro + fingerprint keypad + IKEA PARASOLL contact sensor | The keypad is the main way in, with extra backup systems in place |

## Screens and controls

| Role | What | Notes |
|---|---|---|
| **The one remote** | 2× Sanytron Astrion HA100 remotes running [my own app](https://github.com/baes-cloud/astrion-dashboard) | Android remotes with a touch screen, real buttons, a mic and a charging dock. More below |
| **Knobs** | BæoRemote music knob + hub knob (DIY ESP32-S3 round displays) | Media by the couch, whole-home control in the bedroom |
| **Nest Hubs** | 2× Google Nest Hub (kitchen, bedroom) | No Google dashboard: my own page is cast to them and kept there |
| **TVs** | Samsung The Serif (55" lounge + 43" bedroom) + Google TV Streamer (lounge) + Chromecast (bedroom) | ADB on the Google TV Streamer is the game changer here. Its screensaver is my own page too |
| **Voice** | ESP32-S3-Box-3, plus the remotes while they're docked | "Hey Pikachu" |
| **Office screen** | Samsung 32" Smart Monitor M7 | |
| **Phone** | Android + Home Assistant Companion app (GPS, BLE beacon, notifications) | |
| **Spare buttons** | More than a dozen Zigbee buttons from previous setups | Sitting in a drawer awaiting their next purpose |

**The remotes in a bit more detail.** The Astrion HA100 is an affordable Android remote sold for
Home Assistant, with a 480×800 touch screen and dedicated buttons. Its own app was slow, so I
designed a replacement from scratch that talks to Home Assistant directly:

- Four pages, each on its own physical button: TV (Plex search and libraries), Main (weather,
  next alarm, the door, scenes and a live floorplan with lights, people and the robot vacuum),
  Media (Sonos, mixes, search across the music library and Spotify, and which rooms are playing)
  and Climate (aircon, fan and blinds).
- **Hold Menu** for a help guide aimed at guests: short answers, a walkthrough that asks for real
  button presses, and a one-page version that pops up on the TV at the same time.
- **On the dock** it becomes a clock: a screensaver with the time, the next alarm and what's
  playing (warm amber at night), and it listens for "hey Pikachu".
- Alarm, leak, intruder, door and washer popups wake it up, wherever it is.

**The TVs and Nest Hubs** show the same ambient page, Bæovision, served by the mini PC behind the
lounge TV. On the Google TV Streamer it replaces Google's own screensaver; on the Hubs it's cast
and kept there. Details and screenshots are in
[One remote, and popups on every screen](04-popups-on-every-screen.md#tvs-and-nest-hubs-ambient-screens).

## Sound and media

| Role | What | Notes |
|---|---|---|
| **Speakers** | 11 Sonos: lounge Beam + Sub Mini + 2× ceiling One (rears) + 2× ceiling Play:3s (extra fronts); SYMFONISK lamp pair (bedroom); One + One SL pair (office & wardrobe); one Move (waterproof) in the bathroom | System built over many years, some second hand, some free with wine promos |
| **Media** | Plex on the NAS, Music Assistant (local library + Spotify) | |

## Climate and blinds

| Role | What | Notes |
|---|---|---|
| **Aircon** | Fujitsu split system + Sensibo | Direct Fujitsu smart integration is possible, but complex and clunky. Tried Sensibo on recommendation, and found it easy and hassle free |
| **Fans** | Bedroom ceiling fan (on a Clipsal switch), Tuya oscillating fan in the office | |
| **Blinds** | Tuya blinds and sheer curtains (lounge and bedroom) | |

## Robots and appliances

| Role | What | Notes |
|---|---|---|
| **Robots** | Roborock Qrevo Master + Lubluelu SL68 (local via tuya-local) | The SL68 is my old, cheap one: the backup and a final sweep |
| **Washer** | Samsung washer, now local via LocalThings | Moved off the Samsung cloud in October 2026 |

---
[← Back to the overview](../README.md)
