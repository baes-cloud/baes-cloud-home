# 10 · Lessons learned

1. **PIR to switch on, radar to hold, a sweep to clean up.** Motion sensors are fast but forget
   still people. Radar remembers them but takes a moment. A periodic sweep catches anything left on.
2. **To a radar, robots and washing machines are people.** Exclude the washer, and pause the
   presence automations whenever a robot is running.
3. **"Away" should need everything to agree; "home" should need almost nothing.** GPS *and*
   Bluetooth *and* empty radars to leave; any single sign of life to come back. A false "away"
   at 6 am (it happened once) is much worse than arming late.
4. **Bluetooth alone isn't proof.** Beacons can be spoofed and phones put them to sleep, so the
   backup auto-unlock only fires after a real absence with GPS agreeing.
5. **Detect manual overrides with `context.user_id`.** `parent_id` is empty for timed automations too.
6. **Reloading automations wipes pending `for:` timers.** Design for it: sweeps and safety nets.
7. **Keep things that must never fail apart.** The alarm and its lights are separate automations,
   and notifications are fire-and-forget, so one failure can't take down the rest.
8. **Radar modules occasionally latch.** Auto-restart the module, retry once, then notify. Never loop.
9. **Measure what you record, including attribute-only updates.** Bluetooth distances, raw radar
   geometry and a TV's playback position were about 85% of all database writes.
10. **Watch what writes to flash.** A voice add-on rewrote a 300 MB index after every restart and
    froze the disk for minutes. Removing it, and trimming a cloud integration from 18 devices to
    the 2 I use, made restarts much faster.
11. **Failover needs a two-sided check and should never pause failback.** Two live Home Assistants
    double-fire every automation. Also: strip Supervisor-only config when syncing to a container
    install, and run a real drill.
12. **Put the interface where you are.** Remotes, knobs, a wall board and the phone all show
    the same state, so I never need to open a dashboard.

---
[← Back to the overview](../README.md)
