#!/usr/bin/env python3
"""
Improper Fraction ↔ Mixed Number Conversion Worksheet Generator
Two types of problems:
  - Convert an improper fraction to a mixed number
  - Convert a mixed number to an improper fraction
"""

import argparse
import random
import os
import string
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from common import (
    FONT, FONT_BOLD,
    draw_fraction, draw_cut_line, draw_sheet_id, mixed_to_rational, rational_parts,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_conversion_problem(max_whole=5, max_denom=10):
    """Return (direction, numer, denom, whole, remainder).

    direction: 'to_mixed' or 'to_improper'
    For to_mixed:   given numer/denom (improper), answer is whole rem/denom
    For to_improper: given whole rem/denom (mixed), answer is numer/denom
    """
    denom = random.randint(2, max_denom)
    whole = random.randint(1, max_whole)
    remainder = random.randint(1, denom - 1)
    numer, _ = rational_parts(mixed_to_rational(whole, remainder, denom))

    direction = random.choice(["to_mixed", "to_improper"])
    return direction, numer, denom, whole, remainder


# ---------------------------------------------------------------------------
# PDF drawing
# ---------------------------------------------------------------------------

def draw_mixed(c, x, y, whole, rem, denom, font_size=14):
    """Draw a mixed number like  3 2/5. Returns width."""
    ws = str(whole)
    c.setFont(FONT, font_size)
    c.drawString(x, y, ws)
    ww = c.stringWidth(ws, FONT, font_size)
    x += ww + 2
    fw = draw_fraction(c, x, y, rem, denom, font_size)
    return ww + 2 + fw


def draw_problem_row(c, x, y, prob, index, line_end_x=None, font_size=12):
    direction, numer, denom, whole, remainder = prob

    c.setFont(FONT_BOLD, font_size - 1)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT_BOLD, font_size - 1) + 6

    if direction == "to_mixed":
        fw = draw_fraction(c, cx, y, numer, denom, font_size)
        cx += fw + 10
    else:
        mw = draw_mixed(c, cx, y, whole, remainder, denom, font_size)
        cx += mw + 10

    c.setFont(FONT, font_size)
    c.drawString(cx, y, "=")
    cx += c.stringWidth("=", FONT, font_size) + 8

    if line_end_x is None:
        line_end_x = cx + 70

    c.setStrokeColorRGB(0.75, 0.75, 0.75)
    c.setDash(2, 3)
    c.line(cx, y - 4, line_end_x, y - 4)
    c.setDash()
    c.setStrokeColorRGB(0, 0, 0)


def draw_answer_row(c, x, y, prob, index, font_size=11):
    direction, numer, denom, whole, remainder = prob

    c.setFont(FONT, font_size)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT, font_size) + 4

    if direction == "to_mixed":
        draw_mixed(c, cx, y, whole, remainder, denom, font_size)
    else:
        draw_fraction(c, cx, y, numer, denom, font_size)


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def build_pdf(filename, num_problems=20, max_whole=5, max_denom=10,
              title="Ułamki niewłaściwe i liczby mieszane", seed=None):
    if seed is not None:
        random.seed(seed)

    problems = [generate_conversion_problem(max_whole, max_denom) for _ in range(num_problems)]

    sheet_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    width, height = LETTER
    c = canvas.Canvas(filename, pagesize=LETTER)
    margin_x = 0.75 * inch
    top_y = height - 0.75 * inch
    bottom_margin = 0.5 * inch

    answer_zone_h = 1.75 * inch
    cut_line_y = bottom_margin + answer_zone_h
    problems_start_y = top_y - 60
    problems_end_y = cut_line_y + 15

    font_size = 12
    row_height = 46
    rows_per_page = max(1, int((problems_start_y - problems_end_y) // row_height))
    page_capacity = rows_per_page

    ans_font = 9
    ans_row_h = 20
    ans_cols = 5
    ans_col_w = (width - 2 * margin_x) / ans_cols
    ans_top_y = cut_line_y - 22

    page_problems = []
    for i in range(0, num_problems, page_capacity):
        page_problems.append(problems[i:i + page_capacity])

    for page_idx, page_probs in enumerate(page_problems):
        if page_idx > 0:
            c.showPage()

        # Title & header
        c.setFont(FONT_BOLD, 18)
        c.drawCentredString(width / 2, top_y, title)
        draw_sheet_id(c, width - margin_x, top_y + 2, sheet_id)

        # Problems
        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            px = margin_x
            py = problems_start_y - i * row_height
            draw_problem_row(c, px, py, prob, global_idx, width - margin_x, font_size)

        # Cut line
        draw_cut_line(c, cut_line_y, margin_x, width)

        # Answers below the cut line
        draw_sheet_id(c, width - margin_x, cut_line_y - 13, sheet_id)

        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            col = i % ans_cols
            row = i // ans_cols
            ax = margin_x + col * ans_col_w
            ay = ans_top_y - row * ans_row_h
            draw_answer_row(c, ax, ay, prob, global_idx, ans_font)

    c.save()
    return os.path.abspath(filename)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a PDF worksheet for converting between "
                    "improper fractions and mixed numbers."
    )
    parser.add_argument("-n", "--num-problems", type=int, default=20,
                        help="Number of problems (default: 20)")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output PDF filename")
    parser.add_argument("--max-whole", type=int, default=5,
                        help="Maximum whole-number part (default: 5)")
    parser.add_argument("--max-denom", type=int, default=10,
                        help="Maximum denominator (default: 10)")
    parser.add_argument("--title", type=str,
                        default="Ułamki niewłaściwe i liczby mieszane",
                        help="Worksheet title")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"convert_{ts}.pdf"

    path = build_pdf(
        filename=args.output,
        num_problems=args.num_problems,
        max_whole=args.max_whole,
        max_denom=args.max_denom,
        title=args.title,
        seed=args.seed,
    )
    print(f"Worksheet saved to: {path}")
    print(f"  {args.num_problems} conversion problems")


if __name__ == "__main__":
    main()
