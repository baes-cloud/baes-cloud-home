# 5 · Voice: "hey Pikachu"

My wake word is **"hey Pikachu"**: a custom [openWakeWord](https://github.com/dscripka/openWakeWord)
model I trained.

**Why that phrase?** It's a genuinely good wake word: four syllables, an unusual sound
pattern ("hey pee-ka-choo") that almost never comes up in conversation, TV or music, so false
triggers are rare. And I like Pikachu. (The model file is spelled phonetically,
`hay_pee_kuh_choo.tflite`, which is how you get the pronunciation right in training.)

## Where it listens
- **An ESP32-S3-Box-3** in the kitchen, plus status LED feedback (yellow listening, green
  responding, a safety timeout).
- **The one remote** (both handsets). My remote app streams microphone audio to Home Assistant's openWakeWord
  add-on. It isn't battery-optimised: wake-word streaming is continuous (about 32 KB/s, roughly
  685 MB per 10 hours per remote), so it listens all the time while docked and only for
  **2 minutes after I lift a remote off its charger**.

Running the wake word in Home Assistant (rather than on each device) means the custom model
works on any microphone, including hardware that could never run it locally.

## The pipeline
| Stage | What I use |
|---|---|
| Wake word | openWakeWord add-on, custom "hey Pikachu" model |
| Speech-to-text / text-to-speech | Home Assistant Cloud |
| Understanding | **Local intents first** (instant and offline for commands), Google Gemini for questions and anything phrased oddly |

Commands like "turn off the kitchen" never leave the house. Questions about the house and
general questions go to Gemini, which can see and control only the entities I've exposed to Assist.

### My own phrases
A handful of custom sentences are matched locally and run straight away:

<details><summary><b>Astrion · voice shortcuts</b> (click to expand)</summary>

```yaml
- id: astrion_voice_shortcuts
  alias: Astrion · voice shortcuts
  description: Created for the Astrion remotes (D14). Handled locally by HA (the Piks
    pipeline prefers local intents), so these skip Gemini.
  triggers:
  - trigger: conversation
    command:
    - tv mode
    - watch tv
    - tv sound
    - tv audio
    - '[put the ]sonos on [the ]tv'
    - sonos to [the ]tv
    id: tv
  - trigger: conversation
    command:
    - goodnight
    - good night
    - everything off
    - all [the ]lights off
    - turn off all [the ]lights
    id: goodnight
  - trigger: conversation
    command:
    - night mode
    - night lights
    - night scene
    id: night
  - trigger: conversation
    command:
    - day mode
    - day lights
    - day scene
    id: day
  - trigger: conversation
    command:
    - blinds
    - '[toggle ][the ]blinds'
    - all [the ]blinds
    id: blinds
  - trigger: conversation
    command:
    - blinds half
    - half [the ]blinds
    - sheer[s] half
    - half [the ]sheer[s]
    id: blinds_half
  - trigger: conversation
    command:
    - dim [the ]lights
    - dim [the ]club
    - lights down
    id: dim
  actions:
  - choose:
    - conditions:
      - condition: trigger
        id: tv
      sequence:
      - action: media_player.select_source
        target:
          entity_id: media_player.club
        data:
          source: TV
      - variables:
          others: '{{ (state_attr(''media_player.club'',''group_members'') or [])
            | reject(''eq'',''media_player.club'') | list }}'
      - if:
        - condition: template
          value_template: '{{ others | count > 0 }}'
        then:
        - action: media_player.unjoin
          target:
            entity_id: '{{ others }}'
      - set_conversation_response: TV sound on the Sonos.
    - conditions:
      - condition: trigger
        id: goodnight
      sequence:
      - action: script.long_lights
      - set_conversation_response: Goodnight. Lights off.
    - conditions:
      - condition: trigger
        id: night
      sequence:
      - action: scene.turn_on
        target:
          entity_id: scene.night
      - set_conversation_response: Night lights.
    - conditions:
      - condition: trigger
        id: day
      sequence:
      - action: script.day
      - set_conversation_response: Day lights.
    - conditions:
      - condition: trigger
        id: blinds
      sequence:
      - action: script.club_blinds_all
      - set_conversation_response: Blinds.
    - conditions:
      - condition: trigger
        id: blinds_half
      sequence:
      - action: cover.set_cover_position
        target:
          entity_id: cover.club_sheer_blinds
        data:
          position: 50
      - set_conversation_response: Sheers to half.
    - conditions:
      - condition: trigger
        id: dim
      sequence:
      - action: light.turn_on
        target:
          entity_id: '{{ area_entities(''club'') | select(''match'',''light\\.'')
            | select(''is_state'',''on'') | list }}'
        data:
          brightness_pct: 30
          transition: 2
      - set_conversation_response: Dimmed.
  mode: parallel
```

</details>


---
[← Back to the overview](../README.md)
