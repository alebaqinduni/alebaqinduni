#!/usr/bin/env python3
import datetime, json, math, os, urllib.request
from PIL import Image, ImageDraw, ImageFont

USER = os.environ.get("GITHUB_USERNAME", "alebaqinduni")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = os.environ.get("OUTPUT_DIR", "dist")
os.makedirs(OUT, exist_ok=True)
TODAY = datetime.date.today()
FROM = datetime.datetime.combine(TODAY - datetime.timedelta(days=370), datetime.time.min, tzinfo=datetime.timezone.utc)
TO = datetime.datetime.combine(TODAY + datetime.timedelta(days=1), datetime.time.min, tzinfo=datetime.timezone.utc)
QUERY = '''query($login:String!, $from:DateTime!, $to:DateTime!) { user(login:$login) { contributionsCollection(from:$from, to:$to) { contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }'''
payload = json.dumps({"query": QUERY, "variables": {"login": USER, "from": FROM.isoformat(), "to": TO.isoformat()}}).encode()
req = urllib.request.Request("https://api.github.com/graphql", data=payload, headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "alebaqinduni-contribution-garden"}, method="POST")
with urllib.request.urlopen(req, timeout=30) as response:
    data = json.load(response)
if data.get("errors"):
    raise SystemExit(json.dumps(data["errors"]))
calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = {d["date"]: d["contributionCount"] for w in calendar["weeks"] for d in w["contributionDays"]}

PINK = ["#FFB0D3", "#FF6BAF", "#FF2F92", "#F20A73", "#C70055"]
max_count = max(days.values() or [1])
week_start = TODAY - datetime.timedelta(days=(TODAY.weekday() + 1) % 7) - datetime.timedelta(weeks=52)
cols, rows, cell, gap, left, top = 53, 7, 13, 4, 52, 78
width = left + cols * (cell + gap) + 32
height = top + rows * (cell + gap) + 58
active = []
for col in range(cols):
    for row in range(rows):
        date = week_start + datetime.timedelta(days=col * 7 + row)
        count = days.get(date.isoformat(), 0) if date <= TODAY else 0
        if count > 0:
            active.append((date, left + col*(cell+gap) + cell/2, top + row*(cell+gap) + cell/2, count))
active.sort(key=lambda x: x[0])


def font(size, bold=False):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, size) if os.path.exists(p) else ImageFont.load_default()

TITLE, SUB, MONTH, DAY, LEGEND = font(16, True), font(10), font(9), font(8), font(9)


def level(count):
    if count <= 0:
        return None
    if max_count <= 1:
        return PINK[3]
    ratio = count / max_count
    if ratio <= .20: return PINK[0]
    if ratio <= .40: return PINK[1]
    if ratio <= .65: return PINK[2]
    if ratio <= .85: return PINK[3]
    return PINK[4]


def bunny(d, cx, cy):
    """Tiny chibi white bunny; deliberately no circle, halo, or pink outer ring."""
    cx, cy = int(cx), int(cy)
    white = "#FFFFFF"
    soft_white = "#FFF9FD"
    inner = "#F7D8EC"
    outline = "#C9BDD9"
    dark = "#30213D"
    blush = "#F4A7C8"
    lavender = "#B89AD9"

    # Long floppy ears with soft inner-ear detail.
    d.ellipse((cx-11, cy-31, cx-3, cy-7), fill=white, outline=outline, width=2)
    d.ellipse((cx+3, cy-31, cx+11, cy-7), fill=white, outline=outline, width=2)
    d.ellipse((cx-8, cy-27, cx-5, cy-12), fill=inner)
    d.ellipse((cx+5, cy-27, cx+8, cy-12), fill=inner)

    # Chubby head and little body.
    d.ellipse((cx-12, cy-13, cx+12, cy+11), fill=white, outline=outline, width=2)
    d.ellipse((cx-14, cy+4, cx+14, cy+22), fill=white, outline=outline, width=2)

    # Fluffy white belly and tiny paws.
    d.ellipse((cx-8, cy+8, cx+8, cy+20), fill=soft_white)
    d.ellipse((cx-14, cy+15, cx-5, cy+23), fill=white, outline=outline, width=1)
    d.ellipse((cx+5, cy+15, cx+14, cy+23), fill=white, outline=outline, width=1)

    # Big gentle eyes, tiny nose and happy mouth.
    d.ellipse((cx-7, cy-4, cx-3, cy+1), fill=dark)
    d.ellipse((cx+3, cy-4, cx+7, cy+1), fill=dark)
    d.ellipse((cx-5, cy-3, cx-4, cy-2), fill=white)
    d.ellipse((cx+4, cy-3, cx+5, cy-2), fill=white)
    d.ellipse((cx-1, cy+1, cx+1, cy+4), fill=blush)
    d.arc((cx-5, cy+2, cx, cy+7), 10, 115, fill=dark, width=1)
    d.arc((cx, cy+2, cx+5, cy+7), 65, 170, fill=dark, width=1)

    # Tiny blush, whiskers, and a little lavender bow — no ring around the bunny.
    d.ellipse((cx-10, cy+1, cx-7, cy+4), fill=blush)
    d.ellipse((cx+7, cy+1, cx+10, cy+4), fill=blush)
    d.line((cx-9, cy+5, cx-15, cy+3), fill=outline, width=1)
    d.line((cx-9, cy+7, cx-15, cy+8), fill=outline, width=1)
    d.line((cx+9, cy+5, cx+15, cy+3), fill=outline, width=1)
    d.line((cx+9, cy+7, cx+15, cy+8), fill=outline, width=1)

    # Small bow under one ear for extra cuteness, kept lavender to match the profile.
    bx, by = cx + 8, cy + 9
    d.ellipse((bx-6, by-4, bx+1, by+3), fill=lavender)
    d.ellipse((bx+1, by-4, bx+8, by+3), fill=lavender)
    d.ellipse((bx-1, by-1, bx+3, by+4), fill=white)

    # Tiny fluffy tail.
    d.ellipse((cx+13, cy+7, cx+20, cy+14), fill=white, outline=outline, width=1)


def frame(route_index, progress, route):
    bg, panel, stroke = "#070910", "#0D1220", "#30384A"
    text, sub, empty = "#FFFFFF", "#CBD5E1", "#171D2B"
    im = Image.new("RGB", (width, height), bg)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8,8,width-8,height-8), radius=14, fill=panel, outline=stroke, width=1)
    d.text((24,16), "CONTRIBUTION GARDEN", fill=text, font=TITLE)
    d.text((24,40), f'{calendar["totalContributions"]} contributions in the last year  •  bunny visits active days', fill=sub, font=SUB)

    last = None
    for col in range(cols):
        date = week_start + datetime.timedelta(weeks=col)
        label = date.strftime("%b")
        if label != last:
            d.text((left + col*(cell+gap),59), label, fill=sub, font=MONTH)
            last = label
    for row, label in [(1,"Mon"),(3,"Wed"),(5,"Fri"),(6,"Sun")]:
        d.text((12, top + row*(cell+gap)+2), label, fill=sub, font=DAY)

    for col in range(cols):
        for row in range(rows):
            date = week_start + datetime.timedelta(days=col*7+row)
            count = days.get(date.isoformat(),0) if date <= TODAY else 0
            x, y = left + col*(cell+gap), top + row*(cell+gap)
            fill = level(count) or empty
            border = "#FFD1E5" if count > 0 else "#2A3140"
            d.rounded_rectangle((x,y,x+cell,y+cell), radius=3, fill=fill, outline=border, width=1)

    # The route is a true ping-pong path: left -> right -> left.
    # It never jumps from one edge to the other.
    if route:
        i = min(route_index, len(route)-1)
        j = min(i+1, len(route)-1)
        if i == j:
            x, y = route[i][1], route[i][2]
            hop = 0
        else:
            f = progress
            x = route[i][1] + (route[j][1]-route[i][1])*f
            y = route[i][2] + (route[j][2]-route[i][2])*f
            hop = -abs(math.sin(f*math.pi))*10
        bunny(d, x, y+hop)

    ly = height-24
    d.text((left,ly-8),"Less",fill=sub,font=LEGEND)
    lx=left+34
    for c in [empty]+PINK[1:]:
        d.rounded_rectangle((lx,ly-10,lx+11,ly+1),radius=2,fill=c,outline=stroke)
        lx += 16
    d.text((lx+3,ly-8),"More",fill=sub,font=LEGEND)
    return im


def gif(path):
    frames=[]
    if not active:
        route=[]
    elif len(active) == 1:
        route=active
    else:
        # Forward through every active day, then reverse through the same path.
        # The end points are not duplicated, so the bunny turns around naturally.
        route = active + list(reversed(active[1:-1]))

    n=max(90,min(180,len(route)*3 if route else 90))
    for k in range(n):
        p=k/(n-1) if n>1 else 0
        scaled=p*(len(route)-1) if route else 0
        i=min(int(scaled),len(route)-1) if route else 0
        local=scaled-i if route and i<len(route)-1 else 0
        frames.append(frame(i,local,route))
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=180,loop=0,optimize=True)

gif(os.path.join(OUT,"contribution-garden-rabbit.gif"))
gif(os.path.join(OUT,"contribution-garden-rabbit-light.gif"))
