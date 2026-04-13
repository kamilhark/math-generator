#!/usr/bin/env python3
"""
Decimal Fraction ↔ Fraction Conversion Worksheet Generator
Supports 6 difficulty levels: A, B, C, D, E, MISTRZ
"""

import argparse
import math
import random
import os
import string
from collections import namedtuple
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from common import (
    FONT, FONT_BOLD,
    draw_fraction, draw_cut_line, draw_sheet_id, simplify,
)

# ---------------------------------------------------------------------------
# Problem representation
# ---------------------------------------------------------------------------

Problem = namedtuple('Problem', [
    'direction',  # 'to_decimal' or 'to_fraction'
    'whole',      # integer part (0 for proper fractions)
    'disp_n',     # numerator to display (may be unsimplified for E/MISTRZ)
    'disp_d',     # denominator to display (may be unsimplified)
    'ans_n',      # simplified numerator (for answer key)
    'ans_d',      # simplified denominator (for answer key)
    'dec_str',    # decimal string with Polish comma, e.g. "2,75"
])

LEVELS = ['A', 'B', 'C', 'D', 'E', 'MISTRZ']

# For levels A/B/C: power-of-10 denominators, fraction always simplified.
# For levels D/E/MISTRZ: specific non-power-of-10 denominators.
# simplified=True → numerator must be coprime with denominator.
# whole_max=0 → no whole part; whole_min starts at 1 for C (always mixed number).
LEVEL_CONFIGS = {
    'A':      {'gen': 'power10', 'denoms': [10, 100],              'whole_min': 0, 'whole_max': 0,   'simplified': True},
    'B':      {'gen': 'power10', 'denoms': [10, 100, 1000, 10000], 'whole_min': 0, 'whole_max': 0,   'simplified': True},
    'C':      {'gen': 'power10', 'denoms': [10, 100, 1000],        'whole_min': 1, 'whole_max': 123, 'simplified': True},
    'D':      {'gen': 'simple',  'denoms': [2, 4, 5],              'whole_min': 0, 'whole_max': 12,  'simplified': True},
    'E':      {'gen': 'simple',  'denoms': [8, 20, 25, 50, 500],   'whole_min': 0, 'whole_max': 39,  'simplified': False},
    'MISTRZ': {'gen': 'simple',  'denoms': [12, 40, 125],          'whole_min': 0, 'whole_max': 89,  'simplified': False},
}

# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def _count_factor(n, p):
    count = 0
    while n % p == 0:
        n //= p
        count += 1
    return count


def _is_terminating(denom):
    """True if denom only has factors 2 and 5."""
    denom = abs(denom)
    while denom % 2 == 0:
        denom //= 2
    while denom % 5 == 0:
        denom //= 5
    return denom == 1


def _decimal_places(denom):
    """Number of decimal places needed for denom = 2^a * 5^b."""
    return max(_count_factor(denom, 2), _count_factor(denom, 5))


def _terminating_decimal_str(whole, numer, denom):
    """Format whole + numer/denom as a Polish decimal string (comma separator).

    denom must only have factors 2 and 5 (caller's responsibility).
    """
    places = _decimal_places(denom)
    multiplier = (10 ** places) // denom
    frac_str = str(numer * multiplier).zfill(places)
    return f"{whole},{frac_str}"


def _valid_numerators(denom, simplified_only):
    """Return numerators n in [1, denom-1] such that n/denom is a terminating decimal.

    If simplified_only, restricts to numerators coprime with denom.
    """
    result = []
    for n in range(1, denom):
        _, s_d = simplify(n, denom)
        if not _is_terminating(s_d):
            continue
        if simplified_only and math.gcd(n, denom) != 1:
            continue
        result.append(n)
    return result


# ---------------------------------------------------------------------------
# Problem generators
# ---------------------------------------------------------------------------

def _gen_power10_problem(cfg):
    """Levels A, B, C: power-of-10 denominator, always simplified."""
    denom = random.choice(cfg['denoms'])

    # Numerator coprime with denom (no factor of 2 or 5) → already simplified
    while True:
        numer = random.randint(1, denom - 1)
        if numer % 2 != 0 and numer % 5 != 0:
            break

    whole = random.randint(cfg['whole_min'], cfg['whole_max']) if cfg['whole_max'] > 0 else 0
    dec_str = _terminating_decimal_str(whole, numer, denom)
    direction = random.choice(['to_decimal', 'to_fraction'])

    return Problem(direction, whole, numer, denom, numer, denom, dec_str)


def _gen_simple_problem(cfg):
    """Levels D, E, MISTRZ: non-power-of-10 denominator, optionally unsimplified."""
    denom = random.choice(cfg['denoms'])
    valid = _valid_numerators(denom, cfg['simplified'])
    numer = random.choice(valid)

    ans_n, ans_d = simplify(numer, denom)
    whole = random.randint(cfg['whole_min'], cfg['whole_max'])
    dec_str = _terminating_decimal_str(whole, ans_n, ans_d)
    direction = random.choice(['to_decimal', 'to_fraction'])

    return Problem(direction, whole, numer, denom, ans_n, ans_d, dec_str)


def generate_problem(level='A'):
    """Return a Problem for the given difficulty level."""
    cfg = LEVEL_CONFIGS[level]
    if cfg['gen'] == 'power10':
        return _gen_power10_problem(cfg)
    return _gen_simple_problem(cfg)


# ---------------------------------------------------------------------------
# PDF drawing
# ---------------------------------------------------------------------------

def _draw_mixed_frac(c, x, y, whole, numer, denom, font_size):
    """Draw 'whole numer/denom' (or just numer/denom if whole==0). Returns width used."""
    total_w = 0
    if whole:
        ws = str(whole)
        c.setFont(FONT, font_size)
        c.drawString(x, y, ws)
        ww = c.stringWidth(ws, FONT, font_size)
        x += ww + 3
        total_w += ww + 3
    total_w += draw_fraction(c, x, y, numer, denom, font_size)
    return total_w


def draw_problem_row(c, x, y, prob, index, line_end_x=None, font_size=12):
    c.setFont(FONT_BOLD, font_size - 1)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT_BOLD, font_size - 1) + 6

    c.setFont(FONT, font_size)
    if prob.direction == 'to_fraction':
        c.drawString(cx, y, prob.dec_str)
        cx += c.stringWidth(prob.dec_str, FONT, font_size) + 10
    else:
        cx += _draw_mixed_frac(c, cx, y, prob.whole, prob.disp_n, prob.disp_d, font_size) + 10

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
    c.setFont(FONT, font_size)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT, font_size) + 4

    if prob.direction == 'to_fraction':
        if prob.whole:
            ws = str(prob.whole)
            c.drawString(cx, y, ws)
            cx += c.stringWidth(ws, FONT, font_size) + 2
        draw_fraction(c, cx, y, prob.ans_n, prob.ans_d, font_size)
    else:
        c.drawString(cx, y, prob.dec_str)


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def build_pdf(filename, num_problems=20, level='A',
              title="Ułamki dziesiętne – zamiana", seed=None):
    if seed is not None:
        random.seed(seed)

    problems = [generate_problem(level) for _ in range(num_problems)]
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

    ans_font = 9
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

        c.setFont(FONT_BOLD, 18)
        c.drawCentredString(width / 2, top_y, title)
        draw_sheet_id(c, width - margin_x, top_y + 2, sheet_id)

        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            py = problems_start_y - i * row_height
            draw_problem_row(c, margin_x, py, prob, global_idx, width - margin_x, font_size)

        draw_cut_line(c, cut_line_y, margin_x, width)
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
                    "decimal fractions and common fractions."
    )
    parser.add_argument("-n", "--num-problems", type=int, default=20,
                        help="Number of problems (default: 20)")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output PDF filename")
    parser.add_argument("--level", type=str, default='A', choices=LEVELS,
                        help="Difficulty level: A, B, C, D, E, MISTRZ (default: A)")
    parser.add_argument("--title", type=str,
                        default="Ułamki dziesiętne – zamiana",
                        help="Worksheet title")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"decimal_convert_{ts}.pdf"

    path = build_pdf(
        filename=args.output,
        num_problems=args.num_problems,
        level=args.level,
        title=args.title,
        seed=args.seed,
    )
    print(f"Worksheet saved to: {path}")
    print(f"  {args.num_problems} problems, level {args.level}")


if __name__ == "__main__":
    main()
