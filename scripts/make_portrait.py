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

import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image
    from rembg import remove, new_session
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

# ── Face crop — VERIFIED against source (1214×1295) ───────────────────
# Photo of the face lives in the upper-left of the poster.
# Measured bounds:
#   left text "BUILD LEARN IMPROVE"  ends at x=80
#   right text "SYSTEMS AI ..."       starts at x=296
#   hair top ≈ y=40, chin ≈ y=192, shoulders ≈ y=245
#   subject (incl. shoulders) spans x=126..266, face center x≈196
# This crop centers the subject, clears both text labels, and keeps
# full head + hair + face + neck + a small amount of shoulders.
FACE_CROP = (110, 28, 282, 252)   # (left, top, right, bottom) → 172×224

# ── Portrait grid ──────────────────────────────────────────────────────
# Moderate grid: recognizable detail without dominating the README.
COLS = 78
# Character cells are ~2:1 height:width, so geometric correction uses
# ROW_RATIO ≈ 0.5. We use 0.58 so the face reads with natural height.
ROW_RATIO = 0.58
MIN_ROWS = 50
MAX_ROWS = 80

# ── Character ramp (dark/sparse → bright/dense) ───────────────────────
# EMISSIVE mapping for the dark SVG background: brighter source pixels
# get denser characters, so the face glows out of the dark terminal.
# Leading space = removed background. Subject pixels never reach space
# (silhouette floor) so the hair outline stays visible.
RAMP = " .`:-=+*cs#%@"
SILHOUETTE_FLOOR = 2       # subject min index — preserves hair/shoulder outline
ALPHA_SUBJECT = 60         # above soft rembg edge bleed; isnet gives hair
                           # solid alpha, so 60 keeps the full silhouette
EMIT_GAMMA = 1.35          # >1 darkens mid/dark tones before mapping so
                           # eyes/brows read as clear holes on the dark bg

# ── Image processing ──────────────────────────────────────────────────
BLUR_SIGMA = 1.5           # kills the source photo's halftone dot texture
                           # without washing out eyes/brows/mouth
BILATERAL_D = 9
CLAHE_CLIP = 2.6           # lifts feature contrast (brows, eyes, lips)
UNSHARP = 1.9              # re-crisps eyes/nose/mouth after smoothing
PCT_LO, PCT_HI = 3, 97     # percentile stretch on subject only

# ── SVG rendering ─────────────────────────────────────────────────────
FONT_SIZE = 12
CHAR_W = 7.2               # 0.60 em — monospace advance width
LINE_H = 15
PAD = 18                   # outer padding
FRAME_PAD = 8              # portrait frame inset around the grid
FONT_FAMILY = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

# ── Colors ────────────────────────────────────────────────────────────
BG_COLOR = "#0d1117"
FG_LIGHT = "#6e7681"       # portrait chars in light mode
FG_DARK = "#c9d1d9"        # portrait chars in dark mode (GitHub default)
HDR_COLOR = "#8b949e"
MSG_COLOR = "#58a6ff"
OK_COLOR = "#3fb950"
NAME_COLOR = "#e6edf3"
ACCENT = "#1f6feb"

# ── Animation timing ───────────────────────────────────────────────────
ANIM_TOTAL = 4.2           # reveal duration, seconds (within 3–5s target)
STATUS_EVENTS = [
    (0.0,  "> GENERATING PROFILE..."),
    (0.5,  "> READING SOURCE IMAGE..."),
    (1.0,  "> DETECTING FACE REGION..."),
    (1.5,  "> EXTRACTING FACIAL STRUCTURE..."),
    (2.1,  "> MAPPING ASCII CHARACTERS..."),
    (2.8,  "> REFINING FEATURES..."),
    (3.5,  "> FINALIZING PORTRAIT..."),
    (ANIM_TOTAL, "> PROFILE READY"),
]


# ── Phase 1: Photo → ASCII Portrait ──────────────────────────────────

def prep_image(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Crop to the verified face region, remove background, smooth the
    halftone texture, normalize skin tones, and re-crisp features.

    Returns (grayscale over white, alpha mask).
    """
    src = Image.open(path).convert("RGBA")
    src = src.crop(FACE_CROP)
    print(f"  Cropped to face: {FACE_CROP} → {src.size}")

    session = new_session("isnet-general-use")  # u2net drops dark hair on dark bg
    cut = remove(src, session=session)
    alpha = np.array(cut.split()[-1])
    frac_bg = (alpha < 50).mean()
    print(f"  Background removed: {100*frac_bg:.1f}% transparent")
    if frac_bg < 0.15:
        raise RuntimeError(
            "Background removal failed (too little transparent area). "
            "The u2net model may be corrupt; delete ~/.rembg/models and retry."
        )

    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    gray = np.array(Image.alpha_composite(white, cut).convert("L"))

    # Kill halftone dot texture while keeping major edges
    g = cv2.GaussianBlur(gray, (0, 0), BLUR_SIGMA)
    g = cv2.bilateralFilter(g, BILATERAL_D, 40, 40)

    # Normalize subject tonal range so skin sits bright, features stay dark
    m = alpha > 150
    if m.sum() < 100:
        raise RuntimeError("Face mask is empty after background removal.")
    lo, hi = np.percentile(g[m], [PCT_LO, PCT_HI])
    g = np.clip((g.astype(float) - lo) / max(hi - lo, 1e-6) * 215 + 35, 0, 255)
    # Mild S-curve: push shadows (brows/eyes/lips) down, highlights up
    gn = g / 255.0
    g = (255.0 * (gn * gn * (3 - 2 * gn))).astype(np.uint8)  # smoothstep
    g = g.astype(np.uint8)

    # Local contrast for eyes/brows/nose/mouth
    g = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(4, 4)).apply(g)

    # Unsharp mask — restore feature edges softened by the blur
    blur = cv2.GaussianBlur(g, (0, 0), 1.6)
    g = cv2.addWeighted(g, UNSHARP, blur, -(UNSHARP - 1), 0)

    # Force background to pure white through the alpha mask
    gf = g.astype(float) * (alpha / 255.0) + 255.0 * (1 - alpha / 255.0)
    g = np.clip(gf, 0, 255).astype(np.uint8)
    return g, alpha


def to_ascii(gray: np.ndarray, alpha: np.ndarray) -> list[str]:
    """
    Convert the preprocessed face to ONE ASCII portrait.

    Emissive mapping (bright → dense) because the SVG background is dark:
    luminance of a rendered cell on #0d1117 tracks character density, so
    brighter source pixels must produce denser characters.
    """
    h, w = gray.shape
    rows = int(COLS * (h / w) * ROW_RATIO)
    rows = max(MIN_ROWS, min(rows, MAX_ROWS))

    g_s = np.array(Image.fromarray(gray).resize((COLS, rows), Image.LANCZOS))
    a_s = np.array(Image.fromarray(alpha).resize((COLS, rows), Image.LANCZOS))

    # Soft-fringe guard: partial alpha over white composites near-white and
    # would map to '@' in emissive mode. Pull fringe luminance down toward
    # the silhouette floor so edges read as outline, not glow.
    conf = (a_s.astype(np.float32) / 255.0)
    conf = np.clip((conf - ALPHA_SUBJECT / 255.0) / max(1 - ALPHA_SUBJECT / 255.0, 1e-6), 0, 1)
    g_f = g_s.astype(np.float32)
    g_f = g_f * conf + (SILHOUETTE_FLOOR / (len(RAMP) - 1)) * 255.0 * (1 - conf)
    g_f = np.where(a_s >= ALPHA_SUBJECT, g_f, 0)
    g_s = np.clip(g_f, 0, 255).astype(np.uint8)

    n = len(RAMP)
    floor = SILHOUETTE_FLOOR
    lines: list[str] = []
    for r in range(rows):
        chars = []
        for c in range(COLS):
            if a_s[r, c] < ALPHA_SUBJECT:
                chars.append(" ")
                continue
            v = float(g_s[r, c]) / 255.0
            v = v ** EMIT_GAMMA
            idx = int(v * (n - 1 - floor) + floor + 0.0001)
            chars.append(RAMP[max(floor, min(n - 1, idx))])
        line = "".join(chars).rstrip()
        lines.append(line)

    # Trim fully empty top/bottom rows (keep silhouette intact otherwise)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def save_debug_face(img: Image.Image):
    img.save(DEBUG_FACE)
    print(f"  Debug face: {DEBUG_FACE}")


# ── Phase 2: ASCII Portrait → Animated SVG ───────────────────────────

def build_animated_svg(ascii_lines: list[str]) -> str:
    """
    Build a self-contained animated SVG that progressively reveals
    the exact Phase-1 portrait row by row using SMIL clip wipes.

    Geometry is deterministic:
      - every row is forced to width len(line)*CHAR_W via textLength
      - viewBox equals width/height exactly
      - padding covers ascenders/descenders on all sides
      - nothing relies on browser overflow
    Final state freezes: the complete portrait stays visible.
    """
    print(f"\nPhase 2: Building animated SVG")
    num_rows = len(ascii_lines)
    grid_w = COLS * CHAR_W
    grid_h = num_rows * LINE_H

    fx = PAD + FRAME_PAD
    fy_header = 62
    fy = fy_header + FRAME_PAD
    fw = grid_w + FRAME_PAD * 2
    fh = grid_h + FRAME_PAD * 2

    footer_h = 56
    svg_w = int(round(PAD + fw + PAD))
    svg_h = int(round(fy + fh + footer_h))

    print(f"  Grid: {COLS} × {num_rows}")
    print(f"  SVG:  {svg_w} × {svg_h}, viewBox 0 0 {svg_w} {svg_h}")

    row_delay = ANIM_TOTAL / max(num_rows, 1)
    baseline_off = FONT_SIZE * 0.80   # baseline offset within a LINE_H cell

    lines: list[str] = []

    def w(s: str):
        lines.append(s)

    def esc(s: str) -> str:
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    # ── SVG header — width/height match viewBox exactly ──
    w(f'<svg xmlns="http://www.w3.org/2000/svg" '
      f'width="{svg_w}" height="{svg_h}" '
      f'viewBox="0 0 {svg_w} {svg_h}" '
      f'font-family="{FONT_FAMILY}">')

    w('<style>')
    w(f'.a{{fill:{FG_LIGHT}}}')
    w(f'@media(prefers-color-scheme:dark){{.a{{fill:{FG_DARK}}}}}')
    w(f'.hdr{{fill:{HDR_COLOR};font-size:11px;letter-spacing:1px}}')
    w(f'.msg{{fill:{MSG_COLOR};font-size:11px;letter-spacing:1px}}')
    w(f'.ok{{fill:{OK_COLOR};font-size:11px;letter-spacing:1px;font-weight:700}}')
    w(f'.name{{fill:{NAME_COLOR};font-size:18px;font-weight:700;letter-spacing:3px}}')
    w(f'.sub{{fill:{HDR_COLOR};font-size:10px;letter-spacing:2px}}')
    w('</style>')

    # ── Background covers the full viewBox ──
    w(f'<rect x="0" y="0" width="{svg_w}" height="{svg_h}" fill="{BG_COLOR}"/>')

    # ── Terminal header ──
    w(f'<text x="{PAD}" y="34" class="hdr">&gt; GENERATING PROFILE...</text>')

    # ── Status line (sequential fade at a fixed y) ──
    y_msg = 52
    for i, (t, msg) in enumerate(STATUS_EVENTS):
        if i < len(STATUS_EVENTS) - 1:
            next_t = STATUS_EVENTS[i + 1][0]
            dur = next_t - t + 0.25
        else:
            dur = 1.5
        if i == len(STATUS_EVENTS) - 1:
            # Final message: fade in and STAY
            w(f'<text x="{PAD}" y="{y_msg}" class="ok" opacity="0" '
              f'fill="freeze">')
            w(f'<animate attributeName="opacity" values="0;1" '
              f'dur="0.35s" begin="{t}s" fill="freeze"/>')
            w(f'{esc(msg)}</text>')
        else:
            fin = 0.15
            fout = dur - 0.25
            w(f'<text x="{PAD}" y="{y_msg}" class="msg" opacity="0" '
              f'fill="freeze">')
            w(f'<animate attributeName="opacity" '
              f'values="0;1;1;0" '
              f'keyTimes="0;{fin/dur:.4f};{fout/dur:.4f};1" '
              f'dur="{dur:.3f}s" begin="{t}s" fill="freeze"/>')
            w(f'{esc(msg)}</text>')

    # ── Portrait frame ──
    w(f'<rect x="{fx:.1f}" y="{fy:.1f}" width="{fw:.1f}" height="{fh:.1f}" '
      f'rx="3" fill="{BG_COLOR}" stroke="#30363d" stroke-width="0.5"/>')

    # Corner decorations
    corner = 7
    for cx, cy, dx, dy in [
        (fx, fy, corner, corner),
        (fx + fw, fy, -corner, corner),
        (fx, fy + fh, corner, -corner),
        (fx + fw, fy + fh, -corner, -corner),
    ]:
        w(f'<path d="M{cx:.1f} {cy + dy:.1f} L{cx:.1f} {cy:.1f} '
          f'L{cx + dx:.1f} {cy:.1f}" fill="none" stroke="{ACCENT}" '
          f'stroke-width="0.7" opacity="0.55"/>')

    # ── Per-row SMIL reveal (the EXACT Phase-1 portrait) ──
    gx = fx + FRAME_PAD
    gy = fy + FRAME_PAD

    for i, row_text in enumerate(ascii_lines):
        y = gy + i * LINE_H
        baseline = y + baseline_off
        begin = i * row_delay
        # Clamp last row so everything is fully visible by ANIM_TOTAL
        dur = row_delay
        row_w = len(row_text) * CHAR_W
        safe = esc(row_text)
        # Full grid width for the wipe target — keeps timing even across rows
        # even when trailing spaces were stripped.
        wipe_w = COLS * CHAR_W

        w(f'<clipPath id="c{i}"><rect x="{gx:.1f}" y="{y:.1f}" '
          f'width="0" height="{LINE_H}">'
          f'<animate attributeName="width" from="0" to="{wipe_w:.1f}" '
          f'begin="{begin:.4f}s" dur="{dur:.4f}s" fill="freeze"/>'
          f'</rect></clipPath>')

        # textLength locks the advance width so no browser font-metric
        # difference can squeeze, stretch, or clip the row.
        w(f'<g clip-path="url(#c{i})"><text xml:space="preserve" '
          f'x="{gx:.1f}" y="{baseline:.1f}" class="a" '
          f'font-size="{FONT_SIZE}" '
          f'textLength="{row_w:.1f}" lengthAdjust="spacingAndGlyphs">'
          f'{safe}</text></g>')

        # Cursor block riding the wipe edge, then gone
        w(f'<rect x="{gx:.1f}" y="{y + 1.5:.1f}" width="5" height="12" '
          f'fill="{FG_DARK}" opacity="0">')
        w(f'<animate attributeName="x" from="{gx:.1f}" '
          f'to="{gx + wipe_w:.1f}" begin="{begin:.4f}s" '
          f'dur="{dur:.4f}s" fill="freeze"/>')
        w(f'<animate attributeName="opacity" values="0;0.85;0.85;0" '
          f'keyTimes="0;0.05;0.85;1" begin="{begin:.4f}s" '
          f'dur="{dur:.4f}s" fill="freeze"/>')
        w('</rect>')

    # ── One-shot scan sweep (runs once with the reveal, then freezes) ──
    w(f'<line x1="{fx:.1f}" y1="{gy:.1f}" x2="{fx + fw:.1f}" y2="{gy:.1f}" '
      f'stroke="{ACCENT}" stroke-width="0.5" opacity="0">')
    w(f'<animate attributeName="opacity" values="0;0.35;0" '
      f'dur="{ANIM_TOTAL:.2f}s" begin="0s" fill="freeze"/>')
    w(f'<animate attributeName="y1" values="{gy:.1f};{gy + grid_h:.1f}" '
      f'dur="{ANIM_TOTAL:.2f}s" begin="0s" fill="freeze"/>')
    w(f'<animate attributeName="y2" values="{gy + 12:.1f};'
      f'{gy + grid_h + 12:.1f}" dur="{ANIM_TOTAL:.2f}s" begin="0s" '
      f'fill="freeze"/>')
    w('</line>')

    # ── Identity text below portrait (appears at end, persists) ──
    iy = gy + grid_h + FRAME_PAD + 28
    w(f'<text x="{svg_w // 2}" y="{iy}" text-anchor="middle" class="name" '
      f'opacity="0" fill="freeze">')
    w(f'<animate attributeName="opacity" values="0;1" dur="0.4s" '
      f'begin="{ANIM_TOTAL:.2f}s" fill="freeze"/>')
    w('ADIB SUNASRA</text>')

    w(f'<text x="{svg_w // 2}" y="{iy + 17}" text-anchor="middle" '
      f'class="sub" opacity="0" fill="freeze">')
    w(f'<animate attributeName="opacity" values="0;1" dur="0.4s" '
      f'begin="{ANIM_TOTAL + 0.15:.2f}s" fill="freeze"/>')
    w('FULL-STACK DEVELOPER · AI/ML · SYSTEMS BUILDER</text>')

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

    src = Image.open(SOURCE_IMG)
    print(f"Source: {SOURCE_IMG} ({src.size[0]}×{src.size[1]})")

    # ── Phase 1 ──
    print("\nPhase 1: Generating static ASCII portrait")
    gray, alpha = prep_image(SOURCE_IMG)
    print(f"  Preprocessed size: {gray.shape[1]}×{gray.shape[0]}")

    # Debug image = the exact region converted to ASCII
    debug = Image.fromarray(gray)
    # Draw a thin border so the crop region is obvious
    dbg_px = np.array(debug.convert("RGB"))
    dbg_px[0, :, :] = (255, 64, 64)
    dbg_px[-1, :, :] = (255, 64, 64)
    dbg_px[:, 0, :] = (255, 64, 64)
    dbg_px[:, -1, :] = (255, 64, 64)
    save_debug_face(Image.fromarray(dbg_px))

    ascii_lines = to_ascii(gray, alpha)

    total_chars = COLS * len(ascii_lines)
    non_space = sum(1 for line in ascii_lines for c in line if c != " ")
    max_w = max((len(l) for l in ascii_lines), default=0)
    print(f"  Grid: {COLS} × {len(ascii_lines)} = {total_chars} cells")
    print(f"  Max line width: {max_w} cols")
    print(f"  Non-space: {non_space} ({100 * non_space / max(total_chars,1):.1f}%)")
    h, w_ = gray.shape
    print(f"  Aspect: image {w_}×{h} ({h/w_:.3f}), "
          f"cells {len(ascii_lines)}/{COLS} ({len(ascii_lines)/COLS:.3f}), "
          f"ROW_RATIO={ROW_RATIO}")

    with open(PREVIEW_TXT, "w") as f:
        for row in ascii_lines:
            f.write(row + "\n")
    print(f"  Preview: {PREVIEW_TXT}")

    print("\n--- ASCII PORTRAIT PREVIEW ---\n")
    for row in ascii_lines:
        print(row)
    print("\n--- END PREVIEW ---\n")

    # ── Phase 2 ──
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
