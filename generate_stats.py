import os
import requests
from datetime import date, timedelta

USERNAME = os.environ.get("GITHUB_USERNAME")
TOKEN = os.environ.get("GITHUB_TOKEN")

if not USERNAME or not TOKEN:
    raise ValueError("GITHUB_USERNAME and GITHUB_TOKEN are required.")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""

response = requests.post(
    "https://api.github.com/graphql",
    json={
        "query": QUERY,
        "variables": {"login": USERNAME}
    },
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
)

response.raise_for_status()
result = response.json()

if "errors" in result:
    raise RuntimeError(result["errors"])

calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]

days = []

for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days.append({
            "date": date.fromisoformat(day["date"]),
            "count": day["contributionCount"],
            "color": day["color"]
        })

days.sort(key=lambda x: x["date"])

today = date.today()

total_contributions = calendar["totalContributions"]

year_contributions = sum(
    d["count"]
    for d in days
    if d["date"].year == today.year
)


def calculate_streaks(data):
    longest = 0
    streak = 0
    previous_date = None

    for item in data:
        if item["count"] > 0:
            if (
                previous_date is not None
                and item["date"] == previous_date + timedelta(days=1)
            ):
                streak += 1
            else:
                streak = 1

            longest = max(longest, streak)
            previous_date = item["date"]
        else:
            streak = 0
            previous_date = item["date"]

    day_lookup = {d["date"]: d["count"] for d in data}

    current_streak = 0
    check_date = today

    while day_lookup.get(check_date, 0) > 0:
        current_streak += 1
        check_date -= timedelta(days=1)

    if current_streak == 0:
        check_date = today - timedelta(days=1)

        while day_lookup.get(check_date, 0) > 0:
            current_streak += 1
            check_date -= timedelta(days=1)

    return current_streak, longest


current_streak, longest_streak = calculate_streaks(days)

graph_days = days[-371:]

cell_size = 13
cell_gap = 3
graph_x = 35
graph_y = 145

svg_cells = []

for index, item in enumerate(graph_days):
    x = graph_x + (index // 7) * (cell_size + cell_gap)
    y = graph_y + (index % 7) * (cell_size + cell_gap)

    svg_cells.append(
        f"""
        <rect
            x="{x}"
            y="{y}"
            width="{cell_size}"
            height="{cell_size}"
            rx="3"
            fill="{item['color']}">
            <title>
                {item['date']}: {item['count']} contributions
            </title>
        </rect>
        """
    )

graph_width = ((len(graph_days) // 7) + 1) * (cell_size + cell_gap)

svg = f"""<svg
width="100%"
height="330"
viewBox="0 0 {max(900, graph_width + 70)} 330"
xmlns="http://www.w3.org/2000/svg">

<rect
width="100%"
height="100%"
rx="16"
fill="#0d1117"/>

<text
x="30"
y="35"
fill="#f0f6fc"
font-size="20"
font-family="Arial, sans-serif"
font-weight="700">
GitHub Contribution Stats
</text>

<text
x="30"
y="58"
fill="#8b949e"
font-size="13"
font-family="Arial, sans-serif">
@{USERNAME}
</text>

<rect
x="30"
y="75"
width="175"
height="52"
rx="10"
fill="#161b22"/>

<text
x="43"
y="96"
fill="#8b949e"
font-size="11"
font-family="Arial">
Total Contributions
</text>

<text
x="43"
y="116"
fill="#f0f6fc"
font-size="18"
font-weight="700"
font-family="Arial">
{total_contributions:,}
</text>

<rect
x="215"
y="75"
width="175"
height="52"
rx="10"
fill="#161b22"/>

<text
x="228"
y="96"
fill="#8b949e"
font-size="11"
font-family="Arial">
Current Streak
</text>

<text
x="228"
y="116"
fill="#f0f6fc"
font-size="18"
font-weight="700"
font-family="Arial">
{current_streak} days
</text>

<rect
x="400"
y="75"
width="175"
height="52"
rx="10"
fill="#161b22"/>

<text
x="413"
y="96"
fill="#8b949e"
font-size="11"
font-family="Arial">
Longest Streak
</text>

<text
x="413"
y="116"
fill="#f0f6fc"
font-size="18"
font-weight="700"
font-family="Arial">
{longest_streak} days
</text>

<rect
x="585"
y="75"
width="175"
height="52"
rx="10"
fill="#161b22"/>

<text
x="598"
y="96"
fill="#8b949e"
font-size="11"
font-family="Arial">
This Year
</text>

<text
x="598"
y="116"
fill="#f0f6fc"
font-size="18"
font-weight="700"
font-family="Arial">
{year_contributions:,}
</text>

<text
x="30"
y="135"
fill="#f0f6fc"
font-size="13"
font-family="Arial"
font-weight="600">
Contribution Graph
</text>

{"".join(svg_cells)}

</svg>
"""

with open(
    "github-contribution-stats.svg",
    "w",
    encoding="utf-8"
) as file:
    file.write(svg)

print("Contribution statistics generated successfully.")
print(f"Total Contributions: {total_contributions}")
print(f"Current Streak: {current_streak}")
print(f"Longest Streak: {longest_streak}")
print(f"Contributions This Year: {year_contributions}")
