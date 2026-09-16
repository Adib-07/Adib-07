#!/usr/bin/env python3
"""
Profile automation script for Adib-07/Adib-07.

Generates github-activity.svg from real GitHub contribution data.
Only writes if content actually changes.

Usage:
    python3 scripts/generate-profile.py

Requires: gh CLI authenticated
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
OUTPUT_FILE = ASSETS_DIR / "github-activity.svg"

# Contribution level colors (dark theme)
COLORS_DARK = {
    0: "#161b22",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
}

# Contribution level colors (light theme)
COLORS_LIGHT = {
    0: "#ebedf0",
    1: "#9be9a8",
    2: "#40c463",
    3: "#30a14e",
    4: "#216e39",
}


def check_gh_auth() -> bool:
    """Check if gh CLI is authenticated."""
    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0


def run_gh(args: list[str]) -> str:
    """Run a gh CLI command and return stdout."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        print(f"Warning: gh command failed: {' '.join(args)}", file=sys.stderr)
        print(f"  stderr: {result.stderr}", file=sys.stderr)
        return ""
    return result.stdout.strip()


def get_contribution_data() -> dict:
    """Get contribution counts from GitHub API.

    Returns a dict with real data when authenticated, or a neutral
    fallback with empty contributions when gh auth is unavailable.
    NEVER fabricates statistics.
    """
    if not check_gh_auth():
        print("  GitHub CLI not authenticated. Using neutral fallback.", file=sys.stderr)
        return {
            "login": "Adib-07",
            "contributions": {},
            "repo_count": 0,
            "total_commits": 0,
            "authenticated": False,
        }

    # Get user info
    user_json = run_gh(["api", "user", "--jq", ".login"])
    if not user_json:
        return {
            "login": "Adib-07",
            "contributions": {},
            "repo_count": 0,
            "total_commits": 0,
            "authenticated": False,
        }

    login = user_json

    # Get repository count (single endpoint string, not separate args)
    repos_json = run_gh([
        "api", f"users/{login}/repos",
        "--jq", ".[].name"
    ])
    repo_names = [r.strip() for r in repos_json.split("\n") if r.strip()] if repos_json else []

    # Get contribution calendar (last 52 weeks)
    query = """
    query($login: String!) {
        user(login: $login) {
            contributionsCollection {
                contributionCalendar {
                    weeks {
                        contributionDays {
                            contributionCount
                            date
                        }
                    }
                }
                totalCommitContributions
                restrictedContributionsCount
            }
        }
    }
    """

    result = run_gh([
        "api", "graphql",
        "-f", f"query={query}",
        "-f", f"login={login}",
        "--jq", ".data.user.contributionsCollection.contributionCalendar"
    ])

    contributions = {}
    total_commits = 0

    if result:
        try:
            cal = json.loads(result)
            for week in cal.get("weeks", []):
                for day in week.get("contributionDays", []):
                    date = day["date"]
                    count = day["contributionCount"]
                    contributions[date] = count
                    total_commits += count
        except (json.JSONDecodeError, KeyError):
            pass

    return {
        "login": login,
        "contributions": contributions,
        "repo_names": repo_names,
        "repo_count": len(repo_names),
        "total_commits": total_commits,
        "authenticated": True,
    }


def get_level(count: int) -> int:
    """Map contribution count to level (0-4)."""
    if count == 0:
        return 0
    elif count <= 2:
        return 1
    elif count <= 5:
        return 2
    elif count <= 10:
        return 3
    else:
        return 4


def generate_svg(data: dict) -> str:
    """Generate the github-activity.svg content."""
    today = datetime.now().date()
    # Start from 52 weeks ago, aligned to Sunday
    start = today - timedelta(weeks=52)
    start = start - timedelta(days=start.weekday() + 1)  # Align to Sunday

    # Build grid data
    cells = []
    current = start
    while current <= today:
        date_str = current.isoformat()
        count = data["contributions"].get(date_str, 0)
        level = get_level(count)
        cells.append((current, count, level))
        current += timedelta(days=1)

    # Generate cell elements
    cell_elements = []
    col = 0
    row = 0
    prev_week = None

    for date, count, level in cells:
        week = date.isocalendar()[1]
        if prev_week is not None and week != prev_week:
            col += 1
            row = 0
        prev_week = week

        x = 4 + col * 11
        y = 4 + row * 11

        cell_elements.append(
            f'    <rect x="{x}" y="{y}" width="9" height="9" '
            f'rx="1" class="cell-{level}">'
            f'<title>{date.isoformat()}: {count} contributions</title></rect>'
        )
        row = (row + 1) % 7

    cells_svg = "\n".join(cell_elements)

    # Get repo names from data (already fetched in get_contribution_data)
    repo_names = data.get("repo_names", [])
    repo_count = data.get("repo_count", 0)
    authenticated = data.get("authenticated", False)

    # Determine focus areas
    focus_map = {
        "Civic-eye": "Civic Ops",
        "IMNCI-Safe": "AI/ML",
        "CIRCUVA": "Systems",
        "Jervis": "Local AI",
    }
    focuses = []
    for name in repo_names:
        if name in focus_map:
            focuses.append(focus_map[name])
    focus_text = " · ".join(focuses[:3]) if focuses else "AI · Full-Stack · Systems"

    # Stats section: show real data when authenticated, neutral label when not
    if authenticated:
        repo_stat_value = str(repo_count)
        repo_stat_label = "public"
        focus_label = focus_text
    else:
        repo_stat_value = "—"
        repo_stat_label = "unavailable offline"
        focus_label = "GitHub auth required"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 120" fill="none">
  <style>
    @media (prefers-color-scheme: dark) {{
      .bg {{ fill: #0a0a0f; }}
      .text {{ fill: #e5e7eb; }}
      .text-dim {{ fill: #6b7280; }}
      .text-accent {{ fill: #60a5fa; }}
      .cell-0 {{ fill: #161b22; }}
      .cell-1 {{ fill: #0e4429; }}
      .cell-2 {{ fill: #006d32; }}
      .cell-3 {{ fill: #26a641; }}
      .cell-4 {{ fill: #39d353; }}
      .line {{ stroke: #1a1a2e; }}
      .border {{ stroke: #1a1a2e; fill: none; }}
    }}
    @media (prefers-color-scheme: light) {{
      .bg {{ fill: #fafafa; }}
      .text {{ fill: #1f2937; }}
      .text-dim {{ fill: #9ca3af; }}
      .text-accent {{ fill: #2563eb; }}
      .cell-0 {{ fill: #ebedf0; }}
      .cell-1 {{ fill: #9be9a8; }}
      .cell-2 {{ fill: #40c463; }}
      .cell-3 {{ fill: #30a14e; }}
      .cell-4 {{ fill: #216e39; }}
      .line {{ stroke: #e5e7eb; }}
      .border {{ stroke: #e5e7eb; fill: none; }}
    }}
    text {{ font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', monospace; }}
    .title {{ font-size: 10px; font-weight: 600; letter-spacing: 1.5px; }}
    .label {{ font-size: 7px; }}
    .stat {{ font-size: 9px; font-weight: 600; }}
  </style>

  <rect width="720" height="120" class="bg"/>

  <!-- Title -->
  <text x="20" y="18" class="title text">GITHUB ACTIVITY</text>
  <text x="20" y="30" class="label text-dim">Contributions &amp; repositories</text>

  <!-- Contribution grid -->
  <g transform="translate(20, 42)">
    <rect x="0" y="0" width="520" height="68" rx="2" class="border" stroke-width="0.5"/>
{cells_svg}
  </g>

  <!-- Stats -->
  <g transform="translate(560, 42)">
    <rect width="140" height="68" rx="4" fill="none" class="border" stroke-width="0.5"/>

    <text x="15" y="18" class="label text-dim">REPOSITORIES</text>
    <text x="15" y="32" class="stat text-accent">{repo_stat_value}</text>
    <text x="40" y="32" class="label text-dim">{repo_stat_label}</text>

    <line x1="15" y1="40" x2="125" y2="40" class="line" stroke-width="0.5"/>

    <text x="15" y="54" class="label text-dim">FOCUS AREAS</text>
    <text x="15" y="64" class="label text">{focus_label}</text>
  </g>

  <!-- Legend -->
  <g transform="translate(20, 115)">
    <text x="0" y="0" class="label text-dim">Less</text>
    <rect x="30" y="-7" width="9" height="9" rx="1" class="cell-0"/>
    <rect x="41" y="-7" width="9" height="9" rx="1" class="cell-1"/>
    <rect x="52" y="-7" width="9" height="9" rx="1" class="cell-2"/>
    <rect x="63" y="-7" width="9" height="9" rx="1" class="cell-3"/>
    <rect x="74" y="-7" width="9" height="9" rx="1" class="cell-4"/>
    <text x="90" y="0" class="label text-dim">More</text>
  </g>

</svg>'''

    return svg


def main():
    """Main entry point."""
    print("Generating github-activity.svg...")

    data = get_contribution_data()
    print(f"  User: {data['login']}")
    if data.get("authenticated"):
        print(f"  Repos: {data['repo_count']}")
        print(f"  Total contributions: {data.get('total_commits', 0)}")
    else:
        print("  Repos: — (offline fallback)")
        print("  Total contributions: — (offline fallback)")

    new_content = generate_svg(data)

    # Check if content changed
    if OUTPUT_FILE.exists():
        old_content = OUTPUT_FILE.read_text()
        if old_content == new_content:
            print("  No changes detected. Skipping write.")
            return False

    OUTPUT_FILE.write_text(new_content)
    print(f"  Written to {OUTPUT_FILE}")
    return True


if __name__ == "__main__":
    changed = main()
    sys.exit(0 if changed else 1)
