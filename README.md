# 👋 Hi, I'm Mohit

### 🚀 Aspiring Full-Stack Developer | IT/CS Engineering Student

I'm an IT/CS engineering student passionate about building clean, responsive, and user-friendly web applications. I enjoy turning ideas into real projects while continuously improving my problem-solving and programming skills.

I'm currently strengthening my JavaScript fundamentals and working toward becoming a Full Stack Developer through hands-on projects, consistent learning, and real-world practice.

---

## 💡 About Me

* 💻 Building practical web projects to improve my development skills
  
* 🌱 Currently learning JavaScript, Python, Git, and responsive web design
  
* 🎯 Focused on writing clean, maintainable, and readable code
  
* 🤝 Open to collaborating on beginner-friendly open-source and web development projects
  
* 📚 Learning by building, debugging, and improving every day

---

## 🎯 Current Focus

* 🌐 Completing and deploying my personal portfolio website
  
* 📘 Mastering modern JavaScript (ES6+)
  
* 📱 Building fully responsive websites
  
* 🐍 Strengthening programming fundamentals with Python
  
* 🔗 Learning Git and collaborative development workflows
  
* 🚀 Preparing for internships and entry-level Full Stack Developer roles

---

## 🛠️ Tech Stack

### Comfortable With

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge\&logo=html5\&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge\&logo=css3\&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge\&logo=javascript\&logoColor=black)
![C](https://img.shields.io/badge/C-00599C?style=for-the-badge\&logo=c\&logoColor=white)

### Currently Learning

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge\&logo=git\&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge\&logo=github\&logoColor=white)
![Responsive Design](https://img.shields.io/badge/Responsive_Design-0EA5E9?style=for-the-badge)

### Learning Next

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge\&logo=react\&logoColor=61DAFB)

![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge\&logo=node.js\&logoColor=white)

![Express.js](https://img.shields.io/badge/Express.js-000000?style=for-the-badge\&logo=express\&logoColor=white)

![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge\&logo=mongodb\&logoColor=white)

---

## 📂 Featured Projects

### 🌐 Portfolio Website

A responsive personal portfolio showcasing my projects, skills, and development journey.

**Tech:** HTML • CSS • JavaScript

---

### 🧮 Calculator App

A clean calculator application built with vanilla JavaScript to strengthen DOM manipulation and event handling skills.

**Tech:** HTML • CSS • JavaScript

---

### 🎨 CSS Creative Projects

A collection of UI components and creative designs built using only HTML and CSS.

**Tech:** HTML • CSS

> 🚧 More projects are on the way as I continue learning and building.

---

### ✅Completed project 

* Calculator with python code
  
* Other small project is cooming soon.

---

## 📚 Currently Learning

* Large Language Model
  
* Responsive Web Design
  
* Git & GitHub
  
* Python Programming
  
* APIs and JSON
  
* React Fundamentals

---

## 📈 GitHub Stats

<p align="center">
<img src="https://github-readme-stats.vercel.app/api?username=YOUR_USERNAME&show_icons=true&theme=tokyonight" alt="GitHub Stats" />
</p>

<p align="center">
<img src="https://github-readme-streak-stats.herokuapp.com/?user=YOUR_USERNAME&theme=tokyonight" alt="GitHub Streak" />
</p>

---

## 🌟 Beyond Coding

* ⚽ I enjoy watching football and basketball.
* 🎮 I like story-driven PC games such as Red Dead Redemption 2, God of War, and Ghost of Tsushima.
* 💪 Regular exercise helps me stay focused and productive.
* 🌍 I enjoy exploring new places and learning from new experiences.

---

## 📫 Let's Connect

I'm always happy to connect with fellow developers, learners, and mentors.

[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge\&logo=github)](https://github.com/YOUR_USERNAME)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge\&logo=linkedin)](https://linkedin.com/in/YOUR_LINKEDIN)

🌐 Portfolio: **Coming Soon**

---

> *"Every expert was once a beginner. Consistent effort, curiosity, and real projects are what drive growth."* 🚀


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
current_year = today.year

total_contributions = calendar["totalContributions"]

year_contributions = sum(
    d["count"] for d in days
    if d["date"].year == current_year
)


def calculate_streaks(data):
    longest = 0
    current = 0
    best_current = 0

    previous_date = None

    for item in data:
        if item["count"] > 0:
            if (
                previous_date is not None
                and item["date"] == previous_date + timedelta(days=1)
            ):
                current += 1
            else:
                current = 1

            longest = max(longest, current)
            previous_date = item["date"]
        else:
            current = 0
            previous_date = item["date"]

    # Calculate current streak from today backwards.
    current_streak = 0
    check_date = today

    day_lookup = {d["date"]: d["count"] for d in data}

    while day_lookup.get(check_date, 0) > 0:
        current_streak += 1
        check_date -= timedelta(days=1)

    # If today has no contribution, allow yesterday to be the current streak.
    if current_streak == 0:
        check_date = today - timedelta(days=1)

        while day_lookup.get(check_date, 0) > 0:
            current_streak += 1
            check_date -= timedelta(days=1)

    return current_streak, longest


current_streak, longest_streak = calculate_streaks(days)


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------
# Build GitHub-style contribution graph
# ---------------------------------------------------------

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
        f'''
        <rect
            x="{x}"
            y="{y}"
            width="{cell_size}"
            height="{cell_size}"
            rx="3"
            fill="{item["color"]}">
            <title>{item["date"]}: {item["count"]} contributions</title>
        </rect>
        '''
    )

graph_width = ((len(graph_days) // 7) + 1) * (cell_size + cell_gap)

# ---------------------------------------------------------
# SVG
# ---------------------------------------------------------

svg = f'''<svg width="100%" height="330" viewBox="0 0 {max(900, graph_width + 70)} 330"
xmlns="http://www.w3.org/2000/svg">

<rect width="100%" height="100%" rx="16" fill="#0d1117"/>

<!-- Title -->
<text x="30" y="35"
      fill="#f0f6fc"
      font-size="20"
      font-family="Arial, sans-serif"
      font-weight="700">
  GitHub Contribution Stats
</text>

<text x="30" y="58"
      fill="#8b949e"
      font-size="13"
      font-family="Arial, sans-serif">
  @{esc(USERNAME)}
</text>

<!-- Stats -->

<rect x="30" y="75" width="175" height="52" rx="10" fill="#161b22"/>
<text x="43" y="96" fill="#8b949e" font-size="11" font-family="Arial">
  🟩 Total Contributions
</text>
<text x="43" y="116" fill="#f0f6fc" font-size="18" font-weight="700" font-family="Arial">
  {total_contributions:,}
</text>

<rect x="215" y="75" width="175" height="52" rx="10" fill="#161b22"/>
<text x="228" y="96" fill="#8b949e" font-size="11" font-family="Arial">
  🔥 Current Streak
</text>
<text x="228" y="116" fill="#f0f6fc" font-size="18" font-weight="700" font-family="Arial">
  {current_streak} days
</text>

<rect x="400" y="75" width="175" height="52" rx="10" fill="#161b22"/>
<text x="413" y="96" fill="#8b949e" font-size="11" font-family="Arial">
  🏆 Longest Streak
</text>
<text x="413" y="116" fill="#f0f6fc" font-size="18" font-weight="700" font-family="Arial">
  {longest_streak} days
</text>

<rect x="585" y="75" width="175" height="52" rx="10" fill="#161b22"/>
<text x="598" y="96" fill="#8b949e" font-size="11" font-family="Arial">
  📅 This Year
</text>
<text x="598" y="116" fill="#f0f6fc" font-size="18" font-weight="700" font-family="Arial">
  {year_contributions:,}
</text>

<!-- Graph title -->

<text x="30" y="135"
      fill="#f0f6fc"
      font-size="13"
      font-family="Arial"
      font-weight="600">
  📊 Contribution Graph
</text>

<!-- Contribution cells -->

{"".join(svg_cells)}

</svg>
'''

with open("github-contribution-stats.svg", "w", encoding="utf-8") as file:
    file.write(svg)

print("Contribution statistics generated successfully.")
print(f"Total Contributions: {total_contributions}")
print(f"Current Streak: {current_streak}")
print(f"Longest Streak: {longest_streak}")
print(f"Contributions This Year: {year_contributions}")
```

