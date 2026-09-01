#!/usr/bin/env python3
import datetime
import json
import math
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

USER = os.environ.get("GITHUB_USERNAME", "alebaqinduni")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = os.environ.get("OUTPUT_DIR", "dist")
os.makedirs(OUT, exist_ok=True)

TODAY = datetime.date.today()
FROM = datetime.datetime.combine(TODAY - datetime.timedelta(days=370), datetime.time.min, tzinfo=datetime.timezone.utc)
TO = datetime.datetime.combine(TODAY + datetime.timedelta(days=1), datetime.time.min, tzinfo=datetime.timezone.utc)

QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

payload = json.dumps({"query": QUERY, "variables": {"login": USER, "from": FROM.isoformat(), "to": TO.isoformat()}}).encode()
request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "alebaqinduni-rabbit-contribution-garden",
    },
    method="POST",
)

with urllib.request.urlopen(request, timeout=30) as response:
    data = json.load(response)
if data.get("errors"):
    raise SystemExit("GitHub GraphQL error: " + json.dumps(data["errors"]))

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = {}
for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days[day["date"]] = day["contributionCount"]

# Same compact 53-week / 7-row shape as GitHub.
week_start = TODAY - datetime.timedelta(days=(TODAY.weekday() + 1) % 7)
week_start -= datetime.timedelta(weeks=52)
cols, rows = 53, 7
cell, gap = 13, 4
left, top = 52, 78
width = left + cols * (cell + gap) + 32
height = top + rows * (cell + gap) + 58

PINK = ["#FFEDF5", "#FBCFE8", "#F9A8D4", "#F472B6", "#EC4899"]
max_count = max(days.values() or [1])
active = []

for col in range(cols):
    for row in range(rows):
        date = week_start + datetime.timedelta(days=col * 7 + row)
        count = days.get(date.isoformat(), 0) if date <= TODAY else 0
        x = left + col * (cell + gap)
        y = top + row * (cell + gap)
        if count > 0:
            active.append((date, x + cell / 2, y + cell / 2, count))
active.sort(key=lambda item: item[0])


def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


TITLE = font(16, True)
SUB = font(10)
MONTH = font(9)
DAY = font(8)
LEGEND = font(9)


def pink_level(count):
    if count <= 0:
        return None
    if max_count <= 1:
        return PINK[2]
    ratio = count / max_count
    if ratio <= .20:
        return PINK[0]
    if ratio <= .40:
        return PINK[1]
    if ratio <= .65:
        return PINK[2]
    if ratio <= .85:
        return PINK[3]
    return PINK[4]


def draw_rabbit(draw, cx, cy):
    # Small cute bunny with upright ears and a deliberately tiny tail.
    cx, cy = int(cx), int(cy)
    outline = "#EC4899"
    draw.ellipse((cx-8, cy+2, cx+8, cy+11), fill="white", outline=outline, width=2)
    draw.ellipse((cx-7, cy-6, cx+7, cy+8), fill="white", outline=outline, width=2)
    draw.ellipse((cx-7, cy-20, cx-1, cy-5), fill="white", outline=outline, width=2)
    draw.ellipse((cx+1, cy-20, cx+7, cy-5), fill="white", outline=outline, width=2)
    draw.ellipse((cx-3, cy-2, cx-1, cy), fill="#1F2937")
    draw.ellipse((cx+1, cy-2, cx+3, cy), fill="#1F2937")
    draw.ellipse((cx-1, cy+2, cx+1, cy+4), fill="#F472B6")
    draw.ellipse((cx+8, cy+2, cx+13, cy+7), fill="white", outline=outline, width=1)


def make_frame(dark, route_index, route_progress):
    if dark:
        bg, panel, stroke = "#090B12", "#0F1320", "#252A3A"
        text, sub, empty = "#F8FAFC", "#A1A1AA", "#171923"
    else:
        bg, panel, stroke = "#FFFFFF", "#FFFFFF", "#E5E7EB"
        text, sub, empty = "#1F2937", "#6B7280", "#F1F3F5"

    im = Image.new("RGB", (width, height), bg)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, width-8, height-8), radius=14, fill=panel, outline=stroke, width=1)
    d.text((24, 16), "CONTRIBUTION GARDEN • RABBIT RUN", fill=text, font=TITLE)
    d.text((24, 40), f'{calendar["totalContributions"]} contributions in the last year • rabbit travels active days only', fill=sub, font=SUB)

    last_month = None
    for col in range(cols):
        date = week_start + datetime.timedelta(weeks=col)
        label = date.strftime("%b")
        if label != last_month:
            d.text((left + col * (cell + gap), 59), label, fill=sub, font=MONTH)
            last_month = label

    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri"), (6, "Sun")]:
        d.text((12, top + row * (cell + gap) + 2), label, fill=sub, font=DAY)

    for col in range(cols):
        for row in range(rows):
            date = week_start + datetime.timedelta(days=col * 7 + row)
            count = days.get(date.isoformat(), 0) if date <= TODAY else 0
            x = left + col * (cell + gap)
            y = top + row * (cell + gap)
            fill = pink_level(count) or empty
            d.rounded_rectangle((x, y, x+cell, y+cell), radius=3, fill=fill, outline=stroke, width=1)

    # Trail only appears between consecutive contribution days.
    for a, b in zip(active, active[1:]):
        d1, x1, y1, _ = a
        d2, x2, y2, _ = b
        if (d2 - d1).days == 1:
            d.line((x1, y1, x2, y2), fill="#F472B6", width=2)

    if active:
        if len(active) == 1:
            x, y = active[0][1], active[0][2]
            hop = 0
        else:
            i = min(route_index, len(active) - 1)
            j = min(i + 1, len(active) - 1)
            f = route_progress
            _, x0, y0, _ = active[i]
            _, x1, y1, _ = active[j]
            x = x0 + (x1 - x0) * f
            y = y0 + (y1 - y0) * f
            hop = -abs(math.sin(f * math.pi)) * 9
        draw_rabbit(d, x, y + hop)

    legend_y = height - 24
    d.text((left, legend_y-8), "Less", fill=sub, font=LEGEND)
    lx = left + 34
    for color in [empty] + PINK[1:]:
        d.rounded_rectangle((lx, legend_y-10, lx+11, legend_y+1), radius=2, fill=color, outline=stroke)
        lx += 16
    d.text((lx+3, legend_y-8), "More", fill=sub, font=LEGEND)
    return im


def make_gif(path, dark):
    if not active:
        frames = [make_frame(dark, 0, 0)]
    else:
        frames = []
        frame_count = 48
        for frame_no in range(frame_count):
            progress = frame_no / (frame_count - 1)
            scaled = progress * (len(active) - 1)
            index = min(int(scaled), len(active) - 1)
            local = scaled - index if index < len(active) - 1 else 0
            frames.append(make_frame(dark, index, local))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=220, loop=0, optimize=True)


make_gif(os.path.join(OUT, "contribution-garden-rabbit.gif"), True)
make_gif(os.path.join(OUT, "contribution-garden-rabbit-light.gif"), False)
