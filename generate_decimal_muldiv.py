#!/usr/bin/env python3
"""
Decimal Fraction Multiplication/Division Worksheet Generator
Produces PDF worksheets for 12-year-olds: multiply and divide decimal numbers.
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
    draw_cut_line, draw_sheet_id,
)

PAGE_W, PAGE_H = LETTER
MARGIN_X       = 0.75 * inch
MARGIN_Y_TOP   = 0.5 * inch
ANSWER_ZONE    = 1.75 * inch
ROW_H          = 28
FONT_SIZE      = 12
ANS_FONT_SIZE  = 9

LEVELS = ['1', '2', '3', 'mix']


# ---------------------------------------------------------------------------
# Part 1 — Problem generation
# ---------------------------------------------------------------------------

def _fmt(r, places):
    """Format Rational as Polish decimal string with `places` decimal places."""
    if places == 0:
        return str(int(r))
    scale = 10 ** places
    total = int(r * scale)
    whole = total // scale
    frac  = total % scale
    return f"{whole},{str(frac).zfill(places)}"


def _places_of(r):
    """Return min decimal places needed to represent Rational r exactly (0–4)."""
    for p in range(0, 5):
        if (r * 10 ** p).denominator == 1:
            return p
    return 4


def generate_problem(level='mix', operations=None):
    """Return (a_str, b_str, op, ans_str) for one problem."""
    if operations is None:
        operations = ['×', '÷']
    op = random.choice(operations)

    if level == 'mix':
        level = random.choice(['1', '2', '3'])

    if op == '×':
        if level == '1':
            # decimal (1 place, 1.1–9.9) × whole number (2–9)
            a = Rational(random.randint(11, 99), 10)
            b = Rational(random.randint(2, 9))
        elif level == '2':
            # decimal (1 place) × decimal (1 place), kept small
            a = Rational(random.randint(11, 49), 10)   # 1.1–4.9
            b = Rational(random.randint(11, 19), 10)   # 1.1–1.9
        else:
            # decimal (2 places) × decimal (1 place) → up to 3 decimal places
            # avoid multiples of 10 in last digit so answer doesn't simplify heavily
            a_int = random.choice([n for n in range(111, 500) if n % 10 != 0])
            a = Rational(a_int, 100)                   # 1.11–4.99 (true 2 places)
            b = Rational(random.randint(11, 19), 10)   # 1.1–1.9
        ans = a * b
        ans_p = _places_of(ans)
        a_p = 1 if level in ('1', '2') else 2
        return _fmt(a, a_p), _fmt(b, _places_of(b)), op, _fmt(ans, ans_p)

    else:  # ÷
        if level == '1':
            # decimal (1 place) ÷ whole number (2–5) = decimal (1 place)
            b = random.randint(2, 5)
            q = Rational(random.randint(11, 25), 10)   # 1.1–2.5
            a = Rational(b) * q
            a_p = max(1, _places_of(a))
            return _fmt(a, a_p), str(b), op, _fmt(q, 1)
        elif level == '2':
            # decimal (1 place) ÷ decimal (1 place) = whole number
            b_int = random.choice([2, 3, 4, 5, 6, 8])
            b = Rational(b_int, 10)                    # 0.2–0.8
            q = random.randint(2, 12)
            a = b * q
            a_p = max(1, _places_of(a))
            return _fmt(a, a_p), _fmt(b, 1), op, str(q)
        else:
            # decimal (2 places) ÷ whole number (2–4) = decimal (2 places)
            b = random.randint(2, 4)
            q_int = random.choice([n for n in range(111, 499) if n % 10 != 0])
            q = Rational(q_int, 100)                   # 1.11–4.99 (true 2 places)
            a = Rational(b) * q
            a_p = max(2, _places_of(a))
            return _fmt(a, a_p), str(b), op, _fmt(q, 2)


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
    op_char = "×" if op == "×" else "÷"
    problem_text = f"{a_str}  {op_char}  {b_str}  ="
    c.drawString(cx, y, problem_text)
    cx += c.stringWidth(problem_text, FONT, font_size) + 8

    # answer blank
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
              title="Mnożenie i dzielenie ułamków dziesiętnych", seed=None):
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
        description="Generate decimal fraction multiply/divide worksheet PDF."
    )
    p.add_argument("-n", "--num-problems", type=int, default=20)
    p.add_argument("-o", "--output", default=f"worksheet_{ts}.pdf")
    p.add_argument("--level", choices=LEVELS, default="mix",
                   help="1=decimal×whole, 2=decimal×decimal, mix=both (default: mix)")
    p.add_argument("--ops", default="×,÷",
                   help="Comma-separated operations: ×,÷ (default: ×,÷)")
    p.add_argument("--title", default="Mnożenie i dzielenie ułamków dziesiętnych")
    p.add_argument("--seed", type=int)
    args = p.parse_args()

    operations = [op.strip() for op in args.ops.split(",")]
    path = build_pdf(args.output, args.num_problems, args.level,
                     operations, args.title, args.seed)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
