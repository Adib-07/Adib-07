#!/usr/bin/env python3
"""Turn a source photo into an animated ASCII portrait SVG.

Architecture (two-phase):
  Phase 1: Photo → ONE excellent static ASCII portrait
  Phase 2: ONE ASCII portrait → self-contained animated SVG with SMIL reveal

The key insight: generate the final portrait FIRST, then animate
revealing that exact portrait. Do NOT generate different faces at
each animation stage.

Usage:
    python3 scripts/make_portrait.py

Requires:
    pip install pillow numpy opencv-python-headless rembg onnxruntime
"""

import hashlib
import math
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageOps, ImageEnhance
    from rembg import remove
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}", file=sys.stderr)
    print("Install with: pip install pillow numpy opencv-python-headless rembg onnxruntime", file=sys.stderr)
    sys.exit(1)

# ── Paths ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
SOURCE_IMG = ASSETS_DIR / "adib-source.png"
OUTPUT_SVG = ASSETS_DIR / "adib-generating.svg"
PREVIEW_TXT = ASSETS_DIR / "adib-ascii-preview.txt"
DEBUG_FACE = ASSETS_DIR / "adib-face-debug.png"

# ── Portrait grid ──────────────────────────────────────────────────────
# 90 cols gives good face detail without dominating the page.
# ROW_RATIO controls character aspect: monospace cells are ~2:1 height:width.
COLS = 90
ROW_RATIO = 0.48       # rows = COLS * (h/w) * ROW_RATIO

# ── Character ramp (bright/sparse → dark/dense) ───────────────────────
# Leading space = blank background. Dense chars for shadows/features.
# This ramp is proven to work well on dark-background portraits.
RAMP = " .`:-=+*cs#%@"
NUM_TIERS = len(RAMP)

# ── Image processing ──────────────────────────────────────────────────
CLAHE_CLIP = 3.0       # higher amplifies skin texture into noise
CURVE = 1.7            # darkening curve — the difference-maker
GAMMA = 1.0            # ramp mapping exponent
CROP_BOTTOM = 0.0      # fraction to trim off bottom (torso, chair)

# Face crop region for source photo (1214x1295)
# The face is in the upper-left area of the poster
# Coordinates: (left, top, right, bottom)
FACE_CROP = (30, 10, 320, 400)

# ── SVG rendering ─────────────────────────────────────────────────────
FONT_SIZE = 12.9
CHAR_W = 7.74          # 0.600 em at FONT_SIZE — character advance width
LINE_H = 15            # line height in SVG units
PAD = 14               # padding around portrait
FONT_FAMILY = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# ── Colors ────────────────────────────────────────────────────────────
BG_COLOR = "#0d1117"
FG_LIGHT = "#6e7681"   # portrait chars in light mode
FG_DARK = "#c9d1d9"    # portrait chars in dark mode (GitHub default)
HDR_COLOR = "#8b949e"
MSG_COLOR = "#58a6ff"
OK_COLOR = "#238636"
NAME_COLOR = "#e6edf3"
ACCENT = "#1f6feb"

# ── Animation timing ───────────────────────────────────────────────────
ROW_DELAY = 0.09       # per-row stagger, seconds
ANIM_TOTAL = 5.0       # total animation time

STATUS_EVENTS = [
    (0.0,  "> GENERATING PROFILE..."),
    (0.6,  "> READING SOURCE IMAGE..."),
    (1.2,  "> CONVERTING TO GRAYSCALE..."),
    (1.8,  "> EXTRACTING FACIAL STRUCTURE..."),
    (2.4,  "> MAPPING ASCII CHARACTERS..."),
    (3.2,  "> REFINING FEATURES..."),
    (4.0,  "> FINALIZING PORTRAIT..."),
    (ANIM_TOTAL, "> PROFILE READY"),
]


# ── Phase 1: Photo → ASCII Portrait ──────────────────────────────────

def prep_image(path: Path) -> Image.Image:
    """
    Crop to face, remove background, smooth skin, enhance local contrast, darken.

    This is the critical preprocessing step. Without cropping, the entire
    dark poster fills with dense characters. Without background removal,
    the remaining background fills with dense characters. Without the
    darkening curve, the face comes out washed out.
    """
    src = Image.open(path).convert("RGBA")

    # Crop to face region first — this is critical for poster-style images
    # where the face is only a small part of the full image
    src = src.crop(FACE_CROP)
    print(f"  Cropped to face: {FACE_CROP} → {src.size}")

    # Remove background using neural network
    # Composites subject onto white so background maps to spaces
    cut = remove(src)
    alpha = np.array(cut.split()[-1])

    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    gray = np.array(Image.alpha_composite(white, cut).convert("L"))

    # Bilateral filter: smooths skin while keeping edges (eyes, nose, mouth)
    gray = cv2.bilateralFilter(gray, 11, 50, 50)

    # CLAHE: local contrast enhancement — brings out facial features
    gray = cv2.createCLAHE(
        clipLimit=CLAHE_CLIP, tileGridSize=(8, 8)
    ).apply(gray)

    # Darkening curve: critical for face definition
    # Without this, brows, glasses and lips dissolve
    gray = (255.0 * (gray / 255.0) ** CURVE).astype("uint8")

    # Force removed background to pure white
    gray[alpha < 20] = 255

    return Image.fromarray(gray)


def to_ascii(img: Image.Image, cols: int = COLS) -> list[str]:
    """
    Convert preprocessed image to ASCII character rows.

    Handles:
    - Aspect ratio correction for monospace characters
    - Luminance → character mapping via the ramp
    - Trimming empty top/bottom rows
    """
    w, h = img.size

    if CROP_BOTTOM:
        img = img.crop((0, 0, w, int(h * (1 - CROP_BOTTOM))))
        w, h = img.size

    # Compute rows to preserve facial proportions
    # Monospace cells are ~2:1 height:width, so we need fewer rows
    rows = int(cols * (h / w) * ROW_RATIO)
    rows = max(rows, 30)
    rows = min(rows, 80)

    # Resize with LANCZOS for clean downscale
    img = img.resize((cols, rows), Image.LANCZOS)
    px = list(img.getdata())

    n = len(RAMP)
    out = []
    for r in range(rows):
        line = "".join(
            RAMP[min(n - 1, int((1 - px[r * cols + c] / 255.0) ** GAMMA * n))]
            for c in range(cols)
        ).rstrip()
        out.append(line)

    # Trim empty rows from top and bottom
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()

    return out


def save_debug_face(img: Image.Image):
    """Save the preprocessed face for debugging."""
    img.save(DEBUG_FACE)
    print(f"  Debug face: {DEBUG_FACE}")


# ── Phase 2: ASCII Portrait → Animated SVG ───────────────────────────

def build_animated_svg(ascii_lines: list[str], cols: int = COLS) -> str:
    """
    Build a self-contained animated SVG that progressively reveals
    the portrait row by row using SMIL clipPath wipes.

    Each row is revealed by a clipPath that expands from left to right,
    with a cursor block riding the wipe edge. Rows are staggered from
    top to bottom. The final state is frozen (fill="freeze").
    """
    print(f"\nPhase 2: Building animated SVG")
    print(f"  Rows: {len(ascii_lines)}, Cols: {cols}")

    num_rows = len(ascii_lines)
    svg_w = int(cols * CHAR_W + PAD * 2)
    svg_h = num_rows * LINE_H + PAD * 2

    # Header and footer area
    header_h = 60
    footer_h = 50
    total_h = header_h + svg_h + footer_h

    lines = []

    def w(s):
        lines.append(s)

    def esc(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    # ── SVG header ──
    w(f'<svg xmlns="http://www.w3.org/2000/svg" '
      f'width="{svg_w}" height="{total_h}" '
      f'viewBox="0 0 {svg_w} {total_h}" '
      f'font-family="{FONT_FAMILY}">')

    # ── Styles ──
    w('<style>')
    w(f'.a{{fill:{FG_LIGHT}}}')
    w(f'@media(prefers-color-scheme:dark){{.a{{fill:{FG_DARK}}}}}')
    w(f'.hdr{{fill:{HDR_COLOR};font-size:11px;letter-spacing:1px}}')
    w(f'.msg{{fill:{MSG_COLOR};font-size:11px;letter-spacing:1px}}')
    w(f'.ok{{fill:{OK_COLOR};font-size:11px;letter-spacing:1px}}')
    w(f'.name{{fill:{NAME_COLOR};font-size:18px;font-weight:700;letter-spacing:3px}}')
    w(f'.sub{{fill:{HDR_COLOR};font-size:10px;letter-spacing:2px}}')
    w('</style>')

    # ── Background ──
    w(f'<rect width="{svg_w}" height="{total_h}" fill="{BG_COLOR}"/>')

    # ── Terminal header ──
    y_header = 28
    w(f'<text x="{PAD}" y="{y_header}" class="hdr">'
      f'&gt; GENERATING PROFILE...</text>')

    # Status messages (fade in/out)
    for i, (t, msg) in enumerate(STATUS_EVENTS):
        if i < len(STATUS_EVENTS) - 1:
            next_t = STATUS_EVENTS[i + 1][0]
            dur = next_t - t + 0.3
        else:
            dur = 1.0

        y_msg = y_header + 20
        if i == len(STATUS_EVENTS) - 1:
            w(f'<text x="{PAD}" y="{y_msg}" class="ok" opacity="0" '
              f'begin="{t}s" dur="0.4s" fill="freeze">')
            w(f'  <animate attributeName="opacity" values="0;1" '
              f'dur="0.4s" begin="{t}s" fill="freeze"/>')
            w(f'  {esc(msg)}</text>')
        else:
            fade_in = 0.2
            fade_out_start = dur - 0.3
            w(f'<text x="{PAD}" y="{y_msg}" class="msg" opacity="0" '
              f'begin="{t}s" dur="{dur}s" fill="freeze">')
            w(f'  <animate attributeName="opacity"')
            w(f'    values="0;1;1;0"')
            w(f'    keyTimes="0;{fade_in/dur:.3f};{fade_out_start/dur:.3f};1"')
            w(f'    dur="{dur}s" begin="{t}s" fill="freeze"/>')
            w(f'  {esc(msg)}</text>')

    # ── Portrait origin ──
    gx = PAD
    gy = header_h

    # ── Portrait frame ──
    fx = gx - 6
    fy = gy - 6
    fw = cols * CHAR_W + 12
    fh = num_rows * LINE_H + 12
    w(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" '
      f'rx="3" fill="{BG_COLOR}" stroke="#30363d" stroke-width="0.5"/>')

    # Corner decorations
    corner_len = 6
    for cx, cy, dx, dy in [
        (fx, fy, corner_len, corner_len),
        (fx + fw, fy, -corner_len, corner_len),
        (fx, fy + fh, corner_len, -corner_len),
        (fx + fw, fy + fh, -corner_len, -corner_len),
    ]:
        w(f'<path d="M{cx} {cy + dy} L{cx} {cy} L{cx + dx} {cy}" '
          f'fill="none" stroke="{ACCENT}" stroke-width="0.6" opacity="0.5"/>')

    # ── Per-row SMIL reveal ──
    # Each row is revealed by a clipPath wipe from left to right.
    # A cursor block rides the wipe edge, then disappears.
    # All animations freeze at the end so the portrait stays visible.

    for i, row_text in enumerate(ascii_lines):
        y = gy + i * LINE_H
        begin = f"{i * ROW_DELAY:.2f}s"
        end = f"{(i + 1) * ROW_DELAY:.2f}s"
        row_w = max(len(row_text), 1) * CHAR_W
        safe = esc(row_text)

        # ClipPath: rectangle expanding from 0 to full row width
        w(f'<clipPath id="c{i}"><rect x="{gx}" y="{y}" '
          f'height="{LINE_H}" width="0">'
          f'<animate attributeName="width" from="0" to="{row_w:.1f}" '
          f'begin="{begin}" dur="{ROW_DELAY}s" fill="freeze"/>'
          f'</rect></clipPath>')

        # Row text, clipped by the wipe
        w(f'<g clip-path="url(#c{i})"><text xml:space="preserve" '
          f'x="{gx}" y="{y + 11.2:.1f}" class="a" '
          f'font-size="{FONT_SIZE}">{safe}</text></g>')

        # Cursor block riding the wipe edge
        w(f'<rect y="{y + 1}" width="6" height="12" class="a" '
          f'opacity="0">'
          f'<animate attributeName="x" from="{gx}" to="{gx + row_w:.1f}" '
          f'begin="{begin}" dur="{ROW_DELAY}s" fill="freeze"/>'
          f'<set attributeName="opacity" to="0.8" begin="{begin}"/>'
          f'<set attributeName="opacity" to="0" begin="{end}"/></rect>')

    # ── Scan line effect (subtle) ──
    w(f'<line x1="{fx}" y1="{fy}" x2="{fx + fw}" y2="{fy}" '
      f'stroke="{ACCENT}" stroke-width="0.4" opacity="0.15">')
    w(f'  <animate attributeName="y1" values="{fy};{fy + fh};{fy}" '
      f'dur="5s" repeatCount="indefinite"/>')
    w(f'  <animate attributeName="y2" values="{fy + 15};{fy + fh + 15};'
      f'{fy + 15}" dur="5s" repeatCount="indefinite"/>')
    w('</line>')

    # ── Identity text below portrait ──
    iy = gy + num_rows * LINE_H + 30
    w(f'<text x="{svg_w / 2}" y="{iy}" text-anchor="middle" class="name" '
      f'opacity="0" begin="{ANIM_TOTAL}s" dur="0.5s" fill="freeze">')
    w(f'  <animate attributeName="opacity" values="0;1" dur="0.5s" '
      f'begin="{ANIM_TOTAL}s" fill="freeze"/>')
    w(f'  ADIB SUNASRA')
    w(f'</text>')

    w(f'<text x="{svg_w / 2}" y="{iy + 18}" text-anchor="middle" class="sub" '
      f'opacity="0" begin="{ANIM_TOTAL + 0.2}s" dur="0.5s" fill="freeze">')
    w(f'  <animate attributeName="opacity" values="0;1" dur="0.5s" '
      f'begin="{ANIM_TOTAL + 0.2}s" fill="freeze"/>')
    w(f'  FULL-STACK DEVELOPER · AI/ML · SYSTEMS BUILDER')
    w(f'</text>')

    w('</svg>')
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  PROFILE PORTRAIT GENERATOR")
    print("=" * 60)
    print()

    if not SOURCE_IMG.exists():
        print(f"ERROR: Source image not found: {SOURCE_IMG}", file=sys.stderr)
        sys.exit(1)

    # ── Phase 1: Generate static ASCII portrait ──
    print("Phase 1: Generating static ASCII portrait")
    print(f"  Source: {SOURCE_IMG}")

    # Preprocess: remove background, enhance contrast, darken
    print("  Removing background...")
    processed = prep_image(SOURCE_IMG)
    print(f"  Preprocessed size: {processed.size}")

    save_debug_face(processed)

    # Convert to ASCII
    print("  Converting to ASCII...")
    ascii_lines = to_ascii(processed)

    # Stats
    total_chars = COLS * len(ascii_lines)
    non_space = sum(1 for line in ascii_lines for c in line if c != " ")
    print(f"  Grid: {COLS} × {len(ascii_lines)} = {total_chars} characters")
    print(f"  Non-space: {non_space} ({100*non_space/total_chars:.1f}%)")

    # Save preview
    with open(PREVIEW_TXT, "w") as f:
        for row in ascii_lines:
            f.write(row + "\n")
    print(f"  Preview: {PREVIEW_TXT}")

    # Print to terminal
    print("\n--- ASCII PORTRAIT PREVIEW ---\n")
    for row in ascii_lines:
        print(row)
    print("\n--- END PREVIEW ---\n")

    # ── Phase 2: Build animated SVG ──
    svg_content = build_animated_svg(ascii_lines)
    OUTPUT_SVG.write_text(svg_content)
    size_kb = OUTPUT_SVG.stat().st_size / 1024
    print(f"  Written: {OUTPUT_SVG} ({size_kb:.1f} KB)")

    print()
    print("=" * 60)
    print("  DONE")
    print("=" * 60)
    print(f"  ASCII preview: {PREVIEW_TXT}")
    print(f"  Animated SVG:  {OUTPUT_SVG}")
    print(f"  Debug face:    {DEBUG_FACE}")
    print()


if __name__ == "__main__":
    main()
