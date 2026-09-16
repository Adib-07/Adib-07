#!/usr/bin/env python3
"""
Progressive ASCII Portrait Generator for GitHub Profile.

Converts a source photo into a self-contained animated SVG that
progressively reveals an ASCII/terminal portrait through 7 stages.

Usage:
    python3 scripts/generate-profile-portrait.py

Requires: Pillow (pip install Pillow)
"""

import math
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# Paths
REPO_ROOT = Path(__file__).parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
SOURCE_IMG = ASSETS_DIR / "adib-source.png"
OUTPUT_SVG = ASSETS_DIR / "adib-generating.svg"

# Portrait grid dimensions
COLS = 50
ROWS = 58
FONT_SIZE = 14
CHAR_W = FONT_SIZE * 0.6
CHAR_H = FONT_SIZE
SVG_W = 760
MARGIN_TOP = 110
MARGIN_BOTTOM = 100
SVG_H = MARGIN_TOP + ROWS * CHAR_H + MARGIN_BOTTOM

# ASCII density palette: brightest (index 0) to darkest (index 9)
CHARS = " .:-=+*#%@"
NUM_TIERS = len(CHARS)

# Animation: (delay_seconds, duration_seconds)
STAGE_TIMING = [
    (0.0, 2.0),   # Stage 0: particles
    (0.6, 1.8),   # Stage 1: silhouette
    (1.2, 1.6),   # Stage 2: head
    (1.8, 1.4),   # Stage 3: features
    (2.4, 1.2),   # Stage 4: detail
    (3.0, 1.0),   # Stage 5: refinement
]
FINAL_DELAY = 3.6

# Status messages for terminal HUD
STATUS_MSGS = [
    (0.0,  "> GENERATING PROFILE"),
    (0.5,  "> LOADING IDENTITY..."),
    (1.0,  "> CONSTRUCTING SILHOUETTE..."),
    (1.6,  "> MAPPING FACIAL STRUCTURE..."),
    (2.2,  "> RENDERING FEATURES..."),
    (2.8,  "> REFINING DETAILS..."),
    (3.5,  "> PROFILE READY"),
]

# HUD status lines: (appear_time, label, value)
HUD_LINES = [
    (0.0,  "IDENTITY",  "INITIALIZING"),
    (0.8,  "STRUCTURE", "PROCESSING"),
    (1.6,  "DETAILS",   "PROCESSING"),
    (2.4,  "RENDER",    "PROCESSING"),
    (3.5,  "IDENTITY",  "OK"),
    (3.5,  "STRUCTURE", "OK"),
    (3.5,  "DETAILS",   "OK"),
    (3.5,  "RENDER",    "OK"),
]

# Progress bar: (appear_time, filled_segments_out_of_10, pct_text)
PROGRESS_STEPS = [
    (0.0,  1,  "10%"),
    (1.0,  4,  "35%"),
    (1.8,  6,  "55%"),
    (2.6,  8,  "75%"),
    (3.4,  9,  "92%"),
    (3.8,  10, "100%"),
]


def process_image(src: Path) -> tuple[list[list[float]], list[float]]:
    """Read source image, convert to grayscale, resize to character grid.

    Returns (grid, thresholds) where thresholds are the luminance boundaries
    for each ASCII character tier, computed from the image's actual distribution.
    """
    img = Image.open(src).convert("RGB")
    orig_w, orig_h = img.size
    aspect = orig_h / orig_w
    grid_h = int(COLS * aspect * 0.55)
    grid_h = max(grid_h, 30)
    grid_h = min(grid_h, ROWS)

    img = img.resize((COLS, grid_h), Image.Resampling.LANCZOS)
    pixels = list(img.getdata())

    grid = []
    all_lums = []
    for r in range(grid_h):
        row = []
        for c in range(COLS):
            ri, gi, bi = pixels[r * COLS + c]
            lum = (0.299 * ri + 0.587 * gi + 0.114 * bi) / 255.0
            row.append(lum)
            all_lums.append(lum)
        grid.append(row)

    while len(grid) < ROWS:
        grid.append([1.0] * COLS)

    # Compute percentile-based thresholds for even character distribution
    all_lums.sort()
    thresholds = []
    for i in range(1, NUM_TIERS):
        idx = int(i * len(all_lums) / NUM_TIERS)
        thresholds.append(all_lums[min(idx, len(all_lums) - 1)])
    thresholds.append(1.01)  # Upper bound

    return grid[:ROWS], thresholds


def lum_to_char(lum: float, thresholds: list[float]) -> str:
    """Map luminance to ASCII character using percentile-based thresholds."""
    for i, t in enumerate(thresholds):
        if lum < t:
            return CHARS[i]
    return CHARS[-1]


def char_tier(ch: str) -> int:
    """Return density tier index for a character."""
    return CHARS.index(ch) if ch in CHARS else 0


def generate_stages(grid: list[list[float]], thresholds: list[float]) -> list[list[str]]:
    """Create 7 progressive reveal stages using center-outward spatial ordering.

    Stage 0: sparsest particles near face center
    Stage 1-5: expanding outward with increasing density
    Stage 6: complete portrait
    """
    cx, cy = COLS / 2.0, ROWS * 0.42

    # Build full character grid and compute distances
    cells = []
    for r in range(ROWS):
        for c in range(COLS):
            ch = lum_to_char(grid[r][c], thresholds)
            dist = math.sqrt((c - cx) ** 2 + (r - cy) ** 2)
            cells.append((dist, r, c, ch))

    # Sort by distance from face center (innermost first)
    cells.sort(key=lambda x: x[0])
    max_dist = cells[-1][0] if cells else 1.0

    total = len(cells)
    stages = []

    # Stages 0-5: progressive reveal from center outward
    # Each stage reveals a larger radius, with ~14% more characters
    for s in range(6):
        # Reveal characters up to this radius percentage
        radius_pct = (s + 1) / 7.0
        max_radius = radius_pct * max_dist
        revealed = set()
        for dist, r, c, ch in cells:
            if dist <= max_radius:
                revealed.add((r, c, ch))

        stage_lines = []
        for r in range(ROWS):
            line = []
            for c in range(COLS):
                found = None
                for rr, rc, ch in revealed:
                    if rr == r and rc == c:
                        found = ch
                        break
                line.append(found if found else " ")
            stage_lines.append("".join(line))
        stages.append(stage_lines)

    # Stage 6: complete portrait
    complete_lines = []
    for r in range(ROWS):
        line = []
        for c in range(COLS):
            ch = lum_to_char(grid[r][c], thresholds)
            line.append(ch)
        complete_lines.append("".join(line))
    stages.append(complete_lines)

    return stages


def build_svg(stages: list[list[str]]) -> str:
    """Build the complete animated SVG string using multi-line text blocks."""
    lines = []

    def w(s: str) -> None:
        lines.append(s)

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    gx = round((SVG_W - COLS * CHAR_W) / 2, 1)
    gy = MARGIN_TOP
    text_x = round(gx + CHAR_W / 2, 1)

    # SVG header
    w(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {SVG_H}">')
    w('  <style>')
    w('    text { font-family: \'SF Mono\', \'Cascadia Code\', \'Fira Code\', Consolas, monospace; }')
    w('    .h { fill: #8b949e; font-size: 12px; letter-spacing: 1px; }')
    w('    .s { fill: #58a6ff; font-size: 12px; letter-spacing: 1px; }')
    w('    .ok { fill: #238636; font-size: 12px; letter-spacing: 1px; }')
    w('    .proc { fill: #8b949e; font-size: 12px; letter-spacing: 1px; }')
    w('    .nm { fill: #e6edf3; font-size: 22px; font-weight: 700; letter-spacing: 4px; }')
    w('    .rl { fill: #8b949e; font-size: 11px; letter-spacing: 2px; }')
    w('    .dim { fill: #30363d; font-size: 11px; letter-spacing: 1px; }')
    w('    .bar { fill: #1f6feb; }')
    w('  </style>')

    # Background
    w(f'  <rect width="{SVG_W}" height="{SVG_H}" fill="#0d1117"/>')

    # === HUD HEADER ===
    w(f'  <text x="20" y="35" class="h">&gt; GENERATING PROFILE</text>')

    # Status messages: fade in, hold, fade out, then next message takes over
    msg_interval = 0.5
    msg_fade = 0.3
    msg_hold = 0.7
    for i, (_, msg) in enumerate(STATUS_MSGS):
        t_start = round(i * msg_interval, 2)
        t_fo_start = round(t_start + msg_fade + msg_hold, 2)
        t_end = round(t_fo_start + msg_fade, 2)
        total_dur = round(t_end - t_start, 2)
        kf_fi = round(msg_fade / total_dur, 3)
        kf_fo = round(t_fo_start / total_dur, 3)
        if i == len(STATUS_MSGS) - 1:
            # Final message: fade in and stay
            w(f'  <text x="20" y="55" class="s" opacity="0" '
              f'begin="{t_start}s" dur="{total_dur}s" fill="freeze">')
            w(f'    <animate attributeName="opacity" values="0;1;1" '
              f'keyTimes="0;{kf_fi};1" dur="{total_dur}s" begin="{t_start}s" fill="freeze"/>')
            w(f'{esc(msg)}</text>')
        else:
            # Other messages: fade in, hold, fade out
            w(f'  <text x="20" y="55" class="s" opacity="0" '
              f'begin="{t_start}s" dur="{total_dur}s" fill="freeze">')
            w(f'    <animate attributeName="opacity" values="0;1;1;0" '
              f'keyTimes="0;{kf_fi};{kf_fo};1" dur="{total_dur}s" begin="{t_start}s" fill="freeze"/>')
            w(f'{esc(msg)}</text>')

    # === PROGRESS BAR ===
    bar_x, bar_y, bar_w, bar_h = 20, 72, 250, 12
    w(f'  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" '
      f'rx="2" fill="#161b22" stroke="#30363d" stroke-width="0.5"/>')

    seg_w = (bar_w - 4) / 10
    for seg in range(10):
        sx = round(bar_x + 2 + seg * seg_w, 1)
        sw = round(seg_w - 1, 1)
        # Find the time when this segment should appear
        appear_time = 0.0
        for pt, filled, _ in PROGRESS_STEPS:
            if seg < filled:
                appear_time = pt
                break
        else:
            appear_time = PROGRESS_STEPS[-1][0]

        w(f'  <rect x="{sx}" y="{bar_y + 2}" width="{sw}" height="{bar_h - 4}" '
          f'rx="1" class="bar" opacity="0" begin="{appear_time}s" dur="0.4s" fill="freeze"/>')

    # Percentage text
    for pt, _, pct in PROGRESS_STEPS:
        w(f'  <text x="{bar_x + bar_w + 10}" y="{bar_y + 10}" class="dim" '
          f'opacity="0" begin="{pt}s" dur="0.3s" fill="freeze">{pct}</text>')

    # === HUD STATUS LINES ===
    hx = SVG_W - 180
    for i, (bt, label, value) in enumerate(HUD_LINES):
        hy = 35 + i * 16
        is_ok = value == "OK"
        cls = "ok" if is_ok else "proc"
        w(f'  <text x="{hx}" y="{hy}" class="proc" opacity="0" '
          f'begin="{bt}s" dur="0.3s" fill="freeze">{esc(label)} ............. </text>')
        w(f'  <text x="{hx + 120}" y="{hy}" class="{cls}" opacity="0" '
          f'begin="{bt}s" dur="0.3s" fill="freeze">{esc(value)}</text>')

    # === PORTRAIT FRAME ===
    frame_x = gx - 12
    frame_y = gy - 12
    frame_w = COLS * CHAR_W + 24
    frame_h = ROWS * CHAR_H + 24
    w(f'  <rect x="{frame_x}" y="{frame_y}" width="{frame_w}" height="{frame_h}" '
      f'rx="4" fill="#0d1117" stroke="#30363d" stroke-width="0.5"/>')

    # Corner brackets
    for cx, cy, dx, dy in [
        (frame_x, frame_y, 8, 8),
        (frame_x + frame_w, frame_y, -8, 8),
        (frame_x, frame_y + frame_h, 8, -8),
        (frame_x + frame_w, frame_y + frame_h, -8, -8),
    ]:
        w(f'  <path d="M{cx} {cy + dy} L{cx} {cy} L{cx + dx} {cy}" '
          f'fill="none" stroke="#1f6feb" stroke-width="0.8" opacity="0.4"/>')

    # === PORTRAIT: STAGES 0-5 (animated groups) ===
    for si in range(6):
        delay, dur = STAGE_TIMING[si]
        stage_text = "\n".join(stages[si])
        w(f'  <g opacity="0" begin="{delay}s" dur="{dur}s" fill="freeze">')
        w(f'    <text x="{text_x}" y="{gy}" font-size="{FONT_SIZE}" '
          f'fill="#e6edf3" xml:space="preserve"><tspan x="{text_x}" dy="0">')
        for ri, row_text in enumerate(stages[si]):
            escaped = esc(row_text)
            if ri == 0:
                w(f'{escaped}</tspan>')
            else:
                w(f'<tspan x="{text_x}" dy="{CHAR_H}">{escaped}</tspan>')
        w(f'    </text>')
        w('  </g>')

    # === PORTRAIT: STAGE 6 (final, always visible) ===
    w(f'  <g>')
    w(f'    <text x="{text_x}" y="{gy}" font-size="{FONT_SIZE}" '
      f'fill="#e6edf3" xml:space="preserve"><tspan x="{text_x}" dy="0">')
    for ri, row_text in enumerate(stages[6]):
        escaped = esc(row_text)
        if ri == 0:
            w(f'{escaped}</tspan>')
        else:
            w(f'<tspan x="{text_x}" dy="{CHAR_H}">{escaped}</tspan>')
    w(f'    </text>')
    w('  </g>')

    # === SCAN LINE ===
    scan_top = frame_y
    scan_bot = frame_y + frame_h
    w(f'  <line x1="{frame_x}" y1="{scan_top}" x2="{frame_x + frame_w}" y2="{scan_top}" '
      f'stroke="#1f6feb" stroke-width="0.5" opacity="0.2">')
    w(f'    <animate attributeName="y1" values="{scan_top};{scan_bot};{scan_top}" dur="6s" repeatCount="indefinite"/>')
    w(f'    <animate attributeName="y2" values="{scan_top + 20};{scan_bot + 20};{scan_top + 20}" dur="6s" repeatCount="indefinite"/>')
    w(f'  </line>')

    # === IDENTITY BLOCK ===
    id_y = gy + ROWS * CHAR_H + 40
    w(f'  <text x="{SVG_W / 2}" y="{id_y}" text-anchor="middle" class="nm" '
      f'opacity="0" begin="{FINAL_DELAY}s" dur="0.6s" fill="freeze">ADIB SUNASRA</text>')
    w(f'  <text x="{SVG_W / 2}" y="{id_y + 22}" text-anchor="middle" class="rl" '
      f'opacity="0" begin="{FINAL_DELAY + 0.3}s" dur="0.5s" fill="freeze">'
      'FULL-STACK DEVELOPER · AI/ML · SYSTEMS BUILDER</text>')

    # Bottom accent
    w(f'  <line x1="{gx}" y1="{id_y + 38}" x2="{gx + COLS * CHAR_W}" y2="{id_y + 38}" '
      f'stroke="#1f6feb" stroke-width="0.5" opacity="0.3"/>')
    w(f'  <circle cx="{SVG_W / 2}" cy="{id_y + 38}" r="2" fill="#1f6feb" opacity="0.5"/>')

    w('</svg>')
    return "\n".join(lines)


def main() -> bool:
    """Generate the progressive animated portrait SVG."""
    if not SOURCE_IMG.exists():
        print(f"ERROR: Source image not found: {SOURCE_IMG}", file=sys.stderr)
        return False

    print("Reading source image...")
    grid, thresholds = process_image(SOURCE_IMG)
    print(f"  Grid: {COLS}x{ROWS} characters")

    print("Generating progressive stages...")
    stages = generate_stages(grid, thresholds)
    for i, s in enumerate(stages):
        chars = sum(1 for line in s for c in line if c != " ")
        print(f"  Stage {i}: {chars} visible characters")

    print("Building SVG...")
    svg = build_svg(stages)

    OUTPUT_SVG.write_text(svg)
    size_kb = OUTPUT_SVG.stat().st_size / 1024
    print(f"Written: {OUTPUT_SVG} ({size_kb:.1f} KB)")
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
