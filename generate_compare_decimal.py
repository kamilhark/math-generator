#!/usr/bin/env python3
"""
Decimal vs Fraction Comparison Worksheet Generator
Students place <, =, or > between two values, e.g.:
  0.3  [  ]  0.7      0.75  [  ]  3/4      2/5  [  ]  0.6

Four problem types:
  - decimal_decimal  : two decimal numbers (1-2 decimal places)
  - decimal_fraction : decimal  vs common fraction
  - fraction_decimal : common fraction vs decimal
  - equal            : equal decimal/fraction pairs (e.g. 0.5 = 1/2)
"""

import argparse
import random
import os
import string
from datetime import datetime
from fractions import Fraction

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from common import FONT, FONT_BOLD, draw_fraction, draw_cut_line, draw_sheet_id


# ---------------------------------------------------------------------------
# Problem generation
# ---------------------------------------------------------------------------

PROBLEM_TYPES = ["decimal_decimal", "decimal_fraction", "fraction_decimal", "equal"]

BOX_SIZE = 18

# Fractions that have exact finite decimal representations
EXACT_PAIRS = [
    (Fraction(1, 2),   "0.5"),
    (Fraction(1, 4),   "0.25"),
    (Fraction(3, 4),   "0.75"),
    (Fraction(1, 5),   "0.2"),
    (Fraction(2, 5),   "0.4"),
    (Fraction(3, 5),   "0.6"),
    (Fraction(4, 5),   "0.8"),
    (Fraction(1, 10),  "0.1"),
    (Fraction(3, 10),  "0.3"),
    (Fraction(7, 10),  "0.7"),
    (Fraction(9, 10),  "0.9"),
    (Fraction(1, 8),   "0.125"),
    (Fraction(3, 8),   "0.375"),
    (Fraction(5, 8),   "0.625"),
    (Fraction(7, 8),   "0.875"),
    (Fraction(1, 20),  "0.05"),
    (Fraction(3, 20),  "0.15"),
    (Fraction(1, 25),  "0.04"),
    (Fraction(2, 25),  "0.08"),
]


def rand_decimal():
    """Return (string, Fraction) with 1–2 decimal places, value in [0.01, 1.99]."""
    if random.random() < 0.6:
        # 1 decimal place: 0.1 … 1.9
        n = random.randint(1, 19)
        return f"{n / 10:.1f}", Fraction(n, 10)
    # 2 decimal places, no trailing zero
    while True:
        n = random.randint(1, 199)
        if n % 10 != 0:
            return f"{n / 100:.2f}", Fraction(n, 100)


def rand_fraction():
    """Return (numer, denom) as a simple fraction (denominator in a school-friendly set)."""
    denom = random.choice([2, 3, 4, 5, 8, 10])
    numer = random.randint(1, int(denom * 1.8))
    return numer, denom


def _sign(a, b):
    if a < b:
        return "<"
    if a > b:
        return ">"
    return "="


def generate_decimal_decimal():
    """Two random decimals that are not equal."""
    while True:
        s1, f1 = rand_decimal()
        s2, f2 = rand_decimal()
        if f1 != f2:
            return ("d", s1), ("d", s2), _sign(f1, f2)


def generate_decimal_fraction(flip=False):
    """Decimal vs common fraction (or reversed if flip=True)."""
    s, d_frac = rand_decimal()
    numer, denom = rand_fraction()
    f = Fraction(numer, denom)
    if not flip:
        return ("d", s), ("f", numer, denom), _sign(d_frac, f)
    else:
        return ("f", numer, denom), ("d", s), _sign(f, d_frac)


def generate_equal():
    """An equal decimal/fraction pair from the exact-pairs list."""
    frac, dec_str = random.choice(EXACT_PAIRS)
    n, d = frac.numerator, frac.denominator
    if random.random() < 0.5:
        return ("d", dec_str), ("f", n, d), "="
    else:
        return ("f", n, d), ("d", dec_str), "="


def generate_problem(problem_types=None):
    if problem_types is None:
        problem_types = PROBLEM_TYPES
    kind = random.choice(problem_types)
    if kind == "decimal_decimal":
        return generate_decimal_decimal()
    elif kind == "decimal_fraction":
        return generate_decimal_fraction(flip=False)
    elif kind == "fraction_decimal":
        return generate_decimal_fraction(flip=True)
    else:
        return generate_equal()


# ---------------------------------------------------------------------------
# PDF drawing
# ---------------------------------------------------------------------------

def draw_side(c, x, y, side, font_size=13):
    """Draw one side of a comparison (decimal string or fraction). Returns width."""
    if side[0] == "d":
        c.setFont(FONT, font_size)
        w = c.stringWidth(side[1], FONT, font_size)
        c.drawString(x, y, side[1])
        return w
    else:
        return draw_fraction(c, x, y, side[1], side[2], font_size)


def draw_sign_box(c, x, y):
    """Draw an empty square box centred on y. Returns width."""
    by = y - BOX_SIZE * 0.35
    c.rect(x, by, BOX_SIZE, BOX_SIZE)
    return BOX_SIZE


def draw_problem(c, x, y, prob, index, font_size=13):
    """Draw one comparison problem at (x, y)."""
    left, right, _sign = prob

    c.setFont(FONT_BOLD, font_size - 1)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT_BOLD, font_size - 1) + 6

    lw = draw_side(c, cx, y, left, font_size)
    cx += lw + 12

    bw = draw_sign_box(c, cx, y)
    cx += bw + 12

    draw_side(c, cx, y, right, font_size)


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def build_pdf(filename, num_problems=20, problem_types=None,
              title="Porównaj ułamki dziesiętne i zwykłe: wpisz <, = lub >",
              seed=None):
    if seed is not None:
        random.seed(seed)

    problems = [generate_problem(problem_types) for _ in range(num_problems)]
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
        c.setFont(FONT_BOLD, 16)
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

        # Cut line + answer key
        draw_cut_line(c, cut_line_y, margin_x, width)
        draw_sheet_id(c, width - margin_x, cut_line_y - 13, sheet_id)

        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            sign = prob[2]
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
        description="Generate a PDF worksheet comparing decimals and fractions."
    )
    parser.add_argument("-n", "--num-problems", type=int, default=20,
                        help="Number of problems (default: 20)")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output PDF filename")
    parser.add_argument("--types", type=str, default=None,
                        help="Comma-separated problem types: "
                             "decimal_decimal, decimal_fraction, fraction_decimal, equal "
                             "(default: all)")
    parser.add_argument("--title", type=str,
                        default="Porównaj ułamki dziesiętne i zwykłe: wpisz <, = lub >",
                        help="Worksheet title")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.types:
        valid = set(PROBLEM_TYPES)
        chosen = [t.strip() for t in args.types.split(",")]
        bad = [t for t in chosen if t not in valid]
        if bad:
            parser.error(f"Unknown type(s): {bad}. Valid: {', '.join(PROBLEM_TYPES)}")
        problem_types = chosen
    else:
        problem_types = None

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"compare_decimal_{ts}.pdf"

    path = build_pdf(
        filename=args.output,
        num_problems=args.num_problems,
        problem_types=problem_types,
        title=args.title,
        seed=args.seed,
    )
    print(f"Worksheet saved to: {path}")
    types_used = problem_types or PROBLEM_TYPES
    print(f"  {args.num_problems} problems  |  types: {', '.join(types_used)}")


if __name__ == "__main__":
    main()
