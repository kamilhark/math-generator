#!/usr/bin/env python3
"""
Decimal Fraction Addition/Subtraction Worksheet Generator
Produces PDF worksheets for 12-year-olds: add and subtract decimal numbers.
"""

import argparse
import random
import os
import string
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from sympy import Rational

from common import (
    FONT, FONT_BOLD,
    draw_cut_line, draw_sheet_id, draw_answer_value,
)

PAGE_W, PAGE_H = LETTER
MARGIN_X       = 0.75 * inch
MARGIN_Y_TOP   = 0.5 * inch
ANSWER_ZONE    = 1.75 * inch
ROW_H          = 28
FONT_SIZE      = 12
ANS_FONT_SIZE  = 9

LEVELS = ['1', '2', 'mix']


# ---------------------------------------------------------------------------
# Part 1 — Problem generation
# ---------------------------------------------------------------------------

def _random_decimal(places, max_val=9):
    """Return a Rational and its decimal-place count."""
    scale = 10 ** places
    val_int = random.randint(1, scale * max_val - 1)
    return Rational(val_int, scale), places


def _fmt(r, places):
    """Format Rational as Polish decimal string with `places` decimal places."""
    scale = 10 ** places
    total = int(r * scale)
    whole = total // scale
    frac  = total % scale
    return f"{whole},{str(frac).zfill(places)}"


def generate_problem(level='mix', operations=None):
    """Return (a_str, b_str, op, ans_str, ans_places) for one problem."""
    if operations is None:
        operations = ['+', '-']
    op = random.choice(operations)

    if level == '1':
        places_a = places_b = 1
    elif level == '2':
        places_a = places_b = 2
    else:  # mix
        places_a = random.choice([1, 2])
        places_b = random.choice([1, 2])

    a, pa = _random_decimal(places_a)
    b, pb = _random_decimal(places_b)

    if op == '-' and a < b:
        a, b = b, a
        pa, pb = pb, pa

    ans = a + b if op == '+' else a - b
    ans_places = max(pa, pb)

    return _fmt(a, pa), _fmt(b, pb), op, _fmt(ans, ans_places)


# ---------------------------------------------------------------------------
# Part 2 — PDF drawing
# ---------------------------------------------------------------------------

def draw_problem(c, x, y, prob, index, font_size=FONT_SIZE):
    """Draw one problem on the worksheet."""
    a_str, b_str, op, _ = prob

    c.setFont(FONT_BOLD, font_size - 1)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT_BOLD, font_size - 1) + 6

    c.setFont(FONT, font_size)
    op_str = "+" if op == "+" else "−"
    problem_text = f"{a_str}  {op_str}  {b_str}  ="
    c.drawString(cx, y, problem_text)
    cx += c.stringWidth(problem_text, FONT, font_size) + 8

    # answer blank line
    c.setStrokeColorRGB(0.75, 0.75, 0.75)
    c.setDash(2, 3)
    c.line(cx, y - 3, cx + 70, y - 3)
    c.setDash()
    c.setStrokeColorRGB(0, 0, 0)


def draw_answer(c, x, y, prob, index, font_size=ANS_FONT_SIZE):
    """Draw the answer below the cut line."""
    _, _, _, ans_str = prob
    c.setFont(FONT, font_size)
    c.drawString(x, y, f"{index}. {ans_str}")


# ---------------------------------------------------------------------------
# Part 3 — PDF builder
# ---------------------------------------------------------------------------

def build_pdf(filename, num_problems=20, level='mix', operations=None,
              title="Dodawanie i odejmowanie ułamków dziesiętnych", seed=None):
    """Build the worksheet PDF. Returns absolute path."""
    if seed is not None:
        random.seed(seed)

    sheet_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    problems = [generate_problem(level, operations) for _ in range(num_problems)]

    width, height = LETTER
    c = canvas.Canvas(filename, pagesize=LETTER)
    margin_x = 0.75 * inch
    top_y = height - 0.75 * inch
    bottom_margin = 0.5 * inch

    answer_zone_h = 1.75 * inch
    cut_line_y = bottom_margin + answer_zone_h
    problems_start_y = top_y - 55
    problems_end_y = cut_line_y + 15

    row_height = 46
    rows_per_page = max(1, int((problems_start_y - problems_end_y) // row_height))

    ans_row_h = 20
    ans_cols = 5
    ans_col_w = (width - 2 * margin_x) / ans_cols
    ans_top_y = cut_line_y - 22

    page_problems = []
    for i in range(0, num_problems, rows_per_page):
        page_problems.append(problems[i:i + rows_per_page])

    for page_idx, page_probs in enumerate(page_problems):
        if page_idx > 0:
            c.showPage()

        # header
        c.setFont(FONT_BOLD, 18)
        c.drawCentredString(width / 2, top_y, title)
        draw_sheet_id(c, width - margin_x, top_y + 2, sheet_id)

        # problems
        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            py = problems_start_y - i * row_height
            draw_problem(c, margin_x, py, prob, global_idx)

        # cut line + answers
        draw_cut_line(c, cut_line_y, margin_x, width)
        draw_sheet_id(c, width - margin_x, cut_line_y - 13, sheet_id)

        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            col = i % ans_cols
            row = i // ans_cols
            ax = margin_x + col * ans_col_w
            ay = ans_top_y - row * ans_row_h
            draw_answer(c, ax, ay, prob, global_idx)

    c.save()
    return os.path.abspath(filename)


# ---------------------------------------------------------------------------
# Part 4 — CLI
# ---------------------------------------------------------------------------

def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p = argparse.ArgumentParser(
        description="Generate decimal fraction add/subtract worksheet PDF."
    )
    p.add_argument("-n", "--num-problems", type=int, default=20)
    p.add_argument("-o", "--output", default=f"worksheet_{ts}.pdf")
    p.add_argument("--level", choices=LEVELS, default="mix",
                   help="1=tenths, 2=hundredths, mix=both (default: mix)")
    p.add_argument("--ops", default="+,-",
                   help="Comma-separated operations: +,- (default: +,-)")
    p.add_argument("--title", default="Dodawanie i odejmowanie ułamków dziesiętnych")
    p.add_argument("--seed", type=int)
    args = p.parse_args()

    operations = [op.strip() for op in args.ops.split(",")]
    path = build_pdf(args.output, args.num_problems, args.level,
                     operations, args.title, args.seed)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
