import { useState, useCallback } from "react";

const GITHUB_GRAPHQL = "https://api.github.com/graphql";

const QUERY = `
query($login: String!) {
  user(login: $login) {
    name
    avatarUrl
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
}`;

function calcStreaks(days) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const lookup = {};
  days.forEach(d => { lookup[d.date] = d.count; });

  let longest = 0, streak = 0, prevDate = null;
  for (const d of days) {
    const cur = new Date(d.date + "T00:00:00");
    if (d.count > 0) {
      if (prevDate && cur - prevDate === 86400000) streak++;
      else streak = 1;
      longest = Math.max(longest, streak);
      prevDate = cur;
    } else {
      streak = 0;
      prevDate = cur;
    }
  }

  let current = 0;
  let check = new Date(today);
  while (true) {
    const key = check.toISOString().slice(0, 10);
    if (lookup[key] > 0) { current++; check.setDate(check.getDate() - 1); }
    else break;
  }
  if (current === 0) {
    check = new Date(today);
    check.setDate(check.getDate() - 1);
    while (true) {
      const key = check.toISOString().slice(0, 10);
      if (lookup[key] > 0) { current++; check.setDate(check.getDate() - 1); }
      else break;
    }
  }

  return { current, longest };
}

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const DAYS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

export default function App() {
  const [username, setUsername] = useState("");
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);
  const [tooltip, setTooltip] = useState(null);

  const fetch_ = useCallback(async () => {
    if (!username.trim() || !token.trim()) {
      setError("Both username and token are required.");
      return;
    }
    setLoading(true);
    setError("");
    setData(null);
    try {
      const res = await fetch(GITHUB_GRAPHQL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token.trim()}`
        },
        body: JSON.stringify({ query: QUERY, variables: { login: username.trim() } })
      });
      const json = await res.json();
      if (json.errors) throw new Error(json.errors[0].message);
      if (!json.data?.user) throw new Error("User not found.");

      const cal = json.data.user.contributionsCollection.contributionCalendar;
      const days = [];
      for (const week of cal.weeks)
        for (const day of week.contributionDays)
          days.push({ date: day.date, count: day.contributionCount, color: day.color });
      days.sort((a, b) => a.date.localeCompare(b.date));

      const todayStr = new Date().toISOString().slice(0, 10);
      const thisYear = new Date().getFullYear();
      const yearContribs = days.filter(d => d.date.startsWith(thisYear)).reduce((s, d) => s + d.count, 0);
      const streaks = calcStreaks(days);

      setData({
        name: json.data.user.name || username.trim(),
        avatar: json.data.user.avatarUrl,
        total: cal.totalContributions,
        yearContribs,
        streaks,
        days: days.slice(-371)
      });
    } catch (e) {
      setError(e.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }, [username, token]);

  const cellSize = 12;
  const cellGap = 3;
  const step = cellSize + cellGap;

  const renderGraph = () => {
    if (!data) return null;
    const days = data.days;
    const weeks = [];
    for (let i = 0; i < days.length; i += 7) weeks.push(days.slice(i, i + 7));

    const monthLabels = [];
    let lastMonth = -1;
    weeks.forEach((week, wi) => {
      const firstDay = week[0];
      const mo = new Date(firstDay.date + "T00:00:00").getMonth();
      if (mo !== lastMonth) {
        monthLabels.push({ wi, label: MONTHS[mo] });
        lastMonth = mo;
      }
    });

    const svgW = weeks.length * step + 30;
    const svgH = 7 * step + 30;

    return (
      <div style={{ overflowX: "auto", marginTop: 4 }}>
        <svg width={svgW} height={svgH} style={{ display: "block" }}>
          {monthLabels.map(({ wi, label }) => (
            <text key={wi} x={30 + wi * step} y={10} fontSize={10} fill="var(--text-muted)" fontFamily="inherit">{label}</text>
          ))}
          {weeks.map((week, wi) =>
            week.map((day, di) => {
              const x = 30 + wi * step;
              const y = 16 + di * step;
              const fill = day.color === "#ebedf0" ? "var(--border-strong)" : day.color;
              return (
                <rect
                  key={day.date}
                  x={x} y={y}
                  width={cellSize} height={cellSize}
                  rx={2}
                  fill={fill}
                  style={{ cursor: "pointer" }}
                  onMouseEnter={e => setTooltip({ x: e.clientX, y: e.clientY, date: day.date, count: day.count })}
                  onMouseLeave={() => setTooltip(null)}
                />
              );
            })
          )}
          {[0,1,3,5].map(di => (
            <text key={di} x={0} y={16 + di * step + cellSize - 2} fontSize={9} fill="var(--text-muted)" fontFamily="inherit">{DAYS[di]}</text>
          ))}
        </svg>
        {tooltip && (
          <div style={{
            position: "fixed", left: tooltip.x + 10, top: tooltip.y - 36,
            background: "var(--surface-2)", border: "0.5px solid var(--border-strong)",
            borderRadius: "var(--radius)", padding: "4px 8px",
            fontSize: 12, color: "var(--text-primary)", pointerEvents: "none",
            zIndex: 9999, whiteSpace: "nowrap"
          }}>
            <strong>{tooltip.count}</strong> contribution{tooltip.count !== 1 ? "s" : ""} on {tooltip.date}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ padding: "1.5rem 0", maxWidth: 720, fontFamily: "var(--font-sans)" }}>
      <h2 style={{ fontSize: 18, fontWeight: 500, margin: "0 0 1.25rem", color: "var(--text-primary)" }}>
        GitHub contribution stats
      </h2>

      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: "1.25rem" }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input
            type="text"
            placeholder="GitHub username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            onKeyDown={e => e.key === "Enter" && fetch_()}
            style={{ flex: 1, minWidth: 140 }}
          />
          <div style={{ position: "relative", flex: 2, minWidth: 200 }}>
            <input
              type={showToken ? "text" : "password"}
              placeholder="Personal access token"
              value={token}
              onChange={e => setToken(e.target.value)}
              onKeyDown={e => e.key === "Enter" && fetch_()}
              style={{ width: "100%", paddingRight: 36, boxSizing: "border-box" }}
            />
            <button
              onClick={() => setShowToken(s => !s)}
              style={{ position: "absolute", right: 6, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", padding: 4, cursor: "pointer", color: "var(--text-muted)" }}
              aria-label={showToken ? "Hide token" : "Show token"}
            >
              <i className={`ti ${showToken ? "ti-eye-off" : "ti-eye"}`} style={{ fontSize: 16 }} aria-hidden="true" />
            </button>
          </div>
          <button onClick={fetch_} disabled={loading} style={{ whiteSpace: "nowrap" }}>
            {loading ? "Loading…" : "Load stats ↗"}
          </button>
        </div>
        {error && <p style={{ fontSize: 13, color: "var(--text-danger)", margin: 0 }}>{error}</p>}
        <p style={{ fontSize: 12, color: "var(--text-muted)", margin: 0 }}>
          Token needs <code>read:user</code> scope. <a href="https://github.com/settings/tokens/new?scopes=read:user" style={{ color: "var(--text-accent)" }}>Create one on GitHub ↗</a>
        </p>
      </div>

      {data && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {data.avatar && <img src={data.avatar} alt="" width={40} height={40} style={{ borderRadius: "50%", border: "0.5px solid var(--border)" }} />}
            <div>
              <p style={{ margin: 0, fontWeight: 500, color: "var(--text-primary)" }}>{data.name}</p>
              <p style={{ margin: 0, fontSize: 13, color: "var(--text-muted)" }}>@{username.trim()}</p>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10 }}>
            {[
              { label: "Total contributions", value: data.total.toLocaleString() },
              { label: "This year", value: data.yearContribs.toLocaleString() },
              { label: "Current streak", value: `${data.streaks.current} days` },
              { label: "Longest streak", value: `${data.streaks.longest} days` },
            ].map(({ label, value }) => (
              <div key={label} style={{ background: "var(--surface-1)", borderRadius: "var(--radius)", padding: "0.875rem 1rem" }}>
                <p style={{ margin: "0 0 4px", fontSize: 12, color: "var(--text-muted)" }}>{label}</p>
                <p style={{ margin: 0, fontSize: 22, fontWeight: 500, color: "var(--text-primary)" }}>{value}</p>
              </div>
            ))}
          </div>

          <div style={{ background: "var(--surface-1)", borderRadius: "var(--radius)", padding: "1rem 1.25rem" }}>
            <p style={{ margin: "0 0 8px", fontSize: 13, fontWeight: 500, color: "var(--text-secondary)" }}>Contribution graph</p>
            {renderGraph()}
            <div style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 8, justifyContent: "flex-end" }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Less</span>
              {["#ebedf0","#9be9a8","#40c463","#30a14e","#216e39"].map(c => (
                <div key={c} style={{ width: 11, height: 11, borderRadius: 2, background: c === "#ebedf0" ? "var(--border-strong)" : c }} />
              ))}
              <span style={{ fontSize: 11, color: "var(--text-muted)" }}>More</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
