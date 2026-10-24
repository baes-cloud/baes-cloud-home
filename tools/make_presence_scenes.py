#!/usr/bin/env python3
"""Render the presence scene GIFs (illustrative mock-ups, not recordings).

Usage: python3 tools/make_presence_scenes.py   (run from the repo root; needs Pillow + ffmpeg)
Reads images/rmm/floorplan.png and config/rmm/radar_map_manager.json and writes
images/rmm/presence-{morning,evening-guest,party,away-robot}.gif.

Same look as make_rmm_gif.py, but with several people (and robots) on the map at once,
at different times of day. Positions are percent of the plan, like RMM's own zones.
"""
import json, math, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

MAP = 520            # rendered floorplan size (px)
PANEL = 300          # side panel width (px)
FPS = 10
BG = (27, 36, 45)          # #1B242D
PANEL2 = (45, 60, 75)      # #2D3C4B
LINE = (58, 74, 88)        # #3A4A58
TEAL = (140, 189, 181)     # #8CBDB5 lifted Hailstorm (accent)
SEL = (79, 114, 109)       # #4F726D Gunmetal (selected)
AMBER = (242, 190, 92)     # lights 'on' stay warm amber
DOLL = (230, 188, 182)     # #E6BCB6 Baby Doll
DOLL_INK = (74, 42, 38)    # #4A2A26 text on Baby Doll
INK = (241, 236, 234)      # #F1ECEA
MUTE = (169, 186, 182)     # #A9BAB6
BAD = (227, 123, 123)      # #E37B7B

def font(size, bold=False, display=False):
    name = 'IBMPlexSans-Bold.ttf' if display else ('IBMPlexSans-SemiBold.ttf' if bold else 'IBMPlexSans-Regular.ttf')
    return ImageFont.truetype(os.path.join(os.path.dirname(__file__), 'fonts', name), size)

F_T, F_B, F_S, F_L, F_XS = font(21, display=True), font(15, True), font(14), font(12, True), font(11, True)
F_CLOCK = font(30, display=True)
rmm = json.load(open('config/rmm/radar_map_manager.json'))
base = Image.open('images/rmm/floorplan.png').convert('RGB').resize((MAP, MAP), Image.LANCZOS)
bright = ImageEnhance.Brightness(base).enhance(1.15)

def P(x, y):  # percent -> px
    return (x / 100 * MAP, y / 100 * MAP)

ZONES = {z['name'].lower(): [P(*p) for p in z['points']] for z in rmm['zones']['include_zones']}
EXCL = [[P(*p) for p in z['points']] for z in rmm['zones']['exclude_zones'] if z['name'] == 'washer/dryer']
RADARS = [P(r['layout']['origin_x'], r['layout']['origin_y']) for r in rmm['radars'].values()]

LIGHTS = {  # illustrative positions (percent of the plan)
    'Downlights': (38, 12), 'Couch': (33, 29), 'TV art': (47, 6), 'Art pendants': (71, 22),
    'Kitchen': (68, 46), 'Bedroom': (24, 61), 'Bed lamps': (29, 89), 'Bathroom': (52, 72),
    'Mirror LED': (49, 85), 'Wardrobe': (74, 70), 'Office': (89, 72),
}
# Time of day -> how bright the plan is before lights are added
TOD = {'day': 1.0, 'morning': 0.62, 'dusk': 0.5, 'night': 0.3}

# Places and doorways (from the owner's marked-up plan)
BED, BED2 = (27.9, 74.0), (31.5, 76.0)
SOFA, SOFA2 = (30.0, 35.0), (41.0, 35.5)
SHOWER, BASIN = (59.5, 64.0), (49.0, 82.0)
BENCH, TABLE = (70.0, 46.0), (70.0, 31.0)
FRONT_DOOR, OUTSIDE = (93.0, 12.0), (99.5, 12.0)
DOOR_ENSUITE = (41.7, 76.0); DOOR_BATH_WARDROBE = (64.6, 76.5)
DOOR_WARDROBE_KITCHEN = (89.7, 50.0); DOOR_BEDROOM = (11.7, 52.8)
DOCK, SL68_DOCK = (94.5, 45.0), (6.0, 47.0)

def inside(pt, poly):
    x, y = pt; c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1:
            c = not c
    return c

def path(points, steps):
    pts = [P(*p) for p in points]
    if len(pts) == 1:
        return pts * steps
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg); out = []
    for k in range(steps):
        d = total * k / max(steps - 1, 1)
        for i, s in enumerate(seg):
            if d <= s or i == len(seg) - 1:
                t = min(d / s, 1) if s else 0
                out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t))
                break
            d -= s
    return out

def wrap(text, width, f):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if f.getlength(t) > width and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    return lines + [cur] if cur else lines

def chip(d, x, y, text, fill, ink):
    w = F_XS.getlength(text) + 16
    d.rounded_rectangle([x, y, x + w, y + 20], radius=10, fill=fill)
    d.text((x + 8, y + 3), text, fill=ink, font=F_XS)
    return w

MODE_STYLE = {  # chip colours: warm for attention, red only for alerts
    'Alarm ringing': (AMBER, BG), 'Guest mode': (SEL, INK), 'Party mode': (DOLL, DOLL_INK),
    'Away': (LINE, INK), 'Radar paused': (DOLL, DOLL_INK), 'Door locked': (LINE, INK),
    'Door unlocked': (DOLL, DOLL_INK), 'Reminder': (AMBER, BG),
}

class Scene:
    """A short film: actors move through beats; each beat renders frames."""
    def __init__(self, title, show_lights):
        self.title, self.show_lights, self.frames = title, show_lights, []
        self.pos, self.kind, self.trail = {}, {}, {}

    def enter(self, name, kind, at):
        self.pos[name], self.kind[name], self.trail[name] = P(*at), kind, []

    def leave(self, name):
        for t in (self.pos, self.kind, self.trail):
            t.pop(name, None)

    def beat(self, n, clock, caption, tod='day', lights=(), moves=None, modes=(), music='', holds=(), alert=None):
        moves = moves or {}
        tracks = {a: path(pts, n) for a, pts in moves.items()}
        for i in range(n):
            for a, tr in tracks.items():
                if a in self.pos:
                    self.pos[a] = tr[i]
                    self.trail[a] = (self.trail[a] + [tr[i]])[-12:]
            for a in self.pos:
                if a not in tracks and self.trail[a]:
                    self.trail[a] = self.trail[a][1:]   # a still person's trail fades out
            self.frames.append(self.render(clock, caption, tod, set(lights), modes, music, holds, alert))

    def render(self, clock, caption, tod, lights, modes, music, holds, alert):
        night = TOD[tod] < 0.7
        img = Image.new('RGB', (MAP + PANEL, MAP), BG)
        plan = ImageEnhance.Brightness(base).enhance(TOD[tod])
        glow = Image.new('L', (MAP, MAP), 0); gd = ImageDraw.Draw(glow)
        for name in lights:
            x, y = P(*LIGHTS[name]); r = 95
            gd.ellipse([x - r, y - r, x + r, y + r], fill=235 if night else 110)
        plan = Image.composite(bright, plan, glow.filter(ImageFilter.GaussianBlur(36)))
        ov = Image.new('RGBA', (MAP, MAP), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        # a docked robot isn't a target; a moving one is (its trail shows it moved recently)
        tracked = [a for a, k in self.kind.items() if k != 'untracked' and (k != 'robot' or self.trail[a])]
        occupied = [n for n, poly in ZONES.items() if any(inside(self.pos[a], poly) for a in tracked)]
        occupied += [h for h in holds if h not in occupied]
        for n, poly in ZONES.items():
            on = n in occupied
            od.polygon(poly, fill=TEAL + (85 if on else 18,), outline=TEAL + (150 if on else 55,))
        for poly in EXCL:
            od.polygon(poly, fill=BAD + (40,), outline=BAD + (120,))
        for rx, ry in RADARS:
            od.ellipse([rx - 6, ry - 6, rx + 6, ry + 6], fill=DOLL + (240,))
        for name in self.show_lights:
            x, y = P(*LIGHTS[name]); on = name in lights
            od.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(AMBER + (255,)) if on else (90, 90, 90, 190), outline=(255, 255, 255, 170))
        for a, tr in self.trail.items():
            col = DOLL if self.kind[a] == 'guest' else TEAL
            if self.kind[a] in ('robot', 'untracked'):
                continue
            for i, (tx, ty) in enumerate(tr):
                od.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=col + (int(30 + 140 * (i + 1) / len(tr)),))
        for a, (tx, ty) in self.pos.items():
            k = self.kind[a]
            if k == 'untracked':   # a person the radar can't take on (3 targets per radar)
                od.ellipse([tx - 11, ty - 11, tx + 11, ty + 11], outline=MUTE + (200,), width=2)
                continue
            if k == 'robot':       # a robot: the radar sees a target, the automations ignore it
                od.ellipse([tx - 17, ty - 17, tx + 17, ty + 17], outline=DOLL + (220,), width=2)
                od.rounded_rectangle([tx - 10, ty - 10, tx + 10, ty + 10], radius=10, fill=(206, 214, 212, 255), outline=BG + (255,), width=2)
                od.ellipse([tx - 3, ty - 7, tx + 3, ty - 1], fill=BG + (255,))
                continue
            col = DOLL if k == 'guest' else TEAL
            od.ellipse([tx - 12, ty - 12, tx + 12, ty + 12], fill=col + (245,), outline=INK + (255,), width=2)
        img.paste(Image.alpha_composite(plan.convert('RGBA'), ov).convert('RGB'), (0, 0))
        d = ImageDraw.Draw(img)
        for a, (tx, ty) in self.pos.items():  # labels above the dots
            label = {'me': 'me', 'guest': 'guest', 'robot': a, 'untracked': ''}[self.kind[a]]
            if label:
                w = F_XS.getlength(label)
                d.text((tx - w / 2, ty - 31), label, fill=INK, font=F_XS, stroke_width=3, stroke_fill=BG)
        if alert:
            w = F_B.getlength(alert) + 28
            d.rounded_rectangle([(MAP - w) / 2, MAP - 52, (MAP + w) / 2, MAP - 16], radius=12, fill=PANEL2, outline=AMBER, width=2)
            d.text(((MAP - w) / 2 + 14, MAP - 44), alert, fill=INK, font=F_B)
        # side panel
        x0 = MAP + 18
        d.text((x0, 14), self.title, fill=INK, font=F_T)
        d.text((x0, 44), clock, fill=AMBER if night else TEAL, font=F_CLOCK)
        n = sum(1 for a in tracked)
        d.text((x0, 92), 'ON RADAR', fill=MUTE, font=F_L)
        y = 108
        for line in wrap(f'{n} target{"s" if n != 1 else ""}' + (f' · {", ".join(z.title() for z in occupied)}' if occupied else ''), PANEL - 36, F_B):
            d.text((x0, y), line, fill=TEAL, font=F_B); y += 20
        y += 10
        if modes:
            x = x0
            for m in modes:
                fill, ink = MODE_STYLE.get(m, (LINE, INK))
                w = F_XS.getlength(m) + 16
                if x + w > MAP + PANEL - 14:
                    x, y = x0, y + 26
                x += chip(d, x, y, m, fill, ink) + 6
            y += 32
        d.text((x0, y), 'LIGHTS', fill=MUTE, font=F_L); y += 18
        for i, name in enumerate(self.show_lights):   # two columns
            cx, cy = x0 + (i % 2) * 136, y + (i // 2) * 20
            on = name in lights
            d.ellipse([cx, cy + 4, cx + 10, cy + 14], fill=AMBER if on else LINE)
            d.text((cx + 16, cy), name, fill=INK if on else MUTE, font=F_S)
        y += ((len(self.show_lights) + 1) // 2) * 20 + 10
        if music:
            d.text((x0, y), 'MUSIC', fill=MUTE, font=F_L); y += 18
            for line in wrap(music, PANEL - 36, F_S):
                d.text((x0, y), line, fill=INK, font=F_S); y += 19
            y += 8
        for line in wrap(caption, PANEL - 36, F_S):
            d.text((x0, y), line, fill=INK, font=F_S); y += 19
        d.text((x0, MAP - 24), 'Illustrative mock-up · RMM + LD2450', fill=MUTE, font=font(11))
        return img

    def save(self, out):
        with tempfile.TemporaryDirectory() as tmp:
            for i, f in enumerate(self.frames):
                f.save(f'{tmp}/f{i:04d}.png')
            pal = f'{tmp}/pal.png'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', f'{tmp}/f%04d.png',
                            '-vf', 'palettegen=stats_mode=diff:max_colors=200', pal], check=True)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', f'{tmp}/f%04d.png', '-i', pal,
                            '-lavfi', 'paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle', '-loop', '0', out], check=True)
        print(f'{out}: {len(self.frames)} frames, {os.path.getsize(out) // 1024} KB')

# --- 1. A weekday morning, on my own ---------------------------------------------------
s = Scene('Weekday morning', ['Bedroom', 'Bed lamps', 'Downlights', 'Kitchen', 'Bathroom', 'Mirror LED'])
s.enter('me', 'me', BED)
s.beat(12, '05:45', 'Asleep. My first shift starts at 06:55, so the alarm is set for 70 minutes before it, straight from my work calendar.', tod='night', holds=['bed'], modes=['Door locked'])
s.beat(22, '05:45', 'Alarm 1: every speaker plays, the bedroom lights fade up, and the alarm pops up on the remote, the knob and my phone.',
       tod='night', lights=['Bed lamps', 'Bedroom'], holds=['bed'], modes=['Alarm ringing', 'Door locked'], music='Every speaker: my alarm', alert='Alarm 05:45 · hold to stop')
s.beat(20, '05:52', 'First time out of bed on a weekday: the whole flat fades to the morning scene and the TV opens the ABC News live stream.',
       tod='morning', lights=['Bedroom', 'Bed lamps', 'Downlights', 'Kitchen'], moves={'me': [BED, (34, 75.5), (39, 76), DOOR_ENSUITE, (45, 75), BASIN]},
       modes=['Door locked'], music='Lounge: TV news')
s.beat(18, '05:53', 'First bathroom visit: the bathroom speaker reads today\'s calendar, then the news digest.',
       tod='morning', lights=['Bedroom', 'Downlights', 'Kitchen', 'Bathroom', 'Mirror LED'], moves={'me': [BASIN, (54, 72), SHOWER]},
       modes=['Door locked'], music='Bathroom: calendar, then the news digest')
s.beat(22, '06:01', 'Standing still in the shower: the shower is a stationary zone, so the light holds. A motion sensor would have left me in the dark.',
       tod='morning', lights=['Downlights', 'Kitchen', 'Bathroom', 'Mirror LED'], holds=['bathroom'], modes=['Door locked'], music='Bathroom: news digest')
s.beat(30, '06:09', 'Out through the wardrobe to the kitchen. The bathroom joins the lounge, so the news carries on where I am.',
       tod='morning', lights=['Downlights', 'Kitchen', 'Bathroom'], moves={'me': [SHOWER, (60, 76), DOOR_BATH_WARDROBE, (70, 75), (80, 64), (88, 55), DOOR_WARDROBE_KITCHEN, (86, 47), BENCH]},
       modes=['Door locked'], music='Lounge + bathroom: TV news')
s.beat(20, '06:14', 'Coffee at the bench. Standing still again, and the kitchen holds. The bathroom light goes off on its own once that zone has been empty long enough.',
       tod='morning', lights=['Downlights', 'Kitchen'], modes=['Door locked'], music='Lounge: TV news')
s.beat(22, '06:20', 'Out the front door. It locks 30 seconds after it closes. When GPS and Bluetooth both agree I\'ve gone, lights and media switch off.',
       tod='morning', lights=['Downlights', 'Kitchen'], moves={'me': [BENCH, (82, 30), FRONT_DOOR, OUTSIDE]}, modes=['Door unlocked'], music='Lounge: TV news')
s.leave('me')
s.beat(22, '06:26', 'Five minutes gone and every radar zone empty: lights and media off. Away mode arms after 15. Nothing to remember on the way out.',
       tod='morning', modes=['Door locked', 'Away'])
s.save('images/rmm/presence-morning.gif')

# --- 2. An evening with a friend over ---------------------------------------------------
s = Scene('Evening, two people', ['Downlights', 'Couch', 'TV art', 'Art pendants', 'Bathroom', 'Mirror LED'])
EVE = ['Couch', 'TV art', 'Art pendants']
s.enter('me', 'me', SOFA)
s.beat(12, '19:30', 'Sunset scene on, me on the sofa.', tod='dusk', lights=EVE, holds=['sofa'], modes=['Door locked'], music='Lounge: Glitterbox')
s.enter('guest', 'guest', OUTSIDE)
s.beat(26, '19:31', 'A friend arrives. The radar picks up a second person at the front door. The door locks behind them 30 seconds after it closes.',
       tod='dusk', lights=EVE, moves={'guest': [OUTSIDE, FRONT_DOOR, (80, 26), (60, 38), SOFA2]}, holds=['sofa'], modes=['Door unlocked'], music='Lounge: Glitterbox')
s.beat(22, '19:41', 'Two people on the radar for 10 minutes: guest mode switches itself on. Nobody touches a thing.',
       tod='dusk', lights=EVE, holds=['sofa'], modes=['Guest mode', 'Door locked'], music='Lounge: Glitterbox')
s.beat(26, '22:40', 'Deep in a film, both of us dead still. On my own, 45 quiet minutes on the sofa at night means I fell asleep and everything turns off. Guest mode holds that back.',
       tod='night', lights=EVE, holds=['sofa'], modes=['Guest mode', 'Door locked'], music='Lounge: TV')
s.beat(26, '22:52', 'I duck to the bathroom: its light comes on as normal. The music stays in the lounge, because following me would leave my friend sitting in silence.',
       tod='night', lights=EVE + ['Bathroom', 'Mirror LED'], moves={'me': [SOFA, (22, 46), DOOR_BEDROOM, (16, 64), (34, 72), DOOR_ENSUITE, BASIN]}, modes=['Guest mode', 'Door locked'], music='Lounge: TV (not following me)')
s.beat(26, '22:56', 'Back on the sofa. The bathroom light goes off by itself a few minutes later.',
       tod='night', lights=EVE, moves={'me': [BASIN, DOOR_ENSUITE, (34, 72), (16, 64), DOOR_BEDROOM, (22, 46), SOFA]}, modes=['Guest mode', 'Door locked'], music='Lounge: TV')
s.beat(24, '23:20', 'My friend heads home.', tod='night', lights=EVE, moves={'guest': [SOFA2, (60, 38), (80, 26), FRONT_DOOR, OUTSIDE]}, holds=['sofa'], modes=['Guest mode', 'Door unlocked'], music='Lounge: TV')
s.leave('guest')
s.beat(18, '23:50', 'One person for 30 minutes: guest mode switches itself off again. Normal rules are back.', tod='night', lights=EVE, holds=['sofa'], modes=['Door locked'], music='Lounge: TV')
s.beat(18, '00:35', 'And when I do nod off on the sofa, 45 still minutes later...', tod='night', lights=EVE, holds=['sofa'], modes=['Door locked'], music='Lounge: TV')
s.beat(22, '00:35', '...every light in the flat goes off. The house knows when I\'m sleeping.', tod='night', holds=['sofa'], modes=['Door locked'], music='Lounge: TV')
s.save('images/rmm/presence-evening-guest.gif')

# --- 3. A party: more people than the radars can count ----------------------------------
PARTY = ['Downlights', 'Couch', 'TV art', 'Art pendants', 'Bedroom', 'Bathroom', 'Mirror LED', 'Office']
PL = ['Couch', 'TV art', 'Art pendants', 'Downlights']
s = Scene('Party night', PARTY)
s.enter('me', 'me', (64, 40))
s.beat(14, '20:55', 'Friends due any minute. One switch on the remote turns on party mode.', tod='night', lights=PL, modes=['Door locked'], music='Lounge: Glitterbox')
s.beat(22, '20:56', 'Party mode pauses everything that would be annoying with a crowd: lights reacting to people, scene changes, the door locking itself and announcing it, away mode and the robots.',
       tod='night', lights=PL, modes=['Party mode', 'Door locked'], music='Lounge: Glitterbox')
for i, (spot, via) in enumerate([((44, 30), (66, 30)), ((24, 30), (55, 24)), ((76, 32), (82, 24)), ((70, 44), (78, 36)), ((36, 40), (60, 34))]):
    s.enter(f'g{i}', 'guest' if i < 2 else 'untracked', OUTSIDE)
s.beat(36, '21:20', 'Everyone arrives. The door stays unlocked and quiet, no announcement every time it opens.',
       tod='night', lights=PL, modes=['Party mode', 'Door unlocked'], music='Lounge: Glitterbox',
       moves={'g0': [OUTSIDE, FRONT_DOOR, (66, 30), (44, 30)], 'g1': [OUTSIDE, FRONT_DOOR, (55, 24), (24, 30)],
              'g2': [OUTSIDE, FRONT_DOOR, (82, 24), (76, 32)], 'g3': [OUTSIDE, FRONT_DOOR, (78, 36), (70, 44)],
              'g4': [OUTSIDE, FRONT_DOOR, (60, 34), (36, 40)]})
s.beat(24, '21:40', 'Six people in the lounge and kitchen, but each radar tracks at most three targets. The grey rings are people it can\'t take on. Party mode is a switch, so it doesn\'t need a count.',
       tod='night', lights=PL, modes=['Party mode', 'Door unlocked'], music='Lounge: Glitterbox',
       moves={'me': [(64, 40), (62, 36)], 'g0': [(44, 30), (46, 28)], 'g2': [(76, 32), (74, 30)]})
s.kind['g2'] = 'guest'   # with one guest gone to the bathroom, the lounge radar picks up someone it couldn't track before
s.beat(30, '22:10', 'Someone finds the bathroom: its light still comes on, because that one keeps working in party mode. The bedroom on the way stays dark: room lights don\'t react in party mode.',
       tod='night', lights=PL + ['Bathroom', 'Mirror LED'], modes=['Party mode', 'Door unlocked'], music='Lounge: Glitterbox',
       moves={'g1': [(24, 30), (18, 44), DOOR_BEDROOM, (16, 64), (34, 72), DOOR_ENSUITE, BASIN], 'g3': [(70, 44), (66, 40)]})
s.beat(24, '22:40', 'I take the music into the office to show someone a playlist. Follow-me also keeps working in party mode, so the office speaker joins in.',
       tod='night', lights=PL + ['Bathroom', 'Mirror LED'], modes=['Party mode', 'Door unlocked'], music='Lounge + office: Glitterbox',
       moves={'me': [(62, 36), (78, 44), (86, 47), DOOR_WARDROBE_KITCHEN, (88, 62)]})
for a in ['g0', 'g1', 'g2', 'g3', 'g4']:
    s.leave(a)
s.leave('me')
s.beat(26, '10:00', 'The morning after. Everyone\'s gone, but party mode is still on, so at 10 am the house nudges me to switch it off.',
       tod='day', modes=['Party mode', 'Reminder'], alert='Party mode is still on · Turn off')
s.save('images/rmm/presence-party.gif')

# --- 4. Out for the day: the robots clean, then I come home -----------------------------
s = Scene('Out for the day', ['Downlights', 'Kitchen', 'Couch', 'Bedroom', 'Office', 'Bathroom'])
s.enter('me', 'me', BENCH)
s.enter('roborock', 'robot', DOCK)
s.beat(22, '09:20', 'Heading out the front door.', tod='day', moves={'me': [BENCH, (82, 30), FRONT_DOOR, OUTSIDE]}, lights=['Kitchen'], modes=['Door unlocked'])
s.leave('me')
s.beat(18, '09:35', 'GPS and Bluetooth both agree I\'m away, and every radar zone has been empty for 15 minutes: away mode arms. Door locked, lights off.',
       tod='day', modes=['Away', 'Door locked'])
lanes = [DOCK, (88, 48), (56, 48), (56, 40), (88, 40), (84, 30), (56, 30), (54, 46), (48, 44), (5, 44), (5, 18), (14, 12), (48, 12), (48, 20), (14, 20)]
s.beat(56, '09:45', 'Ten minutes later the Roborock heads out. The radar sees it as a person, so the radar automations pause and the intruder alert ignores the radar while a robot is running.',
       tod='day', moves={'roborock': lanes}, modes=['Away', 'Door locked', 'Radar paused'])
s.beat(26, '11:05', 'The Roborock finished cleanly, so it docks and my old SL68 does a final sweep.',
       tod='day', moves={'roborock': [(14, 20), (30, 46), (60, 48), DOCK]}, modes=['Away', 'Door locked', 'Radar paused'])
s.enter('SL68', 'robot', SL68_DOCK)
s.beat(30, '11:40', 'SL68 doing its lap of the lounge.', tod='day', moves={'SL68': [SL68_DOCK, (10, 30), (20, 14), (50, 16), (52, 44), (30, 46)]}, modes=['Away', 'Door locked', 'Radar paused'])
s.beat(22, '14:10', 'I\'m within 1 km and heading this way: whichever robot is still out goes back to its dock.',
       tod='day', moves={'SL68': [(30, 46), (14, 47), SL68_DOCK]}, modes=['Away', 'Door locked', 'Radar paused'])
s.leave('SL68')
s.beat(12, '14:14', 'Both robots docked, so the radar automations switch back on.', tod='day', modes=['Away', 'Door locked'])
s.enter('me', 'me', OUTSIDE)
s.beat(24, '14:16', 'A fingerprint on the keypad lets me in. Away mode turns off, and the kitchen light is already on as I walk in.',
       tod='day', moves={'me': [OUTSIDE, FRONT_DOOR, (80, 30), BENCH]}, lights=['Kitchen'], modes=['Door unlocked'])
s.beat(18, '14:17', 'The door locks itself 30 seconds after it closes. Back to normal.', tod='day', lights=['Kitchen'], modes=['Door locked'])
s.save('images/rmm/presence-away-robot.gif')
