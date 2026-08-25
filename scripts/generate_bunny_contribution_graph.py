#!/usr/bin/env python3
import datetime
import json
import os
import urllib.request

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
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": QUERY,
    "variables": {"login": USER, "from": FROM.isoformat(), "to": TO.isoformat()},
}).encode()

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "alebaqinduni-bunny-contribution-graph",
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

# Use the same 53-week layout as GitHub's contribution calendar.
week_start = TODAY - datetime.timedelta(days=(TODAY.weekday() + 1) % 7)
week_start -= datetime.timedelta(weeks=52)
cols, rows = 53, 7
cell, gap = 13, 4
left, top = 52, 78
width = left + cols * (cell + gap) + 32
height = top + rows * (cell + gap) + 58

# Five pink intensity levels. Inactive days stay neutral, so the graph never
# becomes a wall of pink, black, or white.
PINK = ["#FFEDF5", "#FBCFE8", "#F9A8D4", "#F472B6", "#EC4899"]
DARK_EMPTY = "#171923"
LIGHT_EMPTY = "#F1F3F5"
DARK_TEXT = "#F8FAFC"
LIGHT_TEXT = "#1F2937"
DARK_SUB = "#A1A1AA"
LIGHT_SUB = "#6B7280"


def esc(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def pink_level(count, max_count):
    if count <= 0:
        return None
    if max_count <= 1:
        return PINK[2]
    ratio = count / max_count
    if ratio <= 0.20:
        return PINK[0]
    if ratio <= 0.40:
        return PINK[1]
    if ratio <= 0.65:
        return PINK[2]
    if ratio <= 0.85:
        return PINK[3]
    return PINK[4]


max_count = max(days.values() or [1])
active_positions = []
active_by_date = {}

for col in range(cols):
    for row in range(rows):
        date = week_start + datetime.timedelta(days=col * 7 + row)
        count = days.get(date.isoformat(), 0) if date <= TODAY else 0
        x = left + col * (cell + gap)
        y = top + row * (cell + gap)
        active_by_date[date] = (x, y, count)
        if count > 0:
            active_positions.append((date, x + cell / 2, y + cell / 2, count))

# Sort active days chronologically. The bunny will hop only between these
# points; inactive days are never part of its route.
active_positions.sort(key=lambda item: item[0])


def bunny_svg(cx, cy, scale=1.0):
    # Small, compact bunny with a deliberately tiny tail.
    return f'''<g transform="translate({cx:.1f} {cy:.1f}) scale({scale})" filter="url(#bunnyGlow)">
  <ellipse cx="0" cy="9" rx="8" ry="5" fill="#FFFFFF" stroke="#EC4899" stroke-width="1.5"/>
  <circle cx="0" cy="1" r="7" fill="#FFFFFF" stroke="#EC4899" stroke-width="1.5"/>
  <ellipse cx="-4" cy="-10" rx="3" ry="8" fill="#FFFFFF" stroke="#EC4899" stroke-width="1.5" transform="rotate(-8 -4 -10)"/>
  <ellipse cx="4" cy="-10" rx="3" ry="8" fill="#FFFFFF" stroke="#EC4899" stroke-width="1.5" transform="rotate(8 4 -10)"/>
  <circle cx="-2.3" cy="0" r="1" fill="#1F2937"/><circle cx="2.3" cy="0" r="1" fill="#1F2937"/>
  <circle cx="0" cy="3" r="1.2" fill="#F472B6"/>
  <circle cx="9" cy="8" r="2.3" fill="#FFFFFF" stroke="#EC4899" stroke-width="1.2"/>
</g>'''


def build_theme(dark=True):
    bg = "#090B12" if dark else "#FFFFFF"
    panel = "#0F1320" if dark else "#FFFFFF"
    stroke = "#252A3A" if dark else "#E5E7EB"
    text = DARK_TEXT if dark else LIGHT_TEXT
    sub = DARK_SUB if dark else LIGHT_SUB
    empty = DARK_EMPTY if dark else LIGHT_EMPTY
    title = "CONTRIBUTION GARDEN • BUNNY HOPS" if dark else "CONTRIBUTION GARDEN • BUNNY HOPS"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs>
  <filter id="bunnyGlow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="1.6" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<rect width="{width}" height="{height}" rx="18" fill="{bg}"/>
<rect x="8" y="8" width="{width-16}" height="{height-16}" rx="14" fill="{panel}" stroke="{stroke}"/>
<text x="24" y="31" fill="{text}" font-family="Arial,sans-serif" font-size="17" font-weight="700">{title} 🐇</text>
<text x="24" y="51" fill="{sub}" font-family="Arial,sans-serif" font-size="11">{calendar["totalContributions"]} contributions in the last year • bunny visits active days only</text>
'''

    # Month labels based on the actual dates in the grid.
    last_month = None
    for col in range(cols):
        date = week_start + datetime.timedelta(weeks=col)
        label = date.strftime("%b")
        if label != last_month:
            x = left + col * (cell + gap)
            svg += f'<text x="{x}" y="69" fill="{sub}" font-family="Arial,sans-serif" font-size="10">{label}</text>'
            last_month = label

    # Weekday labels.
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri"), (6, "Sun")]:
        y = top + row * (cell + gap) + 10
        svg += f'<text x="12" y="{y}" fill="{sub}" font-family="Arial,sans-serif" font-size="9">{label}</text>'

    # The contribution calendar itself: inactive days are neutral; active
    # days are pink with intensity based on the actual contribution count.
    for col in range(cols):
        for row in range(rows):
            date = week_start + datetime.timedelta(days=col * 7 + row)
            count = days.get(date.isoformat(), 0) if date <= TODAY else 0
            x = left + col * (cell + gap)
            y = top + row * (cell + gap)
            fill = pink_level(count, max_count) or empty
            border = "#2A2F3B" if dark else "#E5E7EB"
            svg += f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{fill}" stroke="{border}" stroke-width="0.7"><title>{esc(date.isoformat())}: {count} contribution(s)</title></rect>'

    # A very subtle path appears only for consecutive active days. When there
    # is an inactive gap, the bunny jumps directly to the next active square
    # instead of drawing a path through inactive squares.
    for previous, current in zip(active_positions, active_positions[1:]):
        d1, x1, y1, _ = previous
        d2, x2, y2, _ = current
        if (d2 - d1).days == 1:
            svg += f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" fill="none" stroke="#F472B6" stroke-width="2" stroke-linecap="round" stroke-dasharray="2 5" opacity="0.65"/>'

    # Bunny animation: discrete x/y keyframes are generated only from active
    # contribution days, producing a hop from one active square to the next.
    if active_positions:
        # Limit the animation sequence to the latest 60 active days so the SVG
        # stays lightweight while still showing a lively year-long garden.
        route = active_positions[-60:]
        duration = max(12, len(route) * 0.55)
        xs = []
        ys = []
        key_times = []
        for i, (_, x, y, _) in enumerate(route):
            xs.append(f"{x:.1f}")
            # Alternate a small hop arc without moving onto inactive squares.
            hop = -7 if i % 2 == 0 else -2
            ys.append(f"{y + hop:.1f}")
            key_times.append(f"{i / max(1, len(route)-1):.4f}")
        values_x = ";".join(xs)
        values_y = ";".join(ys)
        times = ";".join(key_times)
        svg += f'''<g>
  <animateTransform attributeName="transform" type="translate" values="0 0;0 0" dur="1s" repeatCount="indefinite"/>
  <g>
    <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.04;0.94;1" dur="{duration}s" repeatCount="indefinite"/>
    <g>
      <animateTransform attributeName="transform" type="translate" values="{';'.join(f'{x:.1f} {y + (-7 if i % 2 == 0 else -2):.1f}' for i, (_, x, y, _) in enumerate(route))}" keyTimes="{times}" dur="{duration}s" repeatCount="indefinite" calcMode="discrete"/>
      <g transform="translate(0 0) scale(.82)">{bunny_svg(0, 0, 1.0)}</g>
    </g>
  </g>
</g>'''

    # Legend: only active colors are pink; neutral inactive square is shown once.
    legend_y = height - 24
    svg += f'<text x="{left}" y="{legend_y}" fill="{sub}" font-family="Arial,sans-serif" font-size="10">Less</text>'
    lx = left + 34
    for color in [empty] + PINK[1:]:
        svg += f'<rect x="{lx}" y="{legend_y-10}" width="11" height="11" rx="2" fill="{color}" stroke="{stroke}" stroke-width="0.5"/>'
        lx += 16
    svg += f'<text x="{lx+3}" y="{legend_y}" fill="{sub}" font-family="Arial,sans-serif" font-size="10">More</text>'
    svg += '</svg>'
    return svg


open(os.path.join(OUT, "contribution-graph-dark.svg"), "w", encoding="utf-8").write(build_theme(True))
open(os.path.join(OUT, "contribution-graph-light.svg"), "w", encoding="utf-8").write(build_theme(False))
