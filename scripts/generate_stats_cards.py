#!/usr/bin/env python3
import datetime
import json
import os
import urllib.request
from collections import defaultdict

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
    followers { totalCount }
    repositories(first:100, ownerAffiliations:[OWNER], isFork:false) {
      totalCount
      nodes {
        languages(first:10, orderBy:{field:SIZE, direction:DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection(from:$from, to:$to) {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
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
        "User-Agent": "alebaqinduni-profile-stats",
    },
    method="POST",
)
with urllib.request.urlopen(request, timeout=30) as response:
    data = json.load(response)

if data.get("errors"):
    raise SystemExit("GitHub GraphQL error: " + json.dumps(data["errors"]))

user = data["data"]["user"]
calendar = user["contributionsCollection"]["contributionCalendar"]
days = {}
for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days[day["date"]] = day["contributionCount"]


def current_streak():
    cursor = TODAY
    if days.get(cursor.isoformat(), 0) == 0:
        cursor -= datetime.timedelta(days=1)
    count = 0
    while days.get(cursor.isoformat(), 0) > 0:
        count += 1
        cursor -= datetime.timedelta(days=1)
    return count


def longest_streak():
    best = run = 0
    for offset in range(370, -1, -1):
        value = days.get((TODAY - datetime.timedelta(days=offset)).isoformat(), 0)
        if value > 0:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def esc(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

languages = defaultdict(int)
colors = {}
for repo in user["repositories"]["nodes"]:
    for edge in repo["languages"]["edges"]:
        name = edge["node"]["name"]
        languages[name] += edge["size"]
        colors[name] = edge["node"].get("color") or "#A78BFA"

top_languages = sorted(languages.items(), key=lambda item: item[1], reverse=True)[:6]

stats = {
    "contributions": calendar["totalContributions"],
    "current_streak": current_streak(),
    "longest_streak": longest_streak(),
    "public_repos": user["repositories"]["totalCount"],
}


def render(theme):
    dark = theme == "dark"
    bg = "#0D1117" if dark else "#FFFFFF"
    panel = "#131A24" if dark else "#F6F8FA"
    border = "#2A3140" if dark else "#D0D7DE"
    primary = "#F0F6FC" if dark else "#24292F"
    muted = "#8B93A1" if dark else "#57606A"
    accent = "#FF6FAE" if dark else "#D63384"
    bunny = "#FF9BC4" if dark else "#D63384"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="300" viewBox="0 0 1180 300">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{bg}"/><stop offset="1" stop-color="{panel}"/></linearGradient>
  <filter id="soft"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="1180" height="300" rx="16" fill="url(#bg)" stroke="{border}"/>
<circle cx="34" cy="32" r="6.5" fill="#FF5F56"/><circle cx="58" cy="32" r="6.5" fill="#FFBD2E"/><circle cx="82" cy="32" r="6.5" fill="#27C93F"/>
<text x="118" y="37" font-family="Fira Code,Consolas,monospace" font-size="14" fill="{muted}">% ./stats.sh --live</text>
<line x1="0" y1="58" x2="1180" y2="58" stroke="{border}"/>
<text x="60" y="91" font-family="Fira Code,Consolas,monospace" font-size="13" letter-spacing="2" fill="{muted}">GITHUB.STATS</text>
<text x="1085" y="91" text-anchor="end" font-family="Arial,sans-serif" font-size="18" fill="{bunny}">૮ ˶ᵔ ᵕ ᵔ˶ ა</text>
'''

    values = [
        (stats["contributions"], "Contributions / year"),
        (stats["current_streak"], "Current streak"),
        (stats["longest_streak"], "Longest streak"),
        (stats["public_repos"], "Public repos"),
    ]
    centers = [192.5, 457.5, 722.5, 987.5]
    for i, ((value, label), center) in enumerate(zip(values, centers)):
        delay = 0.25 + i * 0.12
        svg += f'''<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.45s" begin="{delay:.2f}s" fill="freeze"/>
<text x="{center}" y="150" text-anchor="middle" font-family="Fira Code,Consolas,monospace" font-size="40" font-weight="700" fill="{primary}">{value}</text>
<text x="{center}" y="178" text-anchor="middle" font-family="Fira Code,Consolas,monospace" font-size="13" fill="{muted}">{esc(label)}</text></g>'''
        if i < 3:
            x = 325 + i * 265
            svg += f'<line x1="{x}" y1="115" x2="{x}" y2="185" stroke="{border}"/>'

    svg += f'<text x="60" y="220" font-family="Fira Code,Consolas,monospace" font-size="13" letter-spacing="2" fill="{muted}">TOP.LANGUAGES</text>'
    total = sum(value for _, value in top_languages) or 1
    x = 60
    for i, (name, value) in enumerate(top_languages):
        label_width = max(92, 58 + len(name) * 9)
        if x + label_width > 1115:
            break
        color = colors.get(name, accent)
        delay = 1.0 + i * 0.08
        svg += f'''<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="{delay:.2f}s" fill="freeze"/>
<rect x="{x}" y="228" width="{label_width}" height="34" rx="17" fill="{bg}" stroke="{border}"/>
<circle cx="{x+20}" cy="245" r="5" fill="{color}"/><text x="{x+34}" y="249.5" font-family="Fira Code,Consolas,monospace" font-size="14" fill="{primary}">{esc(name)}</text></g>'''
        x += label_width + 14
    svg += "</svg>"
    return svg

for theme in ("dark", "light"):
    with open(os.path.join(OUT, f"stats-{theme}.svg"), "w", encoding="utf-8") as handle:
        handle.write(render(theme))
