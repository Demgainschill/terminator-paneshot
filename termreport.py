#!/usr/bin/env python3
"""
termreport — Render full terminal scrollback into report-ready PNG images.
Organizes output by tool name for structured reporting.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Basic ANSI color mapping
COLOR_MAP = {
    '30': (0, 0, 0), '31': (205, 49, 49), '32': (13, 188, 121),
    '33': (229, 229, 16), '34': (36, 114, 200), '35': (188, 63, 188),
    '36': (17, 168, 205), '37': (229, 229, 229),
    '90': (128, 128, 128), '91': (241, 76, 76), '92': (35, 209, 139),
    '93': (245, 245, 67), '94': (59, 142, 234), '95': (214, 112, 214),
    '96': (41, 184, 219), '97': (255, 255, 255),
}

def split_ansi(line):
    """Break a line into text segments with their colors."""
    pieces = []
    color = (220, 220, 220)
    tokens = re.split(r'(\x1b\[[0-9;]*m)', line)
    for token in tokens:
        if token.startswith('\x1b['):
            codes = token[2:-1].split(';')
            for code in codes:
                if code in COLOR_MAP:
                    color = COLOR_MAP[code]
                elif code in ('0', '39'):
                    color = (220, 220, 220)
        elif token:
            pieces.append((token, color))
    return pieces or [(line, color)]

def build_image(content, heading="Terminal Output", max_cols=140, size=15):
    raw_lines = content.splitlines() or [""]
    final_lines = []
    for raw in raw_lines:
        plain = re.sub(r'\x1b\[[0-9;]*m', '', raw)
        if len(plain) > max_cols:
            while len(plain) > max_cols:
                final_lines.append(plain[:max_cols])
                plain = plain[max_cols:]
            if plain:
                final_lines.append(plain)
        else:
            final_lines.append(raw)

    font = None
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ):
        try:
            font = ImageFont.truetype(path, size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = font.getbbox("M")
    cw = bbox[2] - bbox[0]
    ch = bbox[3] - bbox[1] + 6

    pad_x, pad_y = 24, 16
    bar_h = 42
    width = max_cols * cw + pad_x * 2
    height = len(final_lines) * ch + pad_y * 2 + bar_h

    canvas = Image.new("RGB", (width, max(height, 200)), (28, 28, 28))
    draw = ImageDraw.Draw(canvas)

    draw.rectangle([0, 0, width, bar_h], fill=(42, 42, 42))
    draw.text((pad_x, 12), heading, fill=(230, 230, 230), font=font)

    y = bar_h + pad_y
    for line in final_lines:
        x = pad_x
        for text, col in split_ansi(line):
            draw.text((x, y), text, fill=col, font=font)
            x += len(text) * cw
        y += ch

    return canvas

def main():
    parser = argparse.ArgumentParser(
        description="Turn terminal scrollback into report PNGs"
    )
    parser.add_argument("-t", "--tool", required=True,
                        help="Tool or category name used for folder organization")
    parser.add_argument("-f", "--file", help="Text file containing scrollback (default: stdin)")
    parser.add_argument("--title", help="Title shown in the image header")
    parser.add_argument("-o", "--output", default="./reports",
                        help="Base directory for output images")
    parser.add_argument("--width", type=int, default=140,
                        help="Maximum characters per line")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", errors="replace") as fh:
            data = fh.read()
    else:
        data = sys.stdin.read()

    if not data.strip():
        print("Error: empty input", file=sys.stderr)
        sys.exit(1)

    heading = args.title or f"{args.tool} — Terminal Output"
    image = build_image(data, heading=heading, max_cols=args.width)

    safe_name = args.tool.lower().replace(" ", "_").replace("/", "_")
    dest = Path(args.output) / safe_name
    dest.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = dest / f"{safe_name}_{stamp}.png"
    image.save(out_file, "PNG", optimize=True)

    print(f"Saved: {out_file}")
    print(f"Lines: {len(data.splitlines())}")

if __name__ == "__main__":
    main()
