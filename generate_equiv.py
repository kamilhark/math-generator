#!/usr/bin/env python3
"""
Equivalent Fractions Worksheet Generator
Students fill in the missing numerator or denominator to complete an
equivalent fraction, e.g.:
  7/8 = [?]/40    or    3/5 = 60/[?]
"""

import argparse
import random
import os
import string
from datetime import datetime
from math import gcd

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from common import FONT, FONT_BOLD, draw_fraction, draw_cut_line, draw_sheet_id


# ---------------------------------------------------------------------------
# Problem generation
# ---------------------------------------------------------------------------

def generate_problem(max_denom=9, max_mult=12):
    """Return (numer, denom, mult, hide_top).

    The displayed question is:
      numer/denom = [box]/(denom*mult)   when hide_top is True
      numer/denom = (numer*mult)/[box]   when hide_top is False
    """
    while True:
        denom = random.randint(2, max_denom)
        numer = random.randint(1, denom - 1)
        if gcd(numer, denom) != 1:
            continue
        mult = random.randint(2, max_mult)
        hide_top = random.choice([True, False])
        return numer, denom, mult, hide_top


# ---------------------------------------------------------------------------
# PDF drawing
# ---------------------------------------------------------------------------

def draw_fraction_with_box(c, x, y, numer, denom, hide_top, font_size=13):
    """Draw a fraction where either the numerator or denominator is a blank box.

    The box is where the student writes the missing value.
    Returns the total width of the drawn element.
    """
    c.setFont(FONT, font_size)
    ns = str(numer)
    ds = str(denom)
    nw = c.stringWidth(ns, FONT, font_size)
    dw = c.stringWidth(ds, FONT, font_size)

    # Box must be wide enough for up to 3 digits
    vis_w = dw if hide_top else nw
    box_w = max(vis_w + 14, font_size * 2.0)
    w = max(nw, dw, box_w) + 6

    bar_y = y + font_size * 0.15

    if hide_top:
        # Blank box above the bar (for numerator)
        box_h = font_size * 0.9
        bx = x + (w - box_w) / 2
        by = bar_y + 3
        c.rect(bx, by, box_w, box_h)
        # Denominator printed normally
        c.setFont(FONT, font_size)
        c.drawCentredString(x + w / 2, bar_y - font_size + 1, ds)
    else:
        # Numerator printed normally
        c.setFont(FONT, font_size)
        c.drawCentredString(x + w / 2, bar_y + 3, ns)
        # Blank box below the bar (for denominator)
        box_h = font_size * 0.9
        bx = x + (w - box_w) / 2
        by = bar_y - font_size - 1
        c.rect(bx, by, box_w, box_h)

    # Fraction bar
    c.line(x, bar_y, x + w, bar_y)
    return w


def draw_problem(c, x, y, prob, index, font_size=13):
    """Draw one problem at position (x, y). Returns the width used."""
    numer, denom, mult, hide_top = prob
    eq_numer = numer * mult
    eq_denom = denom * mult

    c.setFont(FONT_BOLD, font_size - 1)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT_BOLD, font_size - 1) + 6

    fw = draw_fraction(c, cx, y, numer, denom, font_size)
    cx += fw + 12

    c.setFont(FONT, font_size)
    eq = "="
    c.drawString(cx, y, eq)
    cx += c.stringWidth(eq, FONT, font_size) + 12

    bw = draw_fraction_with_box(c, cx, y, eq_numer, eq_denom, hide_top, font_size)
    cx += bw

    return cx - x


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def build_pdf(filename, num_problems=20, max_denom=9, max_mult=12,
              title="Uzupełnij ułamki równoważne", seed=None):
    if seed is not None:
        random.seed(seed)

    problems = [generate_problem(max_denom, max_mult) for _ in range(num_problems)]
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

    font_size = 13
    row_height = 50

    # Two-column layout: problems side by side
    col_gap = 0.3 * inch
    col_w = (width - 2 * margin_x - col_gap) / 2

    rows_per_page = max(1, int((problems_start_y - problems_end_y) // row_height))
    probs_per_page = rows_per_page * 2  # two columns

    ans_font = 9
    ans_row_h = 20
    ans_cols = 5
    ans_col_w = (width - 2 * margin_x) / ans_cols
    ans_top_y = cut_line_y - 22

    page_problems = []
    for i in range(0, num_problems, probs_per_page):
        page_problems.append(problems[i:i + probs_per_page])

    for page_idx, page_probs in enumerate(page_problems):
        if page_idx > 0:
            c.showPage()

        # Title
        c.setFont(FONT_BOLD, 18)
        c.drawCentredString(width / 2, top_y, title)
        draw_sheet_id(c, width - margin_x, top_y + 2, sheet_id)

        # Problems in two columns
        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            col = i % 2
            row = i // 2
            px = margin_x + col * (col_w + col_gap)
            py = problems_start_y - row * row_height
            draw_problem(c, px, py, prob, global_idx, font_size)

        # Cut line
        draw_cut_line(c, cut_line_y, margin_x, width)

        # Answer key
        draw_sheet_id(c, width - margin_x, cut_line_y - 13, sheet_id)

        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            numer, denom, mult, hide_top = prob
            answer = numer * mult if hide_top else denom * mult

            col = i % ans_cols
            row = i // ans_cols
            ax = margin_x + col * ans_col_w
            ay = ans_top_y - row * ans_row_h

            c.setFont(FONT, ans_font)
            c.drawString(ax, ay, f"{global_idx}. {answer}")

    c.save()
    return os.path.abspath(filename)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a PDF worksheet of equivalent-fraction fill-in problems."
    )
    parser.add_argument("-n", "--num-problems", type=int, default=20,
                        help="Number of problems (default: 20)")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output PDF filename")
    parser.add_argument("--max-denom", type=int, default=9,
                        help="Largest denominator for the base fraction (default: 9)")
    parser.add_argument("--max-mult", type=int, default=12,
                        help="Largest multiplier (default: 12)")
    parser.add_argument("--title", type=str,
                        default="Uzupełnij ułamki równoważne",
                        help="Worksheet title")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"equiv_{ts}.pdf"

    path = build_pdf(
        filename=args.output,
        num_problems=args.num_problems,
        max_denom=args.max_denom,
        max_mult=args.max_mult,
        title=args.title,
        seed=args.seed,
    )
    print(f"Worksheet saved to: {path}")
    print(f"  {args.num_problems} problems  |  max denominator: {args.max_denom}"
          f"  |  max multiplier: {args.max_mult}")


if __name__ == "__main__":
    main()
