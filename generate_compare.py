#!/usr/bin/env python3
"""
Fraction Comparison Worksheet Generator
Students place <, =, or > between two fractions, e.g.:
  7/9  [  ]  5/9       3/8  [  ]  3/7
Four problem types are generated in random mix:
  - same_denom  : a/c vs b/c  (compare numerators)
  - same_numer  : a/b vs a/c  (compare denominators — inverse)
  - different   : random proper fractions with different n & d
  - equal       : two equivalent representations of the same value
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
from sympy import Rational

from common import FONT, FONT_BOLD, draw_fraction, draw_cut_line, draw_sheet_id


# ---------------------------------------------------------------------------
# Problem generation
# ---------------------------------------------------------------------------

PROBLEM_TYPES = ["same_denom", "same_numer", "different", "equal"]


def _reduced(n, d):
    g = gcd(abs(n), abs(d))
    return n // g, d // g


def generate_same_denom(max_denom=12):
    """a/d vs b/d  —  a ≠ b, both proper, d shared."""
    d = random.randint(3, max_denom)
    a = random.randint(1, d - 1)
    b = random.randint(1, d - 1)
    while b == a:
        b = random.randint(1, d - 1)
    return a, d, b, d


def generate_same_numer(max_denom=12):
    """a/b vs a/c  —  b ≠ c."""
    a = random.randint(1, max_denom - 2)
    b = random.randint(a + 1, max_denom)
    c = random.randint(a + 1, max_denom)
    while c == b:
        c = random.randint(a + 1, max_denom)
    return a, b, a, c


def generate_different(max_denom=10):
    """Two random proper fractions, at least one digit differs."""
    while True:
        d1 = random.randint(2, max_denom)
        n1 = random.randint(1, d1 - 1)
        d2 = random.randint(2, max_denom)
        n2 = random.randint(1, d2 - 1)
        r1, r2 = Rational(n1, d1), Rational(n2, d2)
        if r1 == r2:
            continue
        if (n1, d1) == (n2, d2):
            continue
        return n1, d1, n2, d2


def generate_equal(max_denom=8, max_mult=6):
    """Two different-looking fractions that are actually equal."""
    while True:
        d = random.randint(2, max_denom)
        n = random.randint(1, d - 1)
        if gcd(n, d) != 1:
            continue
        k1 = random.randint(2, max_mult)
        k2 = random.randint(2, max_mult)
        while k2 == k1:
            k2 = random.randint(2, max_mult)
        return n * k1, d * k1, n * k2, d * k2


def generate_problem(max_denom=12, problem_types=None):
    """Return (n1, d1, n2, d2, sign)."""
    if problem_types is None:
        problem_types = PROBLEM_TYPES

    kind = random.choice(problem_types)
    if kind == "same_denom":
        n1, d1, n2, d2 = generate_same_denom(max_denom)
    elif kind == "same_numer":
        n1, d1, n2, d2 = generate_same_numer(max_denom)
    elif kind == "equal":
        n1, d1, n2, d2 = generate_equal(min(max_denom, 8))
    else:
        n1, d1, n2, d2 = generate_different(max_denom)

    r1, r2 = Rational(n1, d1), Rational(n2, d2)
    if r1 < r2:
        sign = "<"
    elif r1 > r2:
        sign = ">"
    else:
        sign = "="
    return n1, d1, n2, d2, sign


# ---------------------------------------------------------------------------
# PDF drawing
# ---------------------------------------------------------------------------

BOX_SIZE = 18   # side length of the blank sign box (points)


def draw_sign_box(c, x, y):
    """Draw an empty square box centred vertically on y. Returns width."""
    by = y - BOX_SIZE * 0.35
    c.rect(x, by, BOX_SIZE, BOX_SIZE)
    return BOX_SIZE


def draw_problem(c, x, y, prob, index, font_size=13):
    """Draw one comparison problem at (x, y). Returns width used."""
    n1, d1, n2, d2, _sign = prob

    c.setFont(FONT_BOLD, font_size - 1)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT_BOLD, font_size - 1) + 6

    fw1 = draw_fraction(c, cx, y, n1, d1, font_size)
    cx += fw1 + 10

    bw = draw_sign_box(c, cx, y)
    cx += bw + 10

    draw_fraction(c, cx, y, n2, d2, font_size)

    return cx - x


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def build_pdf(filename, num_problems=20, max_denom=12,
              problem_types=None,
              title="Porównaj ułamki: wpisz <, = lub >", seed=None):
    if seed is not None:
        random.seed(seed)

    problems = [generate_problem(max_denom, problem_types)
                for _ in range(num_problems)]
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

    # Two-column layout
    col_gap = 0.3 * inch
    col_w = (width - 2 * margin_x - col_gap) / 2

    rows_per_page = max(1, int((problems_start_y - problems_end_y) // row_height))
    probs_per_page = rows_per_page * 2

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
            sign = prob[4]
            col = i % ans_cols
            row = i // ans_cols
            ax = margin_x + col * ans_col_w
            ay = ans_top_y - row * ans_row_h
            c.setFont(FONT, ans_font)
            c.drawString(ax, ay, f"{global_idx}. {sign}")

    c.save()
    return os.path.abspath(filename)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a PDF worksheet of fraction comparison problems."
    )
    parser.add_argument("-n", "--num-problems", type=int, default=20,
                        help="Number of problems (default: 20)")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output PDF filename")
    parser.add_argument("--max-denom", type=int, default=12,
                        help="Largest denominator (default: 12)")
    parser.add_argument("--types", type=str, default=None,
                        help="Comma-separated problem types to include: "
                             "same_denom, same_numer, different, equal "
                             "(default: all)")
    parser.add_argument("--title", type=str,
                        default="Porównaj ułamki: wpisz <, = lub >",
                        help="Worksheet title")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.types:
        valid = set(PROBLEM_TYPES)
        chosen = [t.strip() for t in args.types.split(",")]
        bad = [t for t in chosen if t not in valid]
        if bad:
            parser.error(f"Unknown problem type(s): {bad}. "
                         f"Valid: {', '.join(PROBLEM_TYPES)}")
        problem_types = chosen
    else:
        problem_types = None

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"compare_{ts}.pdf"

    path = build_pdf(
        filename=args.output,
        num_problems=args.num_problems,
        max_denom=args.max_denom,
        problem_types=problem_types,
        title=args.title,
        seed=args.seed,
    )
    print(f"Worksheet saved to: {path}")
    types_used = problem_types or PROBLEM_TYPES
    print(f"  {args.num_problems} problems  |  types: {', '.join(types_used)}")


if __name__ == "__main__":
    main()
