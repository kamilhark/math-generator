#!/usr/bin/env python3
"""
Mixed Operations Fraction Worksheet Generator

Generates expressions combining +, −, ×, ÷ with parentheses.
Designed for 12-year-old students — small operands, clean answers.

Examples of generated problems:
    ( 1/2 + 1/3 ) × 6 = ___
    3 × ( 3/4 − 1/4 ) = ___
    ( 2/3 + 1/6 ) ÷ 1/2 = ___
"""

import argparse
import random
import os
import string
from fractions import Fraction
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from common import (
    FONT, FONT_BOLD, simplify, to_mixed,
    draw_fraction, draw_cut_line, draw_sheet_id, draw_answer_value,
)


# ---------------------------------------------------------------------------
# Operand pools — kept small for clean results
# ---------------------------------------------------------------------------

# Denominators 2, 3, 4, 6 all share LCD ≤ 12
FRAC_POOL = [
    Fraction(1, 2), Fraction(1, 3), Fraction(2, 3),
    Fraction(1, 4), Fraction(3, 4),
    Fraction(1, 6), Fraction(5, 6),
]

WHOLE_POOL = [Fraction(n) for n in range(2, 7)]

ALL_OPERANDS = FRAC_POOL + WHOLE_POOL

ADD_SUB = ["+", "−"]
MUL_DIV = ["×", "÷"]
ALL_OPS = ADD_SUB + MUL_DIV


# ---------------------------------------------------------------------------
# Expression helpers
# ---------------------------------------------------------------------------

def _apply(op, a, b):
    """Evaluate a single binary operation on two Fractions."""
    if op == "+":
        return a + b
    if op == "−":
        return a - b
    if op == "×":
        return a * b
    if op == "÷":
        return None if b == 0 else a / b
    return None


def _is_clean(result):
    """A result suitable for a 12-year-old: positive, small, simple denominator."""
    if result is None or result < 0:
        return False
    if result.denominator > 12 or abs(result.numerator) > 30:
        return False
    return True


def _pick_operands(count):
    """Pick *count* operands, guaranteeing at least one is a proper fraction."""
    ops = [random.choice(ALL_OPERANDS) for _ in range(count)]
    if not any(v.denominator > 1 for v in ops):
        ops[random.randrange(count)] = random.choice(FRAC_POOL)
    return ops


def _frac_token(f):
    return ("num", f.numerator, f.denominator)


# ---------------------------------------------------------------------------
# Problem generators (each returns (tokens, answer) or None)
# ---------------------------------------------------------------------------

def _gen_two_op():
    """Simple  a ○ b."""
    for _ in range(100):
        a, b = _pick_operands(2)
        op = random.choice(ALL_OPS)
        if op == "÷" and b == 0:
            continue
        result = _apply(op, a, b)
        if _is_clean(result) and result > 0:
            tokens = [_frac_token(a), ("op", op), _frac_token(b)]
            return tokens, result
    return None


def _gen_paren_left():
    """( a ⊕ b ) ⊗ c  — add/sub inside, mul/div outside."""
    for _ in range(200):
        a, b, c = _pick_operands(3)
        op_in = random.choice(ADD_SUB)
        op_out = random.choice(MUL_DIV)

        inner = _apply(op_in, a, b)
        if inner is None or inner <= 0:
            continue
        if op_out == "÷" and c == 0:
            continue
        result = _apply(op_out, inner, c)
        if _is_clean(result) and result > 0:
            tokens = [
                ("lparen",), _frac_token(a), ("op", op_in), _frac_token(b), ("rparen",),
                ("op", op_out), _frac_token(c),
            ]
            return tokens, result
    return None


def _gen_paren_right():
    """a ⊗ ( b ⊕ c )  — mul/div outside, add/sub inside."""
    for _ in range(200):
        a, b, c = _pick_operands(3)
        op_out = random.choice(MUL_DIV)
        op_in = random.choice(ADD_SUB)

        inner = _apply(op_in, b, c)
        if inner is None or inner <= 0:
            continue
        if op_out == "÷" and inner == 0:
            continue
        result = _apply(op_out, a, inner)
        if _is_clean(result) and result > 0:
            tokens = [
                _frac_token(a), ("op", op_out),
                ("lparen",), _frac_token(b), ("op", op_in), _frac_token(c), ("rparen",),
            ]
            return tokens, result
    return None


def _gen_no_paren():
    """a ○ b □ c  — no parentheses, mixed precedence (order-of-operations practice)."""
    for _ in range(200):
        a, b, c = _pick_operands(3)

        if random.random() < 0.5:
            op1, op2 = random.choice(ADD_SUB), random.choice(MUL_DIV)
        else:
            op1, op2 = random.choice(MUL_DIV), random.choice(ADD_SUB)

        if op1 in MUL_DIV:
            first = _apply(op1, a, b)
            if first is None:
                continue
            result = _apply(op2, first, c)
        elif op2 in MUL_DIV:
            second = _apply(op2, b, c)
            if second is None:
                continue
            result = _apply(op1, a, second)
        else:
            first = _apply(op1, a, b)
            if first is None:
                continue
            result = _apply(op2, first, c)

        if _is_clean(result) and result > 0:
            tokens = [
                _frac_token(a), ("op", op1),
                _frac_token(b), ("op", op2),
                _frac_token(c),
            ]
            return tokens, result
    return None


def generate_problem():
    """Return (tokens, answer_Fraction) for one problem."""
    generators = [
        (_gen_paren_left, 40),
        (_gen_paren_right, 40),
        (_gen_no_paren, 10),
        (_gen_two_op, 10),
    ]
    total = sum(w for _, w in generators)
    r = random.randint(1, total)
    cumul = 0
    for gen, w in generators:
        cumul += w
        if r <= cumul:
            result = gen()
            if result is not None:
                return result
            break

    for gen, _ in generators:
        result = gen()
        if result is not None:
            return result

    a = random.choice(FRAC_POOL)
    return [_frac_token(a), ("op", "+"), _frac_token(a)], a + a


# ---------------------------------------------------------------------------
# PDF drawing
# ---------------------------------------------------------------------------

def draw_expression(c, x, y, tokens, font_size=11):
    """Draw an expression from token list. Returns total width consumed."""
    cx = x
    paren_fs = int(font_size * 1.7)
    paren_y_offset = -font_size * 0.35
    gap = 5

    for tok in tokens:
        kind = tok[0]
        if kind == "lparen":
            c.setFont(FONT, paren_fs)
            c.drawString(cx, y + paren_y_offset, "(")
            cx += c.stringWidth("(", FONT, paren_fs) + 2
        elif kind == "rparen":
            c.setFont(FONT, paren_fs)
            c.drawString(cx, y + paren_y_offset, ")")
            cx += c.stringWidth(")", FONT, paren_fs) + gap
        elif kind == "num":
            numer, denom = tok[1], tok[2]
            if denom == 1:
                s = str(numer)
                c.setFont(FONT, font_size)
                c.drawString(cx, y, s)
                cx += c.stringWidth(s, FONT, font_size) + gap
            else:
                w = draw_fraction(c, cx, y, numer, denom, font_size)
                cx += w + gap
        elif kind == "op":
            c.setFont(FONT, font_size)
            c.drawString(cx, y, tok[1])
            cx += c.stringWidth(tok[1], FONT, font_size) + gap
    return cx - x


def draw_problem_row(c, x, y, problem, index, line_end_x=None, font_size=11):
    tokens, _answer = problem

    c.setFont(FONT_BOLD, font_size - 1)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT_BOLD, font_size - 1) + 6

    ew = draw_expression(c, cx, y, tokens, font_size)
    cx += ew + 4

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

def build_pdf(filename, num_problems=20,
              title="Działania na ułamkach z nawiasami", seed=None):
    if seed is not None:
        random.seed(seed)

    problems = [generate_problem() for _ in range(num_problems)]

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

    font_size = 11
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

        c.setFont(FONT_BOLD, 18)
        c.drawCentredString(width / 2, top_y, title)
        draw_sheet_id(c, width - margin_x, top_y + 2, sheet_id)

        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            px = margin_x
            py = problems_start_y - i * row_height
            draw_problem_row(c, px, py, prob, global_idx, width - margin_x, font_size)

        draw_cut_line(c, cut_line_y, margin_x, width)
        draw_sheet_id(c, width - margin_x, cut_line_y - 13, sheet_id)

        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            _tokens, answer = prob
            ans_n, ans_d = answer.numerator, answer.denominator
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
        description="Generate a PDF worksheet with mixed fraction operations and parentheses."
    )
    parser.add_argument("-n", "--num-problems", type=int, default=20,
                        help="Number of problems (default: 20)")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output PDF filename")
    parser.add_argument("--title", type=str,
                        default="Działania na ułamkach z nawiasami",
                        help="Worksheet title")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"mixed_ops_{ts}.pdf"

    path = build_pdf(
        filename=args.output,
        num_problems=args.num_problems,
        title=args.title,
        seed=args.seed,
    )
    print(f"Worksheet saved to: {path}")
    print(f"  {args.num_problems} mixed-operation problems with parentheses")


if __name__ == "__main__":
    main()
