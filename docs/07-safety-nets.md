# 7 · Safety nets

The house tells me when something is wrong, and it fixes the routine failures itself.

| What | How |
|---|---|
| **Water leak** by the washing machine | Push + persistent notification, then every ~3 min an announcement and alarm tone on every Sonos at a raised volume. When it's dry it stops, restores every speaker's original volume and sends an all-clear |
| **Severe weather** | Each new Bureau of Meteorology warning for my area is pushed once; major ones are high-priority |
| **Robot vacuum** | Errors, full or empty tanks, consumables due (with a "Done" button that resets the counter) |
| **Radar ghosts / latches** | Restarts the radar module, retries once, then asks for help |
| **Lights stranded on** | 5-minute zone sweep |
| **Sonos speaker lost** | HA's Sonos integration can give up after a network blip; reloads it (at most hourly) |
| **Remote batteries** | Warns if a remote is on the dock but not charging, or off it and low |
| **The Pi itself** | CPU temperature, disk and memory alerts (System Monitor) |
| **Failover** | Alerts if the watchdog stops, the hold switch is left on, or the standby is unreachable or its sync is stale |
| **News digest job** | Alerts if curation fails twice in a row or the digest goes stale |

<details><summary><b>Bathroom leak alarm</b> (click to expand)</summary>

```yaml
- id: '1786000000001'
  alias: Bathroom leak alarm
  description: 'IKEA BADRING leak sensor next to the washing machine. On leak: immediate
    push to the Razr + persistent notification, snapshot every Sonos speaker''s current
    volume into scene.leak_alarm_volume_snapshot, then every ~3 min while the sensor
    stays wet - raise volume and speak an alert + alarm tone on every Sonos speaker
    currently on/paused/idle (offline speakers skipped automatically). The moment
    the sensor reports dry: stop, restore every speaker''s original volume from the
    snapshot, and send an all-clear push + TTS. Created by Claude 2026-07-27/08-12.'
  triggers:
  - trigger: state
    entity_id: binary_sensor.0x0c2a6ffffe605def_water_leak
    to: 'on'
  conditions: []
  actions:
  - action: script.turn_on
    target:
      entity_id: script.notify_bae
    data:
      variables:
        title: Water leak detected!
        message: Bathroom leak sensor (washing machine) has detected water.
        data:
          ttl: 0
          priority: high
          channel: alarm_stream
    continue_on_error: true
  - action: persistent_notification.create
    data:
      title: Water leak
      message: Water leak detected in the bathroom, near the washing machine. Check
        it now.
      notification_id: bathroom_leak
  - variables:
      leak_speakers: '{{ ["media_player.club", "media_player.bathroom_sonos", "media_player.bathroom_2",
        "media_player.bedroom_sonos", "media_player.office_sonos", "media_player.living_room_sonos"]
        | select(''is_state'',[''on'',''paused'',''idle'']) | list }}'
  - action: scene.create
    data:
      scene_id: leak_alarm_volume_snapshot
      snapshot_entities: '{{ leak_speakers }}'
    continue_on_error: true
  - repeat:
      while:
      - condition: state
        entity_id: binary_sensor.0x0c2a6ffffe605def_water_leak
        state: 'on'
      sequence:
      - variables:
          leak_speakers: '{{ ["media_player.club", "media_player.bathroom_sonos",
            "media_player.bathroom_2", "media_player.bedroom_sonos", "media_player.office_sonos",
            "media_player.living_room_sonos"] | select(''is_state'',[''on'',''paused'',''idle''])
            | list }}'
      - action: media_player.volume_set
        target:
          entity_id: '{{ leak_speakers }}'
        data:
          volume_level: 0.55
        continue_on_error: true
      - action: tts.speak
        target:
          entity_id: tts.home_assistant_cloud
        data:
          media_player_entity_id: '{{ leak_speakers }}'
          cache: true
          message: Beep. Beep. Beep.
        continue_on_error: true
      - delay: 00:00:04
      - action: tts.speak
        target:
          entity_id: tts.home_assistant_cloud
        data:
          media_player_entity_id: '{{ leak_speakers }}'
          cache: true
          message: Water leak detected in the bathroom, near the washing machine.
            Check it now.
        continue_on_error: true
      - delay: 00:00:03
      - action: tts.speak
        target:
          entity_id: tts.home_assistant_cloud
        data:
          media_player_entity_id: '{{ leak_speakers }}'
          cache: true
          message: Beep. Beep. Beep.
        continue_on_error: true
      - delay: 00:03:00
  - action: scene.turn_on
    target:
      entity_id: scene.leak_alarm_volume_snapshot
    continue_on_error: true
  - action: script.turn_on
    target:
      entity_id: script.notify_bae
    data:
      variables:
        title: Leak cleared
        message: The bathroom leak sensor is now dry.
        data:
          ttl: 0
          priority: normal
          channel: alarm_stream
    continue_on_error: true
  - action: persistent_notification.dismiss
    data:
      notification_id: bathroom_leak
  - variables:
      leak_speakers: '{{ ["media_player.club", "media_player.bathroom_sonos", "media_player.bathroom_2",
        "media_player.bedroom_sonos", "media_player.office_sonos", "media_player.living_room_sonos"]
        | select(''is_state'',[''on'',''paused'',''idle'']) | list }}'
  - action: tts.speak
    target:
      entity_id: tts.home_assistant_cloud
    data:
      media_player_entity_id: '{{ leak_speakers }}'
      cache: true
      message: The bathroom leak sensor has cleared. All good.
    continue_on_error: true
  mode: restart
```

</details>


---
[← Back to the overview](../README.md)
