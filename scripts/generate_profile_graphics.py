#!/usr/bin/env python3
import json, os, urllib.request, datetime
from collections import defaultdict

USER = os.environ.get("GITHUB_USERNAME", "alebaqinduni")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = os.environ.get("OUTPUT_DIR", "dist")
os.makedirs(OUT, exist_ok=True)

today = datetime.date.today()
from_dt = datetime.datetime.combine(today - datetime.timedelta(days=370), datetime.time.min, tzinfo=datetime.timezone.utc)
to_dt = datetime.datetime.combine(today + datetime.timedelta(days=1), datetime.time.min, tzinfo=datetime.timezone.utc)

query = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    followers { totalCount }
    repositories(first:100, ownerAffiliations:[OWNER], isFork:false) {
      totalCount
      nodes {
        name
        stargazerCount
        forkCount
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
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {"login": USER, "from": from_dt.isoformat(), "to": to_dt.isoformat()}
}).encode()

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "alebaqinduni-profile-graphics",
    },
    method="POST",
)
with urllib.request.urlopen(req, timeout=30) as response:
    data = json.load(response)

if data.get("errors"):
    raise SystemExit("GitHub GraphQL error: " + json.dumps(data["errors"]))

user = data["data"]["user"]
cc = user["contributionsCollection"]
days = {}
for week in cc["contributionCalendar"]["weeks"]:
    for day in week["contributionDays"]:
        days[day["date"]] = day["contributionCount"]


def esc(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def shell(width, height, title, subtitle):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs>
 <linearGradient id="grad" x1="0" x2="1"><stop stop-color="#A78BFA"/><stop offset="1" stop-color="#10B981"/></linearGradient>
 <filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="{width}" height="{height}" rx="18" fill="#0A101F" stroke="#273449"/>
<text x="30" y="38" fill="#E0E7FF" font-family="Arial,sans-serif" font-size="18" font-weight="700">{esc(title)}</text>
<text x="30" y="60" fill="#94A3B8" font-family="Arial,sans-serif" font-size="12">{esc(subtitle)}</text>'''


# Activity graph: real GitHub contribution data for the last 31 days.
last31 = [days.get((today - datetime.timedelta(days=i)).isoformat(), 0) for i in range(30, -1, -1)]
max_value = max(last31) or 1
points = []
for index, value in enumerate(last31):
    x = 55 + index * (890 / 30)
    y = 190 - (value / max_value) * 105
    points.append(f"{x:.1f},{y:.1f}")

svg = shell(1000, 245, "ACTIVITY GRAPH", "GitHub contributions • last 31 days")
svg += '<g opacity=".28" stroke="#334155"><line x1="55" y1="85" x2="945" y2="85"/><line x1="55" y1="137" x2="945" y2="137"/><line x1="55" y1="190" x2="945" y2="190"/></g>'
svg += f'<polyline points="{" ".join(points)}" fill="none" stroke="url(#grad)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
for index, value in enumerate(last31):
    if value:
        x = 55 + index * (890 / 30)
        y = 190 - (value / max_value) * 105
        svg += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#10B981" filter="url(#glow)"><title>{value} contribution(s)</title></circle>'
svg += '<text x="55" y="218" fill="#64748B" font-family="Arial,sans-serif" font-size="11">30 days ago</text><text x="900" y="218" fill="#64748B" font-family="Arial,sans-serif" font-size="11">today</text>'
svg += f'<text x="750" y="38" fill="#A78BFA" font-family="Arial,sans-serif" font-size="12" font-weight="700">{cc["contributionCalendar"]["totalContributions"]} contributions / year</text>'
svg += '</svg>'
open(os.path.join(OUT, "activity-graph.svg"), "w", encoding="utf-8").write(svg)


# Language chart from actual repository language byte counts.
languages = defaultdict(int)
colors = {}
for repo in user["repositories"]["nodes"]:
    for edge in repo["languages"]["edges"]:
        name = edge["node"]["name"]
        languages[name] += edge["size"]
        colors[name] = edge["node"].get("color") or "#A78BFA"

top = sorted(languages.items(), key=lambda item: item[1], reverse=True)[:6]
total = sum(value for _, value in top) or 1
svg = shell(1000, 210, "TECHNOLOGY FOCUS", "Languages detected across your public repositories")
y = 90
for name, value in top:
    percent = value / total * 100
    width = 610 * percent / 100
    svg += f'<text x="30" y="{y}" fill="#E0E7FF" font-family="Arial,sans-serif" font-size="13" font-weight="700">{esc(name)}</text>'
    svg += f'<rect x="155" y="{y-12}" width="610" height="14" rx="7" fill="#182235"/><rect x="155" y="{y-12}" width="{width:.1f}" height="14" rx="7" fill="{colors[name]}"/>'
    svg += f'<text x="790" y="{y}" fill="#94A3B8" font-family="Arial,sans-serif" font-size="12">{percent:.1f}%</text>'
    y += 25
svg += '</svg>'
open(os.path.join(OUT, "languages.svg"), "w", encoding="utf-8").write(svg)


# Achievement board: locally generated, so it never depends on a paused Vercel service.
repo_count = user["repositories"]["totalCount"]
follower_count = user["followers"]["totalCount"]
star_count = sum(repo["stargazerCount"] for repo in user["repositories"]["nodes"])
svg = shell(1000, 210, "GITHUB ACHIEVEMENTS", "Generated locally by GitHub Actions — no external trophy service")
cards = [
    ("🚀", "REPOSITORIES", repo_count, "public projects"),
    ("⭐", "STARS", star_count, "repository stars"),
    ("🔥", "CONTRIBUTIONS", cc["contributionCalendar"]["totalContributions"], "past year"),
    ("👥", "FOLLOWERS", follower_count, "GitHub followers"),
]
x = 30
for icon, label, value, sub in cards:
    svg += f'<rect x="{x}" y="82" width="220" height="96" rx="14" fill="#111827" stroke="#334155"/>'
    svg += f'<text x="{x+18}" y="113" font-size="25">{icon}</text><text x="{x+18}" y="140" fill="#E0E7FF" font-family="Arial,sans-serif" font-size="14" font-weight="700">{esc(label)}</text>'
    svg += f'<text x="{x+18}" y="161" fill="#A78BFA" font-family="Arial,sans-serif" font-size="16" font-weight="700">{value}</text><text x="{x+105}" y="161" fill="#64748B" font-family="Arial,sans-serif" font-size="10">{esc(sub)}</text>'
    x += 240
svg += '</svg>'
open(os.path.join(OUT, "achievements.svg"), "w", encoding="utf-8").write(svg)


# Momentum/streak card.
streak = 0
cursor = today
while days.get(cursor.isoformat(), 0) > 0:
    streak += 1
    cursor -= datetime.timedelta(days=1)
if streak == 0 and days.get((today - datetime.timedelta(days=1)).isoformat(), 0) > 0:
    cursor = today - datetime.timedelta(days=1)
    while days.get(cursor.isoformat(), 0) > 0:
        streak += 1
        cursor -= datetime.timedelta(days=1)

svg = shell(1000, 125, "DEVELOPER MOMENTUM", "A live snapshot generated from GitHub contribution data")
svg += f'<text x="30" y="102" fill="#A78BFA" font-family="Arial,sans-serif" font-size="25" font-weight="700">🔥 {streak} day streak</text>'
svg += f'<text x="300" y="101" fill="#E0E7FF" font-family="Arial,sans-serif" font-size="13">{cc["totalCommitContributions"]} commits • {cc["totalPullRequestContributions"]} PRs • {cc["totalIssueContributions"]} issues in the past year</text>'
svg += '</svg>'
open(os.path.join(OUT, "streak.svg"), "w", encoding="utf-8").write(svg)
