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
req = urllib.request.Request("https://api.github.com/graphql", data=payload, headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "alebaqinduni-rabbit-contribution-garden"}, method="POST")
with urllib.request.urlopen(req, timeout=30) as response:
    data = json.load(response)
if data.get("errors"):
    raise SystemExit(json.dumps(data["errors"]))
calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = {d["date"]: d["contributionCount"] for w in calendar["weeks"] for d in w["contributionDays"]}

# Palette intentionally matches the profile: deep navy + vivid pink/purple accents.
# No washed-out contribution squares.
PINK = ["#FFC2DE", "#FF82BA", "#FF4F9D", "#FF167F", "#D9005B"]
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


def rabbit(d, cx, cy):
    # Filled pink bunny rather than an outline-only bunny, so it reads clearly at README size.
    cx, cy = int(cx), int(cy)
    pink = "#FF4F9D"
    deep = "#D9005B"
    white = "#FFFFFF"
    # soft halo
    d.ellipse((cx-18, cy-25, cx+18, cy+19), fill="#FF167F")
    # ears
    d.ellipse((cx-10, cy-27, cx-2, cy-7), fill=pink, outline=deep, width=2)
    d.ellipse((cx+2, cy-27, cx+10, cy-7), fill=pink, outline=deep, width=2)
    d.ellipse((cx-7, cy-24, cx-4, cy-11), fill="#FFC2DE")
    d.ellipse((cx+4, cy-24, cx+7, cy-11), fill="#FFC2DE")
    # head + body
    d.ellipse((cx-10, cy-11, cx+10, cy+10), fill=pink, outline=deep, width=2)
    d.ellipse((cx-12, cy+4, cx+12, cy+17), fill=pink, outline=deep, width=2)
    # white belly
    d.ellipse((cx-6, cy+6, cx+6, cy+15), fill=white)
    # face
    d.ellipse((cx-5, cy-3, cx-2, cy), fill="#24152B")
    d.ellipse((cx+2, cy-3, cx+5, cy), fill="#24152B")
    d.ellipse((cx-1, cy+1, cx+1, cy+3), fill=white)
    # tiny tail
    d.ellipse((cx+11, cy+5, cx+16, cy+10), fill=white, outline=deep, width=1)


def frame(index, progress):
    # Always use the deep profile-style card, even in light GitHub mode.
    # This keeps the garden visually consistent with the rest of the profile.
    bg, panel, stroke = "#070910", "#0D1220", "#30384A"
    text, sub, empty = "#FFFFFF", "#CBD5E1", "#171D2B"
    im = Image.new("RGB", (width, height), bg)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8,8,width-8,height-8), radius=14, fill=panel, outline=stroke, width=1)
    d.text((24,16), "CONTRIBUTION GARDEN  •  RABBIT RUN", fill=text, font=TITLE)
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

    # High-contrast contribution cells. Active cells have a subtle white edge; empty cells stay dark.
    for col in range(cols):
        for row in range(rows):
            date = week_start + datetime.timedelta(days=col*7+row)
            count = days.get(date.isoformat(),0) if date <= TODAY else 0
            x, y = left + col*(cell+gap), top + row*(cell+gap)
            fill = level(count) or empty
            border = "#FFB3D4" if count > 0 else "#2A3140"
            d.rounded_rectangle((x,y,x+cell,y+cell), radius=3, fill=fill, outline=border, width=1)

    # IMPORTANT: no connecting line/trail. The rabbit itself is the only moving element.
    # It travels smoothly from active contribution square to active contribution square.
    if active:
        i = min(index, len(active)-1)
        j = min(i+1, len(active)-1)
        if i == j:
            x,y = active[i][1], active[i][2]
            hop = 0
        else:
            f = progress
            x = active[i][1] + (active[j][1]-active[i][1])*f
            y = active[i][2] + (active[j][2]-active[i][2])*f
            hop = -abs(math.sin(f*math.pi))*10
        rabbit(d, x, y+hop)

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
    n=max(60,min(120,len(active)*2 if active else 60))
    for k in range(n):
        p=k/(n-1) if n>1 else 0
        scaled=p*(len(active)-1) if active else 0
        i=min(int(scaled),len(active)-1) if active else 0
        local=scaled-i if active and i<len(active)-1 else 0
        frames.append(frame(i,local))
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=180,loop=0,optimize=True)

gif(os.path.join(OUT,"contribution-garden-rabbit.gif"))
gif(os.path.join(OUT,"contribution-garden-rabbit-light.gif"))
