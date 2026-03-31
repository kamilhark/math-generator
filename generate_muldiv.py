#!/usr/bin/env python3
"""
Fraction Multiplication & Division Worksheet Generator
- Multiplication: two fractions (mixed or improper), answer simplified
- Division: engineered so every answer is a whole number (no remainder)
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
    FONT, FONT_BOLD, rational_parts, simplify, draw_mixed_or_improper,
    draw_cut_line, draw_sheet_id, draw_answer_value,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pick_simple_fraction(max_denom=8):
    """Return (numer, denom) for a proper fraction with small values."""
    d = random.randint(2, max_denom)
    n = random.randint(1, d - 1)
    n, d = simplify(n, d)
    return n, d


def pick_operand(max_whole=3, max_denom=6):
    """Return (numer, denom, style) — a mixed number or improper fraction,
    kept small for 12-year-olds."""
    style = random.choice(["mixed", "improper"])
    denom = random.randint(2, max_denom)
    if style == "mixed":
        whole = random.randint(1, max_whole)
        numer = random.randint(1, denom - 1)
        return whole * denom + numer, denom, "mixed"
    else:
        numer = random.randint(denom + 1, denom * 2)
        return numer, denom, "improper"


# ---------------------------------------------------------------------------
# Problem generation
# ---------------------------------------------------------------------------

def generate_mul_problem(max_whole=3, max_denom=6):
    """Multiplication: pick two fractions, multiply them."""
    a_n, a_d, a_style = pick_operand(max_whole, max_denom)
    b_n, b_d, b_style = pick_operand(max_whole, max_denom)
    ans = Rational(a_n, a_d) * Rational(b_n, b_d)
    ans_n, ans_d = rational_parts(ans)
    return a_n, a_d, a_style, "×", b_n, b_d, b_style, ans_n, ans_d


def generate_div_problem(max_whole=3, max_denom=6):
    """Division: engineered so the answer is always a whole number.
    We pick an integer answer and a divisor fraction, then compute the dividend."""
    answer = random.randint(1, 8)
    b_n, b_d, b_style = pick_operand(max_whole, max_denom)

    a_frac = Rational(answer) * Rational(b_n, b_d)
    a_n, a_d = rational_parts(a_frac)

    if a_d == 1:
        a_style = "mixed"
    elif a_n > a_d:
        a_style = random.choice(["mixed", "improper"])
    else:
        a_style = "improper"

    return a_n, a_d, a_style, "÷", b_n, b_d, b_style, answer, 1


def generate_problem(max_whole=3, max_denom=6, operations=None):
    if operations is None:
        operations = ["×", "÷"]
    op = random.choice(operations)
    if op == "×":
        return generate_mul_problem(max_whole, max_denom)
    else:
        return generate_div_problem(max_whole, max_denom)


# ---------------------------------------------------------------------------
# PDF drawing
# ---------------------------------------------------------------------------

def draw_problem_row(c, x, y, prob, index, line_end_x=None, font_size=12):
    a_n, a_d, a_style, op, b_n, b_d, b_style = prob[:7]

    c.setFont(FONT_BOLD, font_size - 1)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT_BOLD, font_size - 1) + 6

    w1 = draw_mixed_or_improper(c, cx, y, a_n, a_d, a_style, font_size)
    cx += w1 + 10

    c.setFont(FONT, font_size)
    c.drawString(cx, y, op)
    cx += c.stringWidth(op, FONT, font_size) + 10

    w2 = draw_mixed_or_improper(c, cx, y, b_n, b_d, b_style, font_size)
    cx += w2 + 10

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


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def build_pdf(filename, num_problems=20, max_whole=3, max_denom=6,
              operations=None, title="Mnożenie i dzielenie ułamków", seed=None):
    if seed is not None:
        random.seed(seed)

    problems = [generate_problem(max_whole, max_denom, operations) for _ in range(num_problems)]

    sheet_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    width, height = LETTER
    c = canvas.Canvas(filename, pagesize=LETTER)
    margin_x = 0.75 * inch
    top_y = height - 0.75 * inch
    bottom_margin = 0.5 * inch

    answer_zone_h = 1.75 * inch
    cut_line_y = bottom_margin + answer_zone_h
    problems_start_y = top_y - 55
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
            ans_n, ans_d = prob[7], prob[8]
            col = i % ans_cols
            row = i // ans_cols
            ax = margin_x + col * ans_col_w
            ay = ans_top_y - row * ans_row_h
            draw_answer_value(c, ax, ay, ans_n, ans_d, global_idx, ans_font)

    c.save()
    return os.path.abspath(filename)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a PDF worksheet of fraction multiplication/division problems."
    )
    parser.add_argument("-n", "--num-problems", type=int, default=20,
                        help="Number of problems (default: 20)")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output PDF filename")
    parser.add_argument("--max-whole", type=int, default=3,
                        help="Maximum whole-number part (default: 3)")
    parser.add_argument("--max-denom", type=int, default=6,
                        help="Maximum denominator (default: 6)")
    parser.add_argument("--ops", type=str, default="x,/",
                        help="Comma-separated operations: x,/ (default: x,/)")
    parser.add_argument("--title", type=str,
                        default="Mnożenie i dzielenie ułamków",
                        help="Worksheet title")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    op_map = {"x": "×", "*": "×", "/": "÷"}
    operations = []
    for op in args.ops.split(","):
        op = op.strip()
        if op not in op_map:
            parser.error(f"Invalid operation: {op}. Use x or /.")
        operations.append(op_map[op])

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"muldiv_{ts}.pdf"

    path = build_pdf(
        filename=args.output,
        num_problems=args.num_problems,
        max_whole=args.max_whole,
        max_denom=args.max_denom,
        operations=operations,
        title=args.title,
        seed=args.seed,
    )
    print(f"Worksheet saved to: {path}")
    print(f"  {args.num_problems} problems  |  operations: {', '.join(operations)}")


if __name__ == "__main__":
    main()
