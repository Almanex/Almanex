import urllib.request
import json
import os
import math
from collections import defaultdict

USERNAME = "Almanex"

def fetch_github_data(token):
    query = """
    query {
      user(login: "%s") {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            stargazerCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                  color
                }
              }
            }
          }
        }
      }
    }
    """ % USERNAME

    req = urllib.request.Request("https://api.github.com/graphql", method="POST")
    req.add_header("Authorization", f"bearer {token}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps({"query": query}).encode("utf-8")
    
    try:
        with urllib.request.urlopen(req, data=data) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def generate_svg(data):
    # If no data (e.g. running locally without token for testing), use mock data
    if not data or "data" not in data or "user" not in data["data"] or data["data"]["user"] is None:
        commits = [int(math.sin(i/2.0)*10 + 10) for i in range(30)]
        total_contribs = 404
        langs = {"C#": {"size": 5000, "color": "#178600"}, "C++": {"size": 3000, "color": "#f34b7d"}}
        total_stars = 42
    else:
        user_data = data["data"]["user"]
        
        # Parse commits (last 30 days)
        weeks = user_data["contributionsCollection"]["contributionCalendar"]["weeks"]
        days = []
        for w in weeks:
            for d in w["contributionDays"]:
                days.append(d["contributionCount"])
        commits = days[-30:] if len(days) >= 30 else days
        total_contribs = user_data["contributionsCollection"]["contributionCalendar"]["totalContributions"]
        
        # Parse languages and stars
        repos = user_data["repositories"]["nodes"]
        langs = defaultdict(lambda: {"size": 0, "color": "#cccccc"})
        total_stars = 0
        
        for r in repos:
            total_stars += r["stargazerCount"]
            for lang_edge in r["languages"]["edges"]:
                name = lang_edge["node"]["name"]
                color = lang_edge["node"]["color"]
                size = lang_edge["size"]
                langs[name]["size"] += size
                langs[name]["color"] = color or "#cccccc"

    # SVG Building
    width = 800
    height = 420
    bg_color = "#111111"
    sidebar_bg = "#1e1e1e"
    grid_color = "#2b2b2b"
    primary_color = "#0078d7" # Windows 11 Blue
    text_color = "#ffffff"
    text_dim = "#aaaaaa"

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    svg += f'<style> text {{ font-family: "Segoe UI", "Ubuntu", "Helvetica Neue", sans-serif; }} </style>'
    svg += f'<rect width="{width}" height="{height}" fill="{bg_color}" rx="8" ry="8"/>'
    
    # Sidebar
    svg += f'<rect width="60" height="{height}" fill="{sidebar_bg}" rx="8" ry="8" />'
    # Sidebar icons (mocked as simple rects/lines)
    svg += f'<rect x="20" y="20" width="20" height="2" fill="{text_dim}" />'
    svg += f'<rect x="20" y="26" width="20" height="2" fill="{text_dim}" />'
    svg += f'<rect x="20" y="32" width="20" height="2" fill="{text_dim}" />'
    
    svg += f'<circle cx="30" cy="80" r="10" stroke="{primary_color}" stroke-width="2" fill="none" />'
    svg += f'<circle cx="30" cy="80" r="4" fill="{primary_color}" />'
    
    # Title
    svg += f'<text x="90" y="40" font-size="24" fill="{text_color}" font-weight="bold">Performance</text>'
    
    # CPU Graph Area
    graph_x = 90
    graph_y = 100
    graph_w = 660
    graph_h = 120
    
    svg += f'<text x="{graph_x}" y="{graph_y - 15}" font-size="16" fill="{text_color}">CPU (Commits - Last 30 Days)</text>'
    svg += f'<rect x="{graph_x}" y="{graph_y}" width="{graph_w}" height="{graph_h}" fill="none" stroke="{primary_color}" stroke-width="1"/>'
    
    # Grid lines
    for i in range(1, 5):
        y = graph_y + (graph_h / 5) * i
        svg += f'<line x1="{graph_x}" y1="{y}" x2="{graph_x + graph_w}" y2="{y}" stroke="{grid_color}" stroke-width="1" />'
    for i in range(1, 10):
        x = graph_x + (graph_w / 10) * i
        svg += f'<line x1="{x}" y1="{graph_y}" x2="{x}" y2="{graph_y + graph_h}" stroke="{grid_color}" stroke-width="1" />'
        
    # Plot commits
    max_commits = max(commits) if commits and max(commits) > 0 else 10
    points = []
    if not commits: commits = [0]*30
    for i, val in enumerate(commits):
        px = graph_x + (i / max(1, len(commits) - 1)) * graph_w
        py = graph_y + graph_h - (val / max_commits) * graph_h
        points.append(f"{px},{py}")
    
    # Area under curve
    poly_points = f"{graph_x},{graph_y+graph_h} " + " ".join(points) + f" {graph_x+graph_w},{graph_y+graph_h}"
    svg += f'<polygon points="{poly_points}" fill="{primary_color}" fill-opacity="0.2" />'
    
    # Line
    line_points = " ".join(points)
    svg += f'<polyline points="{line_points}" fill="none" stroke="{primary_color}" stroke-width="2" />'
    
    # Memory (Languages) Area
    mem_y = graph_y + graph_h + 50
    svg += f'<text x="{graph_x}" y="{mem_y - 15}" font-size="16" fill="{text_color}">Memory (Top Languages)</text>'
    
    bar_h = 24
    svg += f'<rect x="{graph_x}" y="{mem_y}" width="{graph_w}" height="{bar_h}" fill="{sidebar_bg}" />'
    
    total_size = sum(l["size"] for l in langs.values())
    if total_size == 0: total_size = 1
    
    # Sort langs
    sorted_langs = sorted(langs.items(), key=lambda x: x[1]["size"], reverse=True)
    
    curr_x = graph_x
    legend_x = graph_x
    legend_y = mem_y + bar_h + 30
    
    for i, (name, info) in enumerate(sorted_langs[:6]): # Top 6
        width_px = (info["size"] / total_size) * graph_w
        color = info["color"]
        # Bar segment
        svg += f'<rect x="{curr_x}" y="{mem_y}" width="{width_px}" height="{bar_h}" fill="{color}" />'
        curr_x += width_px
        
        # Legend
        svg += f'<circle cx="{legend_x + 5}" cy="{legend_y - 5}" r="5" fill="{color}" />'
        svg += f'<text x="{legend_x + 15}" y="{legend_y}" font-size="14" fill="{text_color}">{name}</text>'
        legend_x += 120
        if (i+1) % 3 == 0:
            legend_x = graph_x
            legend_y += 25
            
    # Stats summary
    stats_x = graph_x + 400
    stats_y = mem_y + bar_h + 30
    svg += f'<text x="{stats_x}" y="{stats_y}" font-size="14" fill="{text_dim}">Total Commits (1 Year):</text>'
    svg += f'<text x="{stats_x + 150}" y="{stats_y}" font-size="14" fill="{text_color}" font-weight="bold">{total_contribs}</text>'
    
    svg += f'<text x="{stats_x}" y="{stats_y + 25}" font-size="14" fill="{text_dim}">Stars Earned:</text>'
    svg += f'<text x="{stats_x + 150}" y="{stats_y + 25}" font-size="14" fill="{text_color}" font-weight="bold">{total_stars}</text>'

    svg += '</svg>'
    
    # Ensure dist folder exists
    os.makedirs("dist", exist_ok=True)
    with open("dist/task-manager.svg", "w", encoding="utf-8") as f:
        f.write(svg)

if __name__ == "__main__":
    token = os.environ.get("GITHUB_TOKEN")
    data = None
    if token:
        print("Fetching data from GitHub API...")
        data = fetch_github_data(token)
    else:
        print("No GITHUB_TOKEN found. Using mock data for generation.")
        
    print("Generating SVG...")
    generate_svg(data)
    print("Done! Saved to dist/task-manager.svg")
