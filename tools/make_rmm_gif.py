#!/usr/bin/env python3
"""Render the RMM presence demo GIF (illustrative mock-up, not a recording).

Usage: python3 tools/make_rmm_gif.py   (run from the repo root; needs Pillow + ffmpeg)
Reads images/rmm/floorplan.png and config/rmm/radar_map_manager.json and writes
images/rmm/rmm-demo.gif and images/rmm/zones.png.
"""
import json, math, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

MAP = 520            # rendered floorplan size (px)
PANEL = 300          # side panel width (px)
FPS = 10
BG = (27, 36, 45)          # #1B242D
TEAL = (140, 189, 181)     # #8CBDB5 lifted Hailstorm (accent)
AMBER = (242, 190, 92)     # lights 'on' stay warm amber
DOLL = (230, 188, 182)     # #E6BCB6 Baby Doll
INK = (241, 236, 234)      # #F1ECEA
MUTE = (169, 186, 182)     # #A9BAB6
BAD = (227, 123, 123)      # #E37B7B

def font(size, bold=False, display=False):
    name = 'syne_700.ttf' if display else ('manrope_700.ttf' if bold else 'manrope_500.ttf')
    return ImageFont.truetype(os.path.join(os.path.dirname(__file__), 'fonts', name), size)

F_T, F_B, F_S, F_L = font(21, display=True), font(15, True), font(14), font(12, True)
rmm = json.load(open('config/rmm/radar_map_manager.json'))
base = Image.open('images/rmm/floorplan.png').convert('RGB').resize((MAP, MAP), Image.LANCZOS)

def P(x, y):  # percent -> px
    return (x / 100 * MAP, y / 100 * MAP)

ZONES = {z['name'].lower(): [P(*p) for p in z['points']] for z in rmm['zones']['include_zones']}
EXCL = [[P(*p) for p in z['points']] for z in rmm['zones']['exclude_zones'] if z['name'] == 'washer/dryer']
RADARS = [P(r['layout']['origin_x'], r['layout']['origin_y']) for r in rmm['radars'].values()]
LIGHTS = {  # illustrative positions (percent of the plan)
    'Kitchen 25%':  (72, 44), 'Wardrobe': (74, 70), 'Mirror LED': (49, 84), 'Kitchen': (66, 45),
}

def inside(pt, poly):
    x, y = pt; c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1:
            c = not c
    return c

def path(points, steps):
    pts = [P(*p) for p in points]
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

def frame(night, target, trail, lights, clock, title, caption, hold_zone=None):
    img = Image.new('RGB', (MAP + PANEL, MAP), BG)
    plan = ImageEnhance.Brightness(base).enhance(0.32 if night else 1.0)
    glow = Image.new('L', (MAP, MAP), 0); gd = ImageDraw.Draw(glow)
    for name, on in lights.items():
        if on:
            x, y = P(*LIGHTS[name]); r = 110
            gd.ellipse([x - r, y - r, x + r, y + r], fill=235 if night else 120)
    glow = glow.filter(ImageFilter.GaussianBlur(38))
    bright = ImageEnhance.Brightness(base).enhance(1.15)
    plan = Image.composite(bright, plan, glow)
    ov = Image.new('RGBA', (MAP, MAP), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    occupied = [n for n, poly in ZONES.items() if target and inside(target, poly)]
    if hold_zone and hold_zone not in occupied:
        occupied.append(hold_zone)
    for n, poly in ZONES.items():
        a = 95 if n in occupied else 22
        od.polygon(poly, fill=TEAL + (a,), outline=TEAL + (150 if n in occupied else 60,))
    for poly in EXCL:
        od.polygon(poly, fill=BAD + (45,), outline=BAD + (130,))
    for rx, ry in RADARS:
        od.ellipse([rx - 6, ry - 6, rx + 6, ry + 6], fill=DOLL + (240,))
    for name, on in lights.items():
        x, y = P(*LIGHTS[name])
        od.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(AMBER + (255,)) if on else (90, 90, 90, 200), outline=(255, 255, 255, 180))
    for i, (tx, ty) in enumerate(trail):
        a = int(40 + 160 * (i + 1) / max(len(trail), 1))
        od.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=TEAL + (a,))
    if target:
        tx, ty = target
        od.ellipse([tx - 13, ty - 13, tx + 13, ty + 13], fill=TEAL + (245,), outline=INK + (255,), width=2)
        od.text((tx - 4, ty - 9), '1', fill=BG, font=F_B)
    img.paste(Image.alpha_composite(plan.convert('RGBA'), ov).convert('RGB'), (0, 0))
    d = ImageDraw.Draw(img); x0 = MAP + 18
    d.text((x0, 14), title, fill=INK, font=F_T)
    d.text((x0, 44), clock, fill=AMBER if night else TEAL, font=font(30, display=True))
    d.text((x0, 92), 'ZONES OCCUPIED', fill=MUTE, font=F_L)
    d.text((x0, 110), ', '.join(z.title() for z in occupied) or '—', fill=TEAL, font=F_B)
    d.text((x0, 142), 'LIGHTS', fill=MUTE, font=F_L)
    y = 160
    for name, on in lights.items():
        d.ellipse([x0, y + 3, x0 + 12, y + 15], fill=AMBER if on else (58, 74, 88))
        d.text((x0 + 20, y), f'{name}  {"on" if on else "off"}', fill=INK if on else MUTE, font=F_S)
        y += 22
    y += 14
    for line in wrap(caption, PANEL - 36, F_S):
        d.text((x0, y), line, fill=INK, font=F_S); y += 20
    d.text((x0, MAP - 24), 'Illustrative mock-up · RMM + LD2450', fill=MUTE, font=font(11))
    return img

frames = []
def add(frames_list, n=1):
    frames.extend(frames_list * n if isinstance(frames_list, list) else [frames_list] * n)

# --- Scene 1: night path (bed -> bathroom -> kitchen for a drink -> back to bed) ----
T1 = 'Night path'
L_off = {'Kitchen 25%': False, 'Wardrobe': False, 'Mirror LED': False}
L_on = {'Kitchen 25%': True, 'Wardrobe': True, 'Mirror LED': True}
bed = (27.9, 74.0)
bath = (52.3, 77.3)
drink = (85.0, 46.8)
def walk(points, steps, clock, cap_fn, lit_fn):
    trail = []
    for i, p in enumerate(path(points, steps)):
        trail = (trail + [p])[-14:]
        lit = lit_fn(i, p)
        add(frame(True, p, trail, L_on if lit else L_off, clock, T1, cap_fn(i, lit)))
add(frame(True, P(*bed), [], L_off, '02:14', T1, 'Asleep. The bed zone is occupied and it is inside the night window, so the house stays dark.', 'bed'), 14)
walk([bed, (37.5, 72.7), (41.3, 75.4), (47.1, 76.5), bath], 20, '02:14',
     lambda i, lit: 'Into the bathroom: the night path comes on, dim - mirror LED, wardrobe and the kitchen at 25%.' if lit else 'Up for the bathroom: a target leaves the bed zone.',
     lambda i, p: inside(p, ZONES['bathroom']))
add(frame(True, P(*bath), [], L_on, '02:15', T1, 'The radar holds the bathroom while you stand still - no motion sensor timing out on you in the dark.', 'bathroom'), 14)
walk([bath, (50.4, 66.3), (49.6, 53.8), (51.9, 46.5), (63.5, 45.8), (76.9, 46.2), drink], 26, '02:17',
     lambda i, lit: 'Then the kitchen for a drink - the way is already lit at 25%, nothing bright.', lambda i, p: True)
add(frame(True, P(*drink), [], L_on, '02:18', T1, 'Getting a drink.', 'kitchen'), 12)
walk([drink, (80.8, 44.6), (57.7, 42.7), (34.6, 43.5), (21.2, 44.6), (18.3, 51.0), (15.4, 57.7), (15.0, 66.3), (18.3, 74.0), bed], 34, '02:19',
     lambda i, lit: 'Back to bed. The path stays on until you have been back in bed for 2 minutes (or it has been empty for 4).', lambda i, p: True)
add(frame(True, P(*bed), [], L_on, '02:20', T1, 'Back in bed... waiting 2 minutes.', 'bed'), 10)
add(frame(True, P(*bed), [], L_off, '02:22', T1, 'Bed occupied for 2 minutes, so the path lights switch off. No buttons, no app.', 'bed'), 16)

# --- Scene 2: kitchen lights in the day --------------------------------------------
T2 = 'Kitchen lights'
K_off = {'Kitchen': False}; K_on = {'Kitchen': True}
sofa = (34, 40)
add(frame(False, P(*sofa), [], K_off, '13:05', T2, 'Daytime on the sofa. Kitchen light is off.'), 10)
trail = []
for i, p in enumerate(path([sofa, (46, 45), (58, 46), (66, 44)], 22)):
    trail = (trail + [p])[-14:]
    lit = inside(p, ZONES['kitchen'])
    add(frame(False, p, trail, K_on if lit else K_off, '13:05', T2,
              'The kitchen PIR switches the light on the instant you walk in.' if lit else 'Heading to the kitchen.'))
add(frame(False, P(66, 44), [], K_on, '13:09', T2, 'Standing still at the bench: the PIR would have timed out by now, but the radar zone is still occupied, so the light holds.'), 22)
trail = []
for p in path([(66, 44), (58, 46), (46, 45), sofa], 18):
    trail = (trail + [p])[-14:]
    add(frame(False, p, trail, K_on, '13:10', T2, 'Walking away. The zone empties and the hold timer starts.'))
add(frame(False, P(*sofa), [], K_on, '13:11', T2, 'Kitchen zone empty...'), 8)
add(frame(False, P(*sofa), [], K_off, '13:12', T2, 'Zone empty past its hold, so the light turns off (a 5-minute sweep catches anything that slips through).'), 18)

with tempfile.TemporaryDirectory() as tmp:
    for i, f in enumerate(frames):
        f.save(f'{tmp}/f{i:04d}.png')
    pal = f'{tmp}/pal.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', f'{tmp}/f%04d.png',
                    '-vf', 'palettegen=stats_mode=diff:max_colors=200', pal], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', f'{tmp}/f%04d.png', '-i', pal,
                    '-lavfi', 'paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle', '-loop', '0',
                    'images/rmm/rmm-demo.gif'], check=True)

# --- static zones map ---------------------------------------------------------------
z = frame(False, None, [], {}, '', 'RMM zones', 'Teal: room zones fused from three LD2450 radars (red dots). Red: the washer/dryer is excluded because it vibrates like a person.')
d = ImageDraw.Draw(z)
for n, poly in ZONES.items():
    cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
    d.text((cx - F_B.getlength(n.title()) / 2, cy - 8), n.title(), fill='white', font=F_B, stroke_width=3, stroke_fill=(10, 40, 40))
z.save('images/rmm/zones.png', optimize=True)
print(f'{len(frames)} frames ->', os.path.getsize('images/rmm/rmm-demo.gif') // 1024, 'KB gif;', os.path.getsize('images/rmm/zones.png') // 1024, 'KB zones.png')
