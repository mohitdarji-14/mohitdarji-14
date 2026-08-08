import os
import sys
import json
import math
import datetime
import urllib.request
import urllib.error

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "")

if not GITHUB_TOKEN or not GITHUB_USERNAME:
    print("Error: GITHUB_TOKEN and GITHUB_USERNAME environment variables must be set.")
    sys.exit(1)

GRAPHQL_QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

def fetch_contributions():
    today = datetime.date.today()
    from_date = today - datetime.timedelta(days=364)
    from_dt = datetime.datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0)
    to_dt = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)

    payload = json.dumps({
        "query": GRAPHQL_QUERY,
        "variables": {
            "username": GITHUB_USERNAME,
            "from": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "github-stats-script",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"Network error: {e}")
        sys.exit(1)

    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}")
        sys.exit(1)

    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    contributions = []
    for week in weeks:
        for day in week["contributionDays"]:
            contributions.append({
                "date": day["date"],
                "count": day["contributionCount"],
            })

    contributions.sort(key=lambda x: x["date"])
    return contributions


def escape_xml(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def nice_max(raw_max):
    """Round up to a nice number for the y-axis."""
    if raw_max <= 0:
        return 10
    magnitude = 10 ** math.floor(math.log10(raw_max))
    candidates = [magnitude * m for m in [1, 2, 5, 10]]
    for c in candidates:
        if c >= raw_max:
            return c
    return candidates[-1]


def generate_svg(contributions):
    # ------- Canvas -------
    SVG_W = 900
    SVG_H = 280

    # ------- Outer card padding -------
    CARD_PX = 20   # left/right padding of card
    CARD_PY = 16   # top/bottom padding of card

    # ------- Title -------
    TITLE_H = 32   # height reserved for title above chart panel

    # ------- Chart panel (inset box) -------
    PANEL_X = CARD_PX
    PANEL_Y = CARD_PY + TITLE_H
    PANEL_W = SVG_W - CARD_PX * 2
    PANEL_H = SVG_H - CARD_PY * 2 - TITLE_H

    # ------- Chart area inside panel -------
    Y_LABEL_W = 36   # width for y-axis tick labels
    X_LABEL_H = 32  # height for x-axis tick labels
    YAXIS_TITLE_W = 18  # width for rotated "Contributions" label
    XAXIS_TITLE_H = 16  # height for "Date" label below x labels

    INNER_PAD_TOP = 12
    INNER_PAD_RIGHT = 14

    chart_x = PANEL_X + YAXIS_TITLE_W + Y_LABEL_W
    chart_y = PANEL_Y + INNER_PAD_TOP
    chart_w = PANEL_W - YAXIS_TITLE_W - Y_LABEL_W - INNER_PAD_RIGHT
    chart_h = PANEL_H - INNER_PAD_TOP - X_LABEL_H - XAXIS_TITLE_H

    # ------- Colors -------
    SVG_BG       = "#0d1117"
    CARD_BG      = "#0d1117"
    PANEL_BG     = "#010409"
    PANEL_BORDER = "#21262d"
    CARD_BORDER  = "#30363d"
    TITLE_CLR    = "#e6edf3"
    GRID_CLR     = "#21262d"
    AXIS_CLR     = "#8b949e"
    LABEL_CLR    = "#8b949e"
    LINE_CLR     = "#3fb950"
    FONT         = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

    # ------- Y axis -------
    counts = [d["count"] for d in contributions]
    raw_max = max(counts) if counts else 0
    y_max = nice_max(raw_max)

    # Build nice y ticks: 0, 2, 4, 6, 8, 10 style
    # Choose step so we get ~5-6 ticks
    for step_candidate in [1, 2, 5, 10, 20, 50, 100, 200, 500]:
        num_ticks = y_max // step_candidate
        if 4 <= num_ticks <= 7:
            y_step = step_candidate
            break
    else:
        y_step = max(1, y_max // 5)

    y_ticks = list(range(0, y_max + 1, y_step))
    if y_ticks[-1] < y_max:
        y_ticks.append(y_max)

    def y_pos(val):
        return chart_y + chart_h - (val / y_max) * chart_h

    # ------- X axis -------
    n = len(contributions)

    def x_pos(i):
        if n <= 1:
            return chart_x + chart_w / 2
        return chart_x + (i / (n - 1)) * chart_w

    # Generate x labels every ~14 days
    x_labels = []
    if contributions:
        # find indices where we want labels (roughly every 14 days)
        start_date = datetime.date.fromisoformat(contributions[0]["date"])
        for i, day in enumerate(contributions):
            d = datetime.date.fromisoformat(day["date"])
            delta = (d - start_date).days
            if delta % 14 == 0:
                label = d.strftime("%b %d")
                x_labels.append((x_pos(i), label))

    # ------- Build SVG -------
    out = []

    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SVG_W} {SVG_H}" '
        f'width="{SVG_W}" height="{SVG_H}" '
        f'role="img" aria-label="Contributions Over Time">'
    )

    # clip path for chart area
    out.append(
        f'  <defs>'
        f'<clipPath id="cp">'
        f'<rect x="{chart_x}" y="{chart_y}" width="{chart_w}" height="{chart_h}"/>'
        f'</clipPath>'
        f'</defs>'
    )

    # Outer card background + border
    out.append(
        f'  <rect width="{SVG_W}" height="{SVG_H}" rx="10" ry="10" '
        f'fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="1"/>'
    )

    # Title — top left
    out.append(
        f'  <text x="{CARD_PX}" y="{CARD_PY + 20}" '
        f'font-family="{FONT}" font-size="15" font-weight="700" '
        f'fill="{TITLE_CLR}">Contributions Over Time</text>'
    )

    # Chart panel (inset dark box)
    out.append(
        f'  <rect x="{PANEL_X}" y="{PANEL_Y}" '
        f'width="{PANEL_W}" height="{PANEL_H}" '
        f'rx="6" ry="6" fill="{PANEL_BG}" '
        f'stroke="{PANEL_BORDER}" stroke-width="1"/>'
    )

    # Horizontal grid lines + y-axis tick labels
    for tick in y_ticks:
        yp = y_pos(tick)
        # grid line (inside chart area only)
        out.append(
            f'  <line x1="{chart_x:.2f}" y1="{yp:.2f}" '
            f'x2="{chart_x + chart_w:.2f}" y2="{yp:.2f}" '
            f'stroke="{GRID_CLR}" stroke-width="1"/>'
        )
        # y-axis label
        out.append(
            f'  <text x="{chart_x - 6:.2f}" y="{yp + 4:.2f}" '
            f'text-anchor="end" font-family="{FONT}" font-size="10" '
            f'fill="{LABEL_CLR}">{escape_xml(tick)}</text>'
        )

    # Rotated "Contributions" label on y-axis
    yl_x = PANEL_X + YAXIS_TITLE_W - 4
    yl_y = chart_y + chart_h / 2
    out.append(
        f'  <text x="{yl_x:.2f}" y="{yl_y:.2f}" '
        f'text-anchor="middle" '
        f'font-family="{FONT}" font-size="10" fill="{AXIS_CLR}" '
        f'transform="rotate(-90 {yl_x:.2f} {yl_y:.2f})">Contributions</text>'
    )

    # Bottom axis line
    out.append(
        f'  <line x1="{chart_x:.2f}" y1="{chart_y + chart_h:.2f}" '
        f'x2="{chart_x + chart_w:.2f}" y2="{chart_y + chart_h:.2f}" '
        f'stroke="{PANEL_BORDER}" stroke-width="1"/>'
    )

    # Left axis line
    out.append(
        f'  <line x1="{chart_x:.2f}" y1="{chart_y:.2f}" '
        f'x2="{chart_x:.2f}" y2="{chart_y + chart_h:.2f}" '
        f'stroke="{PANEL_BORDER}" stroke-width="1"/>'
    )

    # Right border line
    out.append(
        f'  <line x1="{chart_x + chart_w:.2f}" y1="{chart_y:.2f}" '
        f'x2="{chart_x + chart_w:.2f}" y2="{chart_y + chart_h:.2f}" '
        f'stroke="{PANEL_BORDER}" stroke-width="1"/>'
    )

    # Contribution line (clipped)
    if n > 0:
        pts = []
        for i, day in enumerate(contributions):
            px = x_pos(i)
            py = y_pos(day["count"])
            pts.append(f"{px:.2f},{py:.2f}")
        points_str = " ".join(pts)
        out.append(
            f'  <polyline points="{points_str}" '
            f'fill="none" stroke="{LINE_CLR}" stroke-width="1.5" '
            f'stroke-linejoin="miter" stroke-linecap="round" '
            f'clip-path="url(#cp)"/>'
        )

    # X-axis tick labels
    xlabel_y = chart_y + chart_h + 16
    for lx, ltxt in x_labels:
        out.append(
            f'  <text x="{lx:.2f}" y="{xlabel_y:.2f}" '
            f'text-anchor="middle" font-family="{FONT}" font-size="9.5" '
            f'fill="{LABEL_CLR}">{escape_xml(ltxt)}</text>'
        )

    # "Date" label centered under x-axis
    date_label_y = chart_y + chart_h + X_LABEL_H + XAXIS_TITLE_H - 2
    date_label_x = chart_x + chart_w / 2
    out.append(
        f'  <text x="{date_label_x:.2f}" y="{date_label_y:.2f}" '
        f'text-anchor="middle" font-family="{FONT}" font-size="10" '
        f'fill="{AXIS_CLR}">Date</text>'
    )

    out.append('</svg>')
    return "\n".join(out)


def main():
    print(f"Fetching contributions for {GITHUB_USERNAME}...")
    contributions = fetch_contributions()
    print(f"Fetched {len(contributions)} days of data.")

    svg_content = generate_svg(contributions)

    output_path = "github-contribution-stats.svg"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"SVG written to {output_path}")


if __name__ == "__main__":
    main()
