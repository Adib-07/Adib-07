#!/usr/bin/env python3
"""
Progressive ASCII Portrait Generator for GitHub Profile.

Converts a source photo into a self-contained animated SVG that
progressively reveals an ASCII/terminal portrait through 8 stages.

Usage:
    python3 scripts/generate-profile-portrait.py

Requires: Pillow (pip install Pillow)
"""

import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageFilter, ImageOps
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# Paths
REPO_ROOT = Path(__file__).parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
SOURCE_IMG = ASSETS_DIR / "adib-source.png"
OUTPUT_SVG = ASSETS_DIR / "adib-generating.svg"

# Portrait grid dimensions
COLS = 80
FONT_SIZE = 10

# Character aspect ratio correction
CHAR_ASPECT = 0.6
ROWS = 64

# SVG dimensions
CHAR_W = FONT_SIZE * 0.6
CHAR_H = FONT_SIZE
SVG_W = 760
MARGIN_TOP = 110
MARGIN_BOTTOM = 100
SVG_H = MARGIN_TOP + ROWS * CHAR_H + MARGIN_BOTTOM

# ASCII palette: lightest to darkest (11 chars for better gradation)
CHARS = " .,:;+*?%S#@"
NUM_TIERS = len(CHARS)

# Progressive reveal thresholds (tuned for resized grid: min ~0.18, mean ~0.40)
STAGE_LUM_THRESHOLDS = [0.20, 0.26, 0.32, 0.40, 0.50, 0.62, 0.78, 1.01]

# Animation timing
STAGE_TIMING = [
    (0.0, 2.0), (0.5, 1.8), (1.0, 1.6), (1.6, 1.4),
    (2.2, 1.2), (2.8, 1.0), (3.4, 0.8),
]
FINAL_DELAY = 3.8

STATUS_MSGS = [
    (0.0,  "> GENERATING PROFILE"),
    (0.5,  "> LOADING SOURCE IMAGE..."),
    (1.0,  "> CONVERTING TO GRAYSCALE..."),
    (1.5,  "> EXTRACTING FACIAL STRUCTURE..."),
    (2.0,  "> MAPPING ASCII CHARACTERS..."),
    (2.6,  "> REFINING FEATURES..."),
    (3.2,  "> FINALIZING PORTRAIT..."),
    (3.8,  "> PROFILE READY"),
]

HUD_LINES = [
    (0.0,  "IDENTITY",  "INITIALIZING"),
    (0.8,  "STRUCTURE", "PROCESSING"),
    (1.6,  "FACIAL",    "PROCESSING"),
    (2.4,  "RENDER",    "PROCESSING"),
    (3.8,  "IDENTITY",  "OK"),
    (3.8,  "STRUCTURE", "OK"),
    (3.8,  "FACIAL",    "OK"),
    (3.8,  "RENDER",    "OK"),
]

PROGRESS_STEPS = [
    (0.0,  1, "10%"), (1.0,  3, "30%"), (1.8,  5, "50%"),
    (2.6,  7, "70%"), (3.2,  9, "90%"), (3.8, 10, "100%"),
]


def process_image(src: Path) -> tuple[list[list[float]], list[float], int]:
    """Process source image: alpha handling, face crop, contrast enhancement."""
    img = Image.open(src)

    # Composite against white to handle alpha
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    else:
        img = img.convert("RGB")

    orig_w, orig_h = img.size

    # Detect face region (non-white pixels)
    gray_full = img.convert("L")
    px = list(gray_full.getdata())
    white_t = 235
    min_x, max_x = orig_w, 0
    min_y, max_y = orig_h, 0
    for y in range(orig_h):
        for x in range(orig_w):
            if px[y * orig_w + x] < white_t:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    if max_x <= min_x or max_y <= min_y:
        min_x, min_y = 0, 0
        max_x, max_y = orig_w, orig_h

    # Margin
    mx = int((max_x - min_x) * 0.06)
    my = int((max_y - min_y) * 0.04)
    c = (max(0, min_x - mx), max(0, min_y - my),
         min(orig_w, max_x + mx), min(orig_h, max_y + my))

    # Crop face
    face = img.crop(c)
    fw, fh = face.size
    gray = face.convert("L")

    # Edge detection for feature enhancement
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_px = [e / 255.0 for e in list(edges.getdata())]

    # Gamma correction on luminance
    gamma = 0.55
    lum_px = list(gray.getdata())
    lum_enhanced = [math.pow(p / 255.0, gamma) for p in lum_px]

    # Combine: 85% enhanced luminance + 15% edge detail
    combined = [0.85 * l + 0.15 * e for l, e in zip(lum_enhanced, edge_px)]

    # Resize with aspect correction
    img_aspect = fh / fw
    target_aspect = img_aspect * CHAR_ASPECT
    grid_h = int(COLS * target_aspect)
    grid_h = max(grid_h, 30)
    grid_h = min(grid_h, ROWS)

    # Create image from combined values
    combined_img = Image.new("L", (fw, fh))
    combined_img.putdata([int(v * 255) for v in combined])
    resized = combined_img.resize((COLS, grid_h), Image.Resampling.LANCZOS)
    rp = list(resized.getdata())

    # Build grid
    grid = []
    all_lums = []
    for r in range(grid_h):
        row = []
        for c in range(COLS):
            lum = rp[r * COLS + c] / 255.0
            row.append(lum)
            all_lums.append(lum)
        grid.append(row)

    while len(grid) < ROWS:
        grid.append([1.0] * COLS)

    # Percentile-based thresholds (include min value for darkest tier)
    sl = sorted(all_lums)
    thresholds = [sl[0]]  # Start at minimum value
    for i in range(1, NUM_TIERS - 1):
        idx = int(i * len(sl) / (NUM_TIERS - 1))
        thresholds.append(sl[min(idx, len(sl) - 1)])
    thresholds.append(1.01)

    return grid[:ROWS], thresholds, grid_h


def lum_to_char(lum: float, thresholds: list[float]) -> str:
    for i, t in enumerate(thresholds):
        if lum < t:
            return CHARS[i]
    return CHARS[-1]


def generate_stages(grid: list[list[float]], thresholds: list[float],
                    actual_rows: int) -> list[list[str]]:
    stages = []
    for threshold in STAGE_LUM_THRESHOLDS:
        stage_lines = []
        for r in range(ROWS):
            line = []
            for c in range(COLS):
                if r >= actual_rows:
                    line.append(" ")
                elif grid[r][c] < threshold:
                    line.append(lum_to_char(grid[r][c], thresholds))
                else:
                    line.append(" ")
            stage_lines.append("".join(line))
        stages.append(stage_lines)
    return stages


def build_svg(stages: list[list[str]]) -> str:
    lines = []

    def w(s):
        lines.append(s)

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    gx = round((SVG_W - COLS * CHAR_W) / 2, 1)
    gy = MARGIN_TOP
    text_x = round(gx + CHAR_W / 2, 1)

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

    w(f'  <rect width="{SVG_W}" height="{SVG_H}" fill="#0d1117"/>')

    # HUD
    w(f'  <text x="20" y="35" class="h">&gt; GENERATING PROFILE</text>')

    mi, mf, mh = 0.5, 0.3, 0.7
    for i, (_, msg) in enumerate(STATUS_MSGS):
        ts = round(i * mi, 2)
        tfs = round(ts + mf + mh, 2)
        te = round(tfs + mf, 2)
        td = round(te - ts, 2)
        kfi = round(mf / td, 3)
        kfo = round(min(tfs / td, 0.99), 3)
        if i == len(STATUS_MSGS) - 1:
            w(f'  <text x="20" y="55" class="s" opacity="0" begin="{ts}s" dur="{td}s" fill="freeze">')
            w(f'    <animate attributeName="opacity" values="0;1;1" keyTimes="0;{kfi};1" dur="{td}s" begin="{ts}s" fill="freeze"/>')
            w(f'{esc(msg)}</text>')
        else:
            w(f'  <text x="20" y="55" class="s" opacity="0" begin="{ts}s" dur="{td}s" fill="freeze">')
            w(f'    <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;{kfi};{kfo};1" dur="{td}s" begin="{ts}s" fill="freeze"/>')
            w(f'{esc(msg)}</text>')

    # Progress bar
    bx, by, bw, bh = 20, 72, 250, 12
    w(f'  <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="2" fill="#161b22" stroke="#30363d" stroke-width="0.5"/>')
    sw = (bw - 4) / 10
    for seg in range(10):
        sx = round(bx + 2 + seg * sw, 1)
        ss = round(sw - 1, 1)
        at = 0.0
        for pt, fl, _ in PROGRESS_STEPS:
            if seg < fl:
                at = pt
                break
        else:
            at = PROGRESS_STEPS[-1][0]
        w(f'  <rect x="{sx}" y="{by + 2}" width="{ss}" height="{bh - 4}" rx="1" class="bar" opacity="0" begin="{at}s" dur="0.4s" fill="freeze"/>')
    for pt, _, pct in PROGRESS_STEPS:
        w(f'  <text x="{bx + bw + 10}" y="{by + 10}" class="dim" opacity="0" begin="{pt}s" dur="0.3s" fill="freeze">{pct}</text>')

    # HUD lines
    hx = SVG_W - 180
    for i, (bt, label, value) in enumerate(HUD_LINES):
        hy = 35 + i * 16
        cls = "ok" if value == "OK" else "proc"
        w(f'  <text x="{hx}" y="{hy}" class="proc" opacity="0" begin="{bt}s" dur="0.3s" fill="freeze">{esc(label)} ............. </text>')
        w(f'  <text x="{hx + 120}" y="{hy}" class="{cls}" opacity="0" begin="{bt}s" dur="0.3s" fill="freeze">{esc(value)}</text>')

    # Frame
    fx = gx - 12
    fy = gy - 12
    fw = COLS * CHAR_W + 24
    fh = ROWS * CHAR_H + 24
    w(f'  <rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="4" fill="#0d1117" stroke="#30363d" stroke-width="0.5"/>')
    for cx, cy, dx, dy in [(fx, fy, 8, 8), (fx + fw, fy, -8, 8), (fx, fy + fh, 8, -8), (fx + fw, fy + fh, -8, -8)]:
        w(f'  <path d="M{cx} {cy + dy} L{cx} {cy} L{cx + dx} {cy}" fill="none" stroke="#1f6feb" stroke-width="0.8" opacity="0.4"/>')

    # Animated stages
    for si in range(len(stages) - 1):
        delay, dur = STAGE_TIMING[si]
        w(f'  <g opacity="0" begin="{delay}s" dur="{dur}s" fill="freeze">')
        w(f'    <text x="{text_x}" y="{gy}" font-size="{FONT_SIZE}" fill="#e6edf3" xml:space="preserve"><tspan x="{text_x}" dy="0">')
        for ri, row_text in enumerate(stages[si]):
            e = esc(row_text)
            w(f'{e}</tspan>' if ri == 0 else f'<tspan x="{text_x}" dy="{CHAR_H}">{e}</tspan>')
        w('    </text>')
        w('  </g>')

    # Final stage
    w(f'  <g>')
    w(f'    <text x="{text_x}" y="{gy}" font-size="{FONT_SIZE}" fill="#e6edf3" xml:space="preserve"><tspan x="{text_x}" dy="0">')
    for ri, row_text in enumerate(stages[-1]):
        e = esc(row_text)
        w(f'{e}</tspan>' if ri == 0 else f'<tspan x="{text_x}" dy="{CHAR_H}">{e}</tspan>')
    w('    </text>')
    w('  </g>')

    # Scan line
    w(f'  <line x1="{fx}" y1="{fy}" x2="{fx + fw}" y2="{fy}" stroke="#1f6feb" stroke-width="0.5" opacity="0.2">')
    w(f'    <animate attributeName="y1" values="{fy};{fy + fh};{fy}" dur="6s" repeatCount="indefinite"/>')
    w(f'    <animate attributeName="y2" values="{fy + 20};{fy + fh + 20};{fy + 20}" dur="6s" repeatCount="indefinite"/>')
    w(f'  </line>')

    # Identity
    iy = gy + ROWS * CHAR_H + 40
    w(f'  <text x="{SVG_W / 2}" y="{iy}" text-anchor="middle" class="nm" opacity="0" begin="{FINAL_DELAY}s" dur="0.6s" fill="freeze">ADIB SUNASRA</text>')
    w(f'  <text x="{SVG_W / 2}" y="{iy + 22}" text-anchor="middle" class="rl" opacity="0" begin="{FINAL_DELAY + 0.3}s" dur="0.5s" fill="freeze">FULL-STACK DEVELOPER · AI/ML · SYSTEMS BUILDER</text>')
    w(f'  <line x1="{gx}" y1="{iy + 38}" x2="{gx + COLS * CHAR_W}" y2="{iy + 38}" stroke="#1f6feb" stroke-width="0.5" opacity="0.3"/>')
    w(f'  <circle cx="{SVG_W / 2}" cy="{iy + 38}" r="2" fill="#1f6feb" opacity="0.5"/>')

    w('</svg>')
    return "\n".join(lines)


def print_preview(stages):
    print("\n=== FINAL ASCII PORTRAIT PREVIEW ===\n")
    for line in stages[-1]:
        print(line)
    print()


def main():
    if not SOURCE_IMG.exists():
        print(f"ERROR: Source image not found: {SOURCE_IMG}", file=sys.stderr)
        return False

    print("Reading source image...")
    grid, thresholds, actual_rows = process_image(SOURCE_IMG)
    print(f"  Grid: {COLS}x{ROWS} characters")

    print("Generating progressive stages...")
    stages = generate_stages(grid, thresholds, actual_rows)
    for i, s in enumerate(stages):
        chars = sum(1 for line in s for c in line if c != " ")
        print(f"  Stage {i}: {chars} visible characters")

    print("Building SVG...")
    svg = build_svg(stages)
    OUTPUT_SVG.write_text(svg)
    size_kb = OUTPUT_SVG.stat().st_size / 1024
    print(f"Written: {OUTPUT_SVG} ({size_kb:.1f} KB)")

    print_preview(stages)
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
