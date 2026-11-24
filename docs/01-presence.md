# 1 · Presence: radar, Bluetooth and GPS

Everything else in this house hangs off one question: **where am I, and what am I doing?**
Motion sensors can't answer it on their own: they forget you the moment you sit still. So
the house combines four kinds of sensing, each covering the others' blind spots.

| Layer | Hardware | What it's good at | What it's bad at |
|---|---|---|---|
| **mmWave radar (LD2450)** | 3 radars: an Apollo R PRO-1 plus two DIY ESP32 + LD2450 boards (~$15 radar each) | Each tracks up to 3 people with x/y position, so up to **9 people** across the flat | Can lose a perfectly still person; sees robot vacuums and vibrating washers as people |
| **"Still" radar (LD2412)** | Built into the Apollo | Picks up breathing and micro-movement on the sofa | No position, just "someone is there" |
| **PIR motion** | IKEA VALLHORN, Xiaomi, a Sonoff SNZB-06P | Instant "someone walked in" | Times out on people sitting still |
| **Bluetooth (BLE)** | ESP32 Bluetooth proxies around the flat + my phone's beacon, via **Bermuda** | "My phone is in the flat" (and roughly which room) | Phones put beacons to sleep; BLE alone can be spoofed |
| **GPS** | Home Assistant Companion app | "I'm actually away from home" | Slow and fuzzy near home |

The radars I built are hidden in plain sight: one is in the ceiling under a standard downlight
cover, one sits on a wall behind a canvas artwork, and one is on a shelf inside a display box.
mmWave radar sees straight through fabric, canvas and thin plastic.

## Radar Map Manager: one map from three radars

[Radar Map Manager](https://github.com/Moe8383/radar_map_manager) (a HACS integration) puts all
three LD2450s onto my floorplan, merges the same person seen by two radars into one target,
smooths the tracks, and turns zones I've drawn into ordinary Home Assistant sensors:

- **Room zones:** lounge, kitchen, office, wardrobe, bathroom, bedroom, plus a *sofa* and a *bed* zone
- **Stationary zones:** the bed (holds for an hour), the sofa and the shower, where "not moving" is expected
- **Exclude zone:** the washer/dryer (it vibrates exactly like a person)
- **Entrance zone:** the front door

Each zone becomes `binary_sensor.rmm_default_<zone>_occupancy` plus a people count, and
`sensor.rmm_default_master` counts everyone in the flat.

![Zones](../images/rmm/zones.png)

**What it looks like in practice** (an illustrative mock-up built from my real zones and
radar positions; the generator is in [`tools/make_rmm_gif.py`](../tools/make_rmm_gif.py)):

![RMM demo](../images/rmm/rmm-demo.gif)

And the real thing, live on the remote:

<img src="../images/astrion/LD2450-tracking.gif" width="320" alt="Live radar tracking on the remote">

The exported map (zones, radar positions, tracking settings) is in
[`config/rmm/radar_map_manager.json`](../config/rmm/radar_map_manager.json).

## The pattern every room light uses

> **PIR turns it on instantly. Radar keeps it on while you're still there. A sweep cleans up.**

```yaml
- id: '1785400000003'
  alias: 'RMM: Kitchen presence light'
  description: 'Kitchen lights (light.kitchen_group). ON in the day window from any
    kitchen sensor (kitchen PIR = the IKEA VALLHORN, re-paired 2026-11-20, RMM kitchen
    zone) or the front door opening. OFF is checked every minute (reload-proof, so
    the sweeper no longer handles the kitchen): never while any kitchen sensor is
    on. the guest dates, 06:00-21:00 (guests): off only after the kitchen has been
    quiet 20 min AND the whole house (all PIRs, RMM zones, radar moving targets, front
    door) quiet 15 min. Otherwise: off 5 min after the kitchen goes quiet (2026-11-17:
    long hold limited to the guest dates). Rewritten by Claude 2026-11-17 for the
    guests (old config in ~/Documents/claude/ha-backups/kitchen-hold-20261117).'
  triggers:
  - trigger: state
    entity_id:
    - binary_sensor.kitchen_motion
    - binary_sensor.rmm_default_kitchen_occupancy
    to: 'on'
    id: 'on'
  - trigger: state
    entity_id: binary_sensor.front_door_open
    to: 'on'
    id: 'on'
  - trigger: time_pattern
    minutes: /1
    id: check
  conditions:
  - alias: Auto-stay is off (party mode suspends this)
    condition: state
    entity_id: input_boolean.auto_stay
    state: 'off'
  actions:
  - variables:
      kitchen_sensors:
      - binary_sensor.kitchen_motion
      - binary_sensor.rmm_default_kitchen_occupancy
      - binary_sensor.front_door_open
      house_sensors:
      - binary_sensor.kitchen_motion
      - binary_sensor.rmm_default_kitchen_occupancy
      - binary_sensor.front_door_open
      - binary_sensor.rmm_default_lounge_occupancy
      - binary_sensor.rmm_default_office_occupancy
      - binary_sensor.rmm_default_wardrobe_occupancy
      - binary_sensor.rmm_default_bathroom_occupancy
      - binary_sensor.rmm_default_bedroom_occupancy
      - binary_sensor.rmm_default_sofa_occupancy
      - binary_sensor.rmm_default_bed_occupancy
      - binary_sensor.bathroom_occupancy_sonoff_snzb_06p
      - binary_sensor.bedroom_motion
      - binary_sensor.wardrobe_motion_occupancy
      - binary_sensor.club_apollo_r_pro_1_ld2450_moving_target
      - binary_sensor.ld2450_tracker_moving_target
      - binary_sensor.ld2450_tracker_2_moving_target
  - choose:
    - conditions:
      - condition: trigger
        id: 'on'
      - alias: Day window
        condition: template
        value_template: '{% set d = now().weekday() %}{% set t = now().hour*60 + now().minute
          %}{{ not ((d in [6,0,1,2,3] and t >= 21*60) or (d in [0,1,2,3,4] and t <
          7*60) or (d in [4,5] and t >= 23*60) or (d in [5,6] and t < 9*60)) }}'
      sequence:
      - action: light.turn_on
        target:
          entity_id: light.kitchen_group
        data: {}
    - conditions:
      - condition: trigger
        id: check
      - condition: state
        entity_id: light.kitchen_group
        state: 'on'
      - alias: Kitchen (and, the guest dates by day, the house) quiet long enough
        condition: template
        value_template: '{% set ns = namespace(q=86400) %}{% for s in expand(kitchen_sensors)
          %}{% if s.state == ''on'' %}{% set ns.q = 0 %}{% else %}{% set ns.q = [ns.q,
          (now() - s.last_changed).total_seconds()] | min %}{% endif %}{% endfor %}{%
          set kq = ns.q %}{% set ns = namespace(q=86400) %}{% for s in expand(house_sensors)
          %}{% if s.state == ''on'' %}{% set ns.q = 0 %}{% else %}{% set ns.q = [ns.q,
          (now() - s.last_changed).total_seconds()] | min %}{% endif %}{% endfor %}{%
          set hq = ns.q %}{% set long = is_state('input_boolean.guests_staying','on')
          and 6 <= now().hour < 21 %}{{ (kq > 1200 and hq > 900) if long else (kq
          > 300) }}'
      sequence:
      - action: light.turn_off
        target:
          entity_id: light.kitchen_group
        data: {}
  mode: queued
  max: 5
```

The **night path** is the same idea at 2 am. The bathroom opens off the bedroom and into the
wardrobe, which opens into the kitchen. So getting up for the bathroom, then going out through the
wardrobe to the kitchen for a drink, follows exactly the route the automation lights, dimly:
mirror LED, wardrobe, kitchen at 25%. Back across the lounge to bed, it all goes off two minutes
later. That's the walk in the animation above.

<details><summary><b>RMM: Night path to bathroom</b> (click to expand)</summary>

```yaml
- id: '1785400000002'
  alias: 'RMM: Night path to bathroom'
  description: 'Getting up at night: wardrobe LED + bathroom mirror LED only. Starts
    on the bathroom PIR, or on the office radar zone / office+wardrobe PIRs when the
    kitchen radar saw someone arrive in the last 2 min (a walk from the sofa; a parked
    ghost has an old last_changed and can''t pass). No kitchen triggers or kitchen
    lights: it must never wake anyone on the couch.
    2026-11-22: wardrobe LED swapped for the light.wardrobes group, plus
    the Hue Flux strip and kitchen console candles (Bae''s request). Off when back
    in bed/sofa 2 min or office/wardrobe/bathroom empty 4 min. Created by Claude 2026-07-25.
    2026-11-07: the wardrobe PIR trigger pointed at binary_sensor.bathroom_motion,
    which no longer exists; now binary_sensor.wardrobe_motion_occupancy.'
  triggers:
  - trigger: state
    entity_id: binary_sensor.bathroom_occupancy_sonoff_snzb_06p
    to: 'on'
    id: path
  - trigger: state
    entity_id:
    - binary_sensor.rmm_default_office_occupancy
    - binary_sensor.wardrobe_motion_occupancy
    to: 'on'
    id: via_kitchen
  - trigger: state
    entity_id:
    - binary_sensor.rmm_default_bed_occupancy
    - binary_sensor.rmm_default_sofa_occupancy
    to: 'on'
    for: 00:02:00
    id: return
  - trigger: state
    entity_id:
    - binary_sensor.rmm_default_office_occupancy
    - binary_sensor.rmm_default_wardrobe_occupancy
    - binary_sensor.rmm_default_bathroom_occupancy
    - binary_sensor.bathroom_occupancy_sonoff_snzb_06p
    to: 'off'
    for: 00:04:00
    id: away
  conditions:
  - alias: Auto-stay is off (party mode suspends this)
    condition: state
    entity_id: input_boolean.auto_stay
    state: 'off'
  - condition: template
    value_template: '{% set d = now().weekday() %}{% set t = now().hour*60 + now().minute
      %}{{ (d in [6,0,1,2,3] and t >= 21*60) or (d in [0,1,2,3,4] and t < 7*60) or
      (d in [4,5] and t >= 23*60) or (d in [5,6] and t < 9*60) }}'
  actions:
  - choose:
    - conditions:
      - condition: trigger
        id: path
      - alias: Washer guard - while the washer runs it shakes the bathroom mmWave, so
          only count it if someone also moved in the bedroom/wardrobe in the last 2 min
        condition: template
        value_template: >-
          {% if not is_state('binary_sensor.samsung_washer_da_wm_tp2_20_common_running','on') %}true{% else %}
          {%- set ns = namespace(ok=false) -%}
          {%- for e in ['binary_sensor.bedroom_motion','binary_sensor.wardrobe_motion_occupancy','binary_sensor.rmm_default_bedroom_occupancy','binary_sensor.rmm_default_bed_occupancy'] -%}
          {%- set s = states[e] -%}
          {%- if s is not none and (s.state == 'on' or (now() - s.last_changed).total_seconds() < 120) -%}{%- set ns.ok = true -%}{%- endif -%}
          {%- endfor -%}{{ ns.ok }}{% endif %}
      sequence:
      - action: light.turn_on
        target:
          entity_id:
          - light.wardrobes
          - light.kitchen_console_candles
        data:
          brightness_pct: 40
        continue_on_error: true
      - alias: Flux strip much dimmer than the rest (Bae 2026-11-25)
        action: light.turn_on
        target:
          entity_id: light.home_hue_flux_strip_light_1
        data:
          brightness_pct: 5
        continue_on_error: true
      - alias: WiZ mirror LED last, and only if reachable (pywizlight errors abort
          the run)
        if:
        - condition: template
          value_template: '{{ states(''light.bathroom_mirror_led'') not in [''unavailable'',
            ''unknown''] }}'
        then:
        - action: light.turn_on
          target:
            entity_id: light.bathroom_mirror_led
          data: {}
          continue_on_error: true
    - conditions:
      - condition: trigger
        id: via_kitchen
      - alias: Someone walked through the kitchen in the last 2 min (not a ghost parked
          there)
        condition: template
        value_template: '{% set k = states.binary_sensor.rmm_default_kitchen_occupancy
          %}{{ k is not none and (k.state == ''on'' or k.state == ''off'') and (now()
          - k.last_changed).total_seconds() < 120 }}'
      sequence:
      - action: light.turn_on
        target:
          entity_id:
          - light.wardrobes
          - light.kitchen_console_candles
        data:
          brightness_pct: 40
        continue_on_error: true
      - alias: Flux strip much dimmer than the rest (Bae 2026-11-25)
        action: light.turn_on
        target:
          entity_id: light.home_hue_flux_strip_light_1
        data:
          brightness_pct: 5
        continue_on_error: true
      - alias: WiZ mirror LED last, and only if reachable (pywizlight errors abort
          the run)
        if:
        - condition: template
          value_template: '{{ states(''light.bathroom_mirror_led'') not in [''unavailable'',
            ''unknown''] }}'
        then:
        - action: light.turn_on
          target:
            entity_id: light.bathroom_mirror_led
          data: {}
          continue_on_error: true
    - conditions:
      - condition: or
        conditions:
        - condition: trigger
          id: return
        - condition: trigger
          id: away
      - condition: state
        entity_id: binary_sensor.rmm_default_office_occupancy
        state: 'off'
      - condition: state
        entity_id: binary_sensor.rmm_default_wardrobe_occupancy
        state: 'off'
      - condition: state
        entity_id: binary_sensor.rmm_default_bathroom_occupancy
        state: 'off'
      - alias: Bathroom PIR quiet too (2026-11-22, so a dead bedroom radar can't strand
          or cut the path lights); ignored while the washer runs, which shakes it
        condition: template
        value_template: '{{ not is_state(''binary_sensor.bathroom_occupancy_sonoff_snzb_06p'',''on'')
          or is_state(''binary_sensor.samsung_washer_da_wm_tp2_20_common_running'',''on'') }}'
      sequence:
      - action: light.turn_off
        target:
          entity_id:
          - light.wardrobes
          - light.home_hue_flux_strip_light_1
          - light.kitchen_console_candles
        continue_on_error: true
      - alias: WiZ mirror LED last, and only if reachable
        if:
        - condition: template
          value_template: '{{ states(''light.bathroom_mirror_led'') not in [''unavailable'',
            ''unknown''] }}'
        then:
        - action: light.turn_off
          target:
            entity_id: light.bathroom_mirror_led
          continue_on_error: true
  mode: restart
```

</details>


### Sitting still on the sofa
The LD2450 occasionally "loses" someone who hasn't moved for a long time. The Apollo's
second radar (LD2412) detects breathing, so a template helper holds the sofa as occupied
while *either* radar still sees me. That keeps the couch lights on during a film, and it
also feeds the "fell asleep" detection that turns everything off.

<details><summary><b>RMM: Fell asleep - all lights off</b> (click to expand)</summary>

```yaml
- id: '1785400000001'
  alias: 'RMM: Fell asleep - all lights off'
  description: 'Asleep detection: sofa = Apollo radar sees zero movement for 45 min
    (observed 22.5-min awake-stillness stretches, so 25 was too tight) while the sofa
    zone is occupied (fidgeting while watching TV resets the timer, so night lights
    stay on); bed = bed zone occupied 20 min. Night window + other zones empty + guest
    mode off. UPDATED 2026-08-11: added the Apollo LD2412 in tandem. The sofa branch
    now accepts EITHER the RMM sofa zone OR the LD2412 still_target, because the RMM
    zone rests on stationary_max_hold (a 3450 s timer) and collapses if the LD2450
    loses a motionless sleeper - which strands the lights on all night. The LD2412
    detects micro-motion/breathing, so it is evidence rather than a timer. A 45-min
    quiet period on EITHER radar can now trigger. Strictly additive: every case that
    fired before still fires.'
  triggers:
  - trigger: state
    entity_id: binary_sensor.club_apollo_r_pro_1_ld2450_moving_target
    to: 'off'
    for: 00:45:00
    id: sofa
  - trigger: state
    entity_id: binary_sensor.rmm_default_bed_occupancy
    to: 'on'
    for: 00:20:00
    id: bed
  - trigger: state
    entity_id: binary_sensor.club_apollo_r_pro_1_ld2412_moving_target
    to: 'off'
    for: 00:45:00
    id: sofa
  conditions:
  - alias: Auto-stay is off (party mode suspends this)
    condition: state
    entity_id: input_boolean.auto_stay
    state: 'off'
  - alias: 'Bae is home (2026-11-03: never while Bae is away)'
    condition: state
    entity_id: binary_sensor.bae_home
    state: 'on'
  - condition: template
    value_template: '{% set d = now().weekday() %}{% set t = now().hour*60 + now().minute
      %}{{ (d in [6,0,1,2,3] and t >= 21*60) or (d in [0,1,2,3,4] and t < 7*60) or
      (d in [4,5] and t >= 23*60) or (d in [5,6] and t < 9*60) }}'
  - condition: state
    entity_id: binary_sensor.rmm_default_kitchen_occupancy
    state: 'off'
  - condition: state
    entity_id: binary_sensor.rmm_default_office_occupancy
    state: 'off'
  - condition: state
    entity_id: binary_sensor.rmm_default_wardrobe_occupancy
    state: 'off'
  - condition: state
    entity_id: binary_sensor.rmm_default_bathroom_occupancy
    state: 'off'
  - condition: state
    entity_id: input_boolean.guest_mode
    state: 'off'
  actions:
  - choose:
    - conditions:
      - condition: trigger
        id: sofa
      - condition: or
        conditions:
        - condition: state
          entity_id: binary_sensor.rmm_default_sofa_occupancy
          state: 'on'
        - condition: state
          entity_id: binary_sensor.club_apollo_r_pro_1_ld2412_still_target
          state: 'on'
      sequence:
      - action: light.turn_off
        target:
          entity_id: all
    - conditions:
      - condition: trigger
        id: bed
      sequence:
      - action: light.turn_off
        target:
          entity_id: all
  mode: single
```

</details>


### Respecting manual changes
If I switch a light by hand (app, remote, voice), the automations leave that light alone
until 6 am. The trick is to check **`context.user_id`**, not `parent_id`: time-triggered
automations also have no parent, which made the first version lock lights by mistake.

<details><summary><b>RMM: Light override tracker</b> (click to expand)</summary>

```yaml
- id: '1785400000020'
  alias: 'RMM: Light override tracker'
  description: 'A light turned off/on BY A HUMAN (context.user_id set - UI, app or
    voice) locks or unlocks that light for automation. Uses user_id, NOT parent_id:
    time-triggered automations (the sweeper, the 21:00 scene) also have parent_id=None
    and were false-locking lights. Reset daily 06:00.'
  triggers:
  - trigger: state
    entity_id:
    - light.couch
    - light.club_accent_lights
    - light.club_art_pendants
    - light.club_led_group
    to: 'off'
    id: manual_off
  - trigger: state
    entity_id:
    - light.couch
    - light.club_accent_lights
    - light.club_art_pendants
    - light.club_led_group
    to: 'on'
    id: manual_on
  conditions:
  - condition: template
    value_template: '{{ trigger.to_state.context.user_id is not none }}'
  actions:
  - choose:
    - conditions:
      - condition: trigger
        id: manual_off
      sequence:
      - action: input_boolean.turn_on
        target:
          entity_id: '{% set m = {"light.couch": "input_boolean.override_couch_light",
            "light.club_accent_lights": "input_boolean.override_accent_lights", "light.club_art_pendants":
            "input_boolean.override_art_pendants", "light.club_led_group": "input_boolean.override_club_leds"}
            %}{{ m[trigger.entity_id] }}'
    - conditions:
      - condition: trigger
        id: manual_on
      sequence:
      - action: input_boolean.turn_off
        target:
          entity_id: '{% set m = {"light.couch": "input_boolean.override_couch_light",
            "light.club_accent_lights": "input_boolean.override_accent_lights", "light.club_art_pendants":
            "input_boolean.override_art_pendants", "light.club_led_group": "input_boolean.override_club_leds"}
            %}{{ m[trigger.entity_id] }}'
  mode: queued
  max: 10
```

</details>


### Safety nets
Reloading automations wipes any pending `for:` timers, which can strand a light on. A sweep
every 5 minutes turns off any presence light whose zone has been empty past its hold time.

<details><summary><b>RMM: Zone-empty sweep</b> (click to expand)</summary>

```yaml
- id: '1785400000023'
  alias: 'RMM: Zone-empty sweep'
  description: 'Safety net every 5 min: any presence light still on while its zone
    has been empty past its hold time gets turned off. Exists because automation reloads
    wipe pending ''for:'' timers, which can strand lights on. Daytime only - night
    lighting is owned by the path/sleep/scene automations. Created by Claude 2026-07-25.
    The sofa branch also requires the lounge zone to be clear, because the club lights
    serve the whole lounge/sofa area. Office branch is business-hours aware (25 min
    hold Mon-Fri 08:00-18:00) and requires the desk PIR to be off. Sofa presence now
    comes from binary_sensor.sofa_occupied_held (RMM sofa, held while the LD2412 still
    sees someone after RMM loses a still person), so sitting still no longer turns
    the couch lights off. Changed by Claude 2026-10-04. Kitchen branch now clears
    the whole kitchen group (LED + floor) and treats an unavailable PIR as no motion.
    Changed by Claude 2026-10-25. 2026-11-17: kitchen branch removed; RMM: Kitchen
    presence light now checks its own off every minute.'
  triggers:
  - trigger: time_pattern
    minutes: /5
  conditions:
  - alias: Auto-stay is off (party mode suspends this)
    condition: state
    entity_id: input_boolean.auto_stay
    state: 'off'
  - condition: template
    value_template: '{% set d = now().weekday() %}{% set t = now().hour*60 + now().minute
      %}{{ not ((d in [6,0,1,2,3] and t >= 21*60) or (d in [0,1,2,3,4] and t < 7*60)
      or (d in [4,5] and t >= 23*60) or (d in [5,6] and t < 9*60)) }}'
  - condition: state
    entity_id: input_boolean.away_mode
    state: 'off'
  actions:
  - choose:
    - conditions:
      - condition: template
        value_template: '{% set biz =  d in [0,1,2,3,4] and t >= 8*60 and t < 18*60  %}{%
          set lim = 1500 if biz else 300 %}{{ is_state(''binary_sensor.rmm_default_office_occupancy'',''off'')
          and (now() - states.binary_sensor.rmm_default_office_occupancy.last_changed).total_seconds()
          > lim }}'
      - condition: template
        value_template: '{{ is_state(''light.office_only'',''on'') }}'
      sequence:
      - action: light.turn_off
        target:
          entity_id:
          - light.office_only
  - choose:
    - conditions:
      - condition: template
        value_template: '{{ is_state(''binary_sensor.rmm_default_wardrobe_occupancy'',''off'')
          and (now() - states.binary_sensor.rmm_default_wardrobe_occupancy.last_changed).total_seconds()
          > 120 }}'
      - condition: template
        value_template: '{{ is_state(''light.wardrobe'',''on'') }}'
      sequence:
      - action: light.turn_off
        target:
          entity_id:
          - light.wardrobe
  - choose:
    - conditions:
      - condition: template
        value_template: '{{ is_state(''binary_sensor.rmm_default_bathroom_occupancy'',''off'')
          and (now() - states.binary_sensor.rmm_default_bathroom_occupancy.last_changed).total_seconds()
          > 120 }}'
      - condition: template
        value_template: '{{ is_state(''light.bathroom_mirror_led'',''on'') or is_state(''light.bathroom_downlights'',''on'')
          }}'
      - condition: state
        entity_id: binary_sensor.bathroom_occupancy_sonoff_snzb_06p
        state: 'off'
      sequence:
      - action: light.turn_off
        target:
          entity_id:
          - light.bathroom_mirror_led
          - light.bathroom_downlights
  - choose:
    - conditions:
      - condition: template
        value_template: '{{ is_state(''binary_sensor.rmm_default_bedroom_occupancy'',''off'')
          and (now() - states.binary_sensor.rmm_default_bedroom_occupancy.last_changed).total_seconds()
          > 300 }}'
      - condition: template
        value_template: '{{ is_state(''light.bedroom_cupboard_light_3'',''on'') or
          is_state(''light.bedroom_cupboard_light_2'',''on'') or is_state(''light.bedlamps'',''on'')
          }}'
      sequence:
      - action: light.turn_off
        target:
          entity_id:
          - light.bedroom_cupboard_light_3
          - light.bedroom_cupboard_light_2
          - light.bedlamps
  - choose:
    - conditions:
      - condition: template
        value_template: '{{ is_state(''binary_sensor.rmm_default_lounge_occupancy'',''off'')
          and (now() - states.binary_sensor.rmm_default_lounge_occupancy.last_changed).total_seconds()
          > 300 }}'
      - condition: template
        value_template: '{{ is_state(''light.kitchen_console_candles'',''on'') }}'
      sequence:
      - action: light.turn_off
        target:
          entity_id:
          - light.kitchen_console_candles
  - choose:
    - conditions:
      - condition: template
        value_template: '{{ is_state(''binary_sensor.sofa_occupied_held'',''off'')
          and (now() - states.binary_sensor.sofa_occupied_held.last_changed).total_seconds()
          > 180 }}'
      - condition: template
        value_template: '{{ is_state(''light.couch'',''on'') }}'
      - condition: state
        entity_id: binary_sensor.rmm_default_lounge_occupancy
        state: 'off'
      sequence:
      - action: light.turn_off
        target:
          entity_id:
          - light.couch
  mode: single
```

</details>


Radars sometimes latch onto a "ghost". This one restarts just the radar module (not the ESP)
when it sees a physically impossible target, retries once, and only then asks me for help:

<details><summary><b>RMM: LD2450 ghost auto-recover (long)</b> (click to expand)</summary>

```yaml
- id: '1785400000024'
  alias: 'RMM: LD2450 ghost auto-recover'
  description: 'Restarts a stuck LD2450 radar module when it latches onto a phantom
    target. Three detectors: (A) a target parked within 500mm of the sensor face for
    20 min - physically implausible, this is the observed failure mode; (B) presence
    latched on for 6 h with the moving_target sensor never once flipping - a real
    sleeper twitches, a ghost does not; (C) presence reported while away mode is armed.
    Presses <slug>_radar_restart (restarts the LD2450 module only, not the ESP), retries
    once, then raises a persistent notification rather than looping. Clears RMM''s
    fused copy afterwards. 1 h cooldown per firing. Created by Claude 2026-07-25.'
  triggers:
  - trigger: numeric_state
    entity_id: sensor.ld2450_tracker_target_1_distance
    below: 500
    for: 00:20:00
    id: near_ld2450_tracker
  - trigger: state
    entity_id: binary_sensor.ld2450_tracker_presence
    to: 'on'
    for: 06:00:00
    id: stuck_ld2450_tracker
  - trigger: state
    entity_id: binary_sensor.ld2450_tracker_presence
    to: 'on'
    for: 00:10:00
    id: away_ld2450_tracker
  - trigger: numeric_state
    entity_id: sensor.ld2450_tracker_2_target_1_distance
    below: 500
    for: 00:20:00
    id: near_ld2450_tracker_2
  - trigger: state
    entity_id: binary_sensor.ld2450_tracker_2_presence
    to: 'on'
    for: 06:00:00
    id: stuck_ld2450_tracker_2
  - trigger: state
    entity_id: binary_sensor.ld2450_tracker_2_presence
    to: 'on'
    for: 00:10:00
    id: away_ld2450_tracker_2
  conditions: []
  actions:
  - choose:
    - conditions:
      - condition: trigger
        id: near_ld2450_tracker
      - condition: state
        entity_id: binary_sensor.ld2450_tracker_moving_target
        state: 'off'
      - condition: template
        value_template: '{{ this.attributes.last_triggered is none or (now() - this.attributes.last_triggered).total_seconds()
          > 3600 }}'
      sequence:
      - action: button.press
        target:
          entity_id: button.ld2450_tracker_radar_restart
        continue_on_error: true
      - delay: 00:00:45
      - if:
        - condition: state
          entity_id: binary_sensor.ld2450_tracker_presence
          state: 'on'
        then:
        - action: button.press
          target:
            entity_id: button.ld2450_tracker_radar_restart
          continue_on_error: true
        - delay: 00:00:45
        - if:
          - condition: state
            entity_id: binary_sensor.ld2450_tracker_presence
            state: 'on'
          then:
          - action: persistent_notification.create
            data:
              title: LD2450 ghost stuck
              message: bedroom_tracker still reports a target after two radar restarts.
                It may need an ESPHome reboot or power cycle.
              notification_id: ghost_ld2450_tracker
      - action: radar_map_manager.reset_tracking_history
        data: {}
        continue_on_error: true
    - conditions:
      - condition: trigger
        id: stuck_ld2450_tracker
      - condition: state
        entity_id: binary_sensor.ld2450_tracker_moving_target
        state: 'off'
      - condition: template
        value_template: '{{ this.attributes.last_triggered is none or (now() - this.attributes.last_triggered).total_seconds()
          > 3600 }}'
      - condition: template
        value_template: '{{ (now() - states.binary_sensor.ld2450_tracker_moving_target.last_changed).total_seconds()
          > 21600 }}'
      sequence:
      - action: button.press
        target:
          entity_id: button.ld2450_tracker_radar_restart
        continue_on_error: true
      - delay: 00:00:45
      - if:
        - condition: state
          entity_id: binary_sensor.ld2450_tracker_presence
          state: 'on'
        then:
        - action: button.press
          target:
            entity_id: button.ld2450_tracker_radar_restart
          continue_on_error: true
        - delay: 00:00:45
        - if:
          - condition: state
            entity_id: binary_sensor.ld2450_tracker_presence
            state: 'on'
          then:
          - action: persistent_notification.create
            data:
              title: LD2450 ghost stuck
              message: bedroom_tracker still reports a target after two radar restarts.
                It may need an ESPHome reboot or power cycle.
              notification_id: ghost_ld2450_tracker
      - action: radar_map_manager.reset_tracking_history
        data: {}
        continue_on_error: true
    - conditions:
      - condition: trigger
        id: away_ld2450_tracker
      - condition: template
        value_template: '{{ this.attributes.last_triggered is none or (now() - this.attributes.last_triggered).total_seconds()
          > 3600 }}'
      - condition: state
        entity_id: input_boolean.away_mode
        state: 'on'
      sequence:
      - action: button.press
        target:
          entity_id: button.ld2450_tracker_radar_restart
        continue_on_error: true
      - delay: 00:00:45
      - if:
        - condition: state
          entity_id: binary_sensor.ld2450_tracker_presence
          state: 'on'
        then:
        - action: button.press
          target:
            entity_id: button.ld2450_tracker_radar_restart
          continue_on_error: true
        - delay: 00:00:45
        - if:
          - condition: state
            entity_id: binary_sensor.ld2450_tracker_presence
            state: 'on'
          then:
          - action: persistent_notification.create
            data:
              title: LD2450 ghost stuck
              message: bedroom_tracker still reports a target after two radar restarts.
                It may need an ESPHome reboot or power cycle.
              notification_id: ghost_ld2450_tracker
      - action: radar_map_manager.reset_tracking_history
        data: {}
        continue_on_error: true
    - conditions:
      - condition: trigger
        id: near_ld2450_tracker_2
      - condition: state
        entity_id: binary_sensor.ld2450_tracker_2_moving_target
        state: 'off'
      - condition: template
        value_template: '{{ this.attributes.last_triggered is none or (now() - this.attributes.last_triggered).total_seconds()
          > 3600 }}'
      sequence:
      - action: button.press
        target:
          entity_id: button.ld2450_tracker_2_radar_restart
        continue_on_error: true
      - delay: 00:00:45
      - if:
        - condition: state
          entity_id: binary_sensor.ld2450_tracker_2_presence
          state: 'on'
        then:
        - action: button.press
          target:
            entity_id: button.ld2450_tracker_2_radar_restart
          continue_on_error: true
        - delay: 00:00:45
        - if:
          - condition: state
            entity_id: binary_sensor.ld2450_tracker_2_presence
            state: 'on'
          then:
          - action: persistent_notification.create
            data:
              title: LD2450 ghost stuck
              message: LD2450 Tracker 2 still reports a target after two radar restarts.
                It may need an ESPHome reboot or power cycle.
              notification_id: ghost_ld2450_tracker_2
      - action: radar_map_manager.reset_tracking_history
        data: {}
        continue_on_error: true
    - conditions:
      - condition: trigger
        id: stuck_ld2450_tracker_2
      - condition: state
        entity_id: binary_sensor.ld2450_tracker_2_moving_target
        state: 'off'
      - condition: template
        value_template: '{{ this.attributes.last_triggered is none or (now() - this.attributes.last_triggered).total_seconds()
          > 3600 }}'
      - condition: template
        value_template: '{{ (now() - states.binary_sensor.ld2450_tracker_2_moving_target.last_changed).total_seconds()
          > 21600 }}'
      sequence:
      - action: button.press
        target:
          entity_id: button.ld2450_tracker_2_radar_restart
        continue_on_error: true
      - delay: 00:00:45
      - if:
        - condition: state
          entity_id: binary_sensor.ld2450_tracker_2_presence
          state: 'on'
        then:
        - action: button.press
          target:
            entity_id: button.ld2450_tracker_2_radar_restart
          continue_on_error: true
        - delay: 00:00:45
        - if:
          - condition: state
            entity_id: binary_sensor.ld2450_tracker_2_presence
            state: 'on'
          then:
          - action: persistent_notification.create
            data:
              title: LD2450 ghost stuck
              message: LD2450 Tracker 2 still reports a target after two radar restarts.
                It may need an ESPHome reboot or power cycle.
              notification_id: ghost_ld2450_tracker_2
      - action: radar_map_manager.reset_tracking_history
        data: {}
        continue_on_error: true
    - conditions:
      - condition: trigger
        id: away_ld2450_tracker_2
      - condition: template
        value_template: '{{ this.attributes.last_triggered is none or (now() - this.attributes.last_triggered).total_seconds()
          > 3600 }}'
      - condition: state
        entity_id: input_boolean.away_mode
        state: 'on'
      sequence:
      - action: button.press
        target:
          entity_id: button.ld2450_tracker_2_radar_restart
        continue_on_error: true
      - delay: 00:00:45
      - if:
        - condition: state
          entity_id: binary_sensor.ld2450_tracker_2_presence
          state: 'on'
        then:
        - action: button.press
          target:
            entity_id: button.ld2450_tracker_2_radar_restart
          continue_on_error: true
        - delay: 00:00:45
        - if:
          - condition: state
            entity_id: binary_sensor.ld2450_tracker_2_presence
            state: 'on'
          then:
          - action: persistent_notification.create
            data:
              title: LD2450 ghost stuck
              message: LD2450 Tracker 2 still reports a target after two radar restarts.
                It may need an ESPHome reboot or power cycle.
              notification_id: ghost_ld2450_tracker_2
      - action: radar_map_manager.reset_tracking_history
        data: {}
        continue_on_error: true
  mode: queued
  max: 6
```

</details>


## "Am I home?": GPS and Bluetooth must agree

The house only treats me as *away* when the phone's GPS says I've left **and** the
Bluetooth proxies can't hear my phone. If GPS is unsure, I'm home. That one template sensor
is used by every away/home automation instead of `person.*`:

```yaml
# Presence (moved out of configuration.yaml 2026-10-05).
template:
  - binary_sensor:
      # --- Bae presence: BOTH trackers must agree before anything treats Bae as away.
      # on  = Companion app (GPS) says home, OR Bermuda BLE says home, OR the app's
      #       location is unknown/unavailable (never act "away" without a positive GPS away).
      # off = the Companion app positively says away AND Bermuda BLE does not say home.
      # delay_off swallows brief Bermuda reload blips. Used by every away/home
      # automation instead of person.bae. Added by Claude 2026-09-13.
      # 2026-11-22: BLE side is now the Pixel 10a's own beacon (Razr retired).
      - name: Bae home
        unique_id: bae_home_combined
        device_class: presence
        delay_off: "00:00:30"
        state: >-
          {%- set gps = states('device_tracker.pixel_10a') -%}
          {%- set ble = states('device_tracker.bermuda_pixel_10a_bermuda_tracker') -%}
          {{ not (gps not in ['home', 'unknown', 'unavailable'] and ble != 'home') }}
        attributes:
          companion_app: "{{ states('device_tracker.pixel_10a') }}"
          bermuda_ble: "{{ states('device_tracker.bermuda_pixel_10a_bermuda_tracker') }}"
```

On top of that, **away mode** (`input_boolean.away_mode`) only arms when the radars have
also been empty for 15 minutes, because a false "away" at 6 am while I'm asleep is worse
than arming a bit late. It disarms on *any* sign of life, because a false disarm is
harmless and a stuck away mode is not.

<details><summary><b>RMM: Away mode - arm</b> (click to expand)</summary>

```yaml
- id: '1785400000012'
  alias: 'RMM: Away mode - arm'
  description: Arms away mode ONLY when person.bae is not_home AND the Motorola Razr
    is not home AND every radar zone is clear. device_tracker.pixel_6a is deliberately
    EXCLUDED - I leaves that phone at home, so it is not a presence signal. Radar-empty
    alone is NOT sufficient; it loses very still people.
  triggers:
  - trigger: numeric_state
    entity_id: sensor.rmm_default_master
    below: 1
    for: 00:15:00
  - trigger: state
    entity_id: binary_sensor.bae_home
    to: 'off'
    for: 00:05:00
  conditions:
  - condition: state
    entity_id: input_boolean.guests_staying
    state: 'off'
    alias: Guest mode (Bae away) is off
  - alias: Auto-stay is off (party mode suspends this)
    condition: state
    entity_id: input_boolean.auto_stay
    state: 'off'
  - condition: state
    entity_id: input_boolean.away_mode
    state: 'off'
  - condition: state
    entity_id: binary_sensor.bae_home
    state: 'off'
  - condition: not
    conditions:
    - condition: state
      entity_id: device_tracker.pixel_10a
      state: home
  - condition: template
    value_template: '{{ expand(''binary_sensor.rmm_default_lounge_occupancy'',''binary_sensor.rmm_default_sofa_occupancy'',''binary_sensor.rmm_default_bed_occupancy'',''binary_sensor.rmm_default_bedroom_occupancy'',''binary_sensor.rmm_default_kitchen_occupancy'',''binary_sensor.rmm_default_office_occupancy'',''binary_sensor.rmm_default_bathroom_occupancy'',''binary_sensor.rmm_default_wardrobe_occupancy'')
      | selectattr(''state'',''eq'',''on'') | list | count == 0 }}'
  actions:
  - action: input_boolean.turn_on
    target:
      entity_id: input_boolean.away_mode
  - action: light.turn_off
    target:
      entity_id: all
  - action: media_player.media_pause
    target:
      entity_id: media_player.club
    continue_on_error: true
  - action: remote.turn_off
    target:
      entity_id: remote.the_club_tvv
    continue_on_error: true
  - action: media_player.turn_off
    target:
      entity_id: media_player.55_the_serif_3
    continue_on_error: true
  - action: climate.turn_off
    target:
      entity_id: climate.aircon
    continue_on_error: true
  - action: radar_map_manager.reset_tracking_history
    data: {}
    continue_on_error: true
  mode: single
```

</details>

<details><summary><b>RMM: Guest mode auto (2+ people → relax the automations)</b> (click to expand)</summary>

```yaml
- id: '1785400000016'
  alias: 'RMM: Guest mode auto'
  description: 2+ radar targets for 10 min -> guest mode on (suppresses sleep lights-off
    and Sonos-follow); back to <=1 for 30 min -> off. Created by Claude 2026-07-25.
  triggers:
  - trigger: numeric_state
    entity_id: sensor.rmm_default_master
    above: 1
    for: 00:10:00
    id: guests
  - trigger: numeric_state
    entity_id: sensor.rmm_default_master
    below: 2
    for: 00:30:00
    id: alone
  conditions: []
  actions:
  - choose:
    - conditions:
      - condition: trigger
        id: guests
      sequence:
      - action: input_boolean.turn_on
        target:
          entity_id: input_boolean.guest_mode
    - conditions:
      - condition: trigger
        id: alone
      sequence:
      - action: input_boolean.turn_off
        target:
          entity_id: input_boolean.guest_mode
  mode: restart
```

</details>


## Robots are people too (to a radar)
A robot vacuum looks exactly like a person to mmWave radar. Whenever a robot runs, the
radar-driven automations are paused and `binary_sensor.roborock_active` ("Robot vacuum
active") tells the intruder alert to ignore the radar. When it docks, a single script
switches everything back on:

<details><summary><b>radar_presence_resume</b> (click to expand)</summary>

```yaml
radar_presence_resume:
  alias: Radar presence · resume after a robot clean
  description: Turns back on the radar-driven automations that a robot-vacuum run
    pauses (the radars see a robot as a person). Used by Roborock · clean while away
    and the SL68 follow-up cleans. Added 2026-10-05.
  mode: single
  icon: mdi:radar
  sequence:
  - action: radar_map_manager.reset_tracking_history
    data: {}
    continue_on_error: true
  - delay: 00:00:20
  - action: automation.turn_on
    target:
      entity_id:
      - automation.rmm_kitchen_presence_light
      - automation.rmm_office_presence_light
      - automation.rmm_wardrobe_presence_light
      - automation.rmm_bedroom_presence_light
      - automation.rmm_bathroom_light_with_shower_hold
      - automation.rmm_couch_light
      - automation.rmm_console_candles
      - automation.rmm_night_path_to_bathroom
      - automation.rmm_fell_asleep_all_lights_off
      - automation.rmm_sonos_follows_you
      - automation.rmm_guest_mode_auto
      - automation.rmm_fall_alert
      - automation.rmm_ambient_day_lights
      - automation.rmm_ld2450_ghost_auto_recover
```

</details>


---
[← Back to the overview](../README.md)
