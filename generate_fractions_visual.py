#!/usr/bin/env python3
"""
Fraction visual worksheet generator.

Three problem types:
  - Number line: letters on ticks between 0 and 1; find letter for a fraction or fraction for a letter.
  - Circle (pie): equal wedges, some shaded; write the fraction.
  - Subdivided rectangle: recursive binary splits, some regions shaded; write the fraction shaded.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import string
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from sympy import Rational

from common import FONT, FONT_BOLD, draw_cut_line, draw_fraction, draw_sheet_id, simplify

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NUMBER_LINE_DENOMS = (2, 3, 4, 5, 6, 8, 10)
LETTERS = string.ascii_uppercase  # A–Z

SHADE_GREY = (0.82, 0.82, 0.82)


# ---------------------------------------------------------------------------
# Problem generation
# ---------------------------------------------------------------------------


def generate_number_line_problem(max_denom: int = 10) -> dict:
    """Return a dict describing one number-line problem (0..1, ticks at 1/denom)."""
    allowed = [d for d in NUMBER_LINE_DENOMS if d <= max_denom]
    denom = random.choice(allowed)
    # Interior ticks only: indices 1 .. denom-1
    target_idx = random.randint(1, denom - 1)
    numer, d = simplify(target_idx, denom)
    letter = LETTERS[target_idx - 1]
    # Alternate directions across worksheet by index in caller; here random for variety
    return {
        "kind": "number_line",
        "denom": denom,
        "target_idx": target_idx,
        "numer": numer,
        "denom_ans": d,
        "letter": letter,
    }


def generate_circle_problem(max_denom: int = 8) -> dict:
    """Pie chart: equal sectors, random contiguous shaded arc from the top, clockwise."""
    denom = random.randint(2, max_denom)
    shaded = random.randint(1, denom - 1)
    numer, d = simplify(shaded, denom)
    return {
        "kind": "circle",
        "denom": denom,
        "shaded": shaded,
        "numer": numer,
        "denom_ans": d,
    }


def _split_cell(
    x: float,
    y: float,
    w: float,
    h: float,
    depth: int,
    max_depth: int,
) -> List[Tuple[float, float, float, float]]:
    """Recursively split rectangle (binary halving). Returns leaf cells (x,y,w,h) in unit square."""
    if depth >= max_depth:
        return [(x, y, w, h)]
    # Force at least one split at root; then probabilistic deeper splits
    if depth == 0 or random.random() < 0.55:
        vertical = w >= h
        if vertical:
            w2 = w / 2.0
            left = _split_cell(x, y, w2, h, depth + 1, max_depth)
            right = _split_cell(x + w2, y, w2, h, depth + 1, max_depth)
            return left + right
        h2 = h / 2.0
        bottom = _split_cell(x, y, w, h2, depth + 1, max_depth)
        top = _split_cell(x, y + h2, w, h2, depth + 1, max_depth)
        return bottom + top
    return [(x, y, w, h)]


def _dyadic_area_frac(w: float, h: float) -> Rational:
    """Area w*h when w,h are (sums of) powers of 1/2 from binary splitting."""
    a = w * h
    if a <= 0:
        return Rational(0, 1)
    for n in range(0, 28):
        den = 2**n
        num = round(a * den)
        if abs(num / den - a) < 1e-9:
            return Rational(num, den)
    return Rational(str(a))


def generate_bar_problem(max_depth: int = 3) -> dict:
    """Rectangle recursively halved; random subset of leaf cells shaded."""
    md = max(1, max_depth)
    cells = _split_cell(0.0, 0.0, 1.0, 1.0, 0, md)
    if len(cells) < 2:
        cells = _split_cell(0.0, 0.0, 1.0, 1.0, 0, max(md, 2))

    n = len(cells)
    k = random.randint(1, n - 1)
    shaded_idx = set(random.sample(range(n), k))

    shaded_frac = sum(
        _dyadic_area_frac(w, h) for (x, y, w, h) in [cells[i] for i in shaded_idx]
    )
    numer, denom = simplify(shaded_frac.p, shaded_frac.q)

    return {
        "kind": "bar",
        "cells": cells,
        "shaded_idx": shaded_idx,
        "numer": numer,
        "denom_ans": denom,
    }


def _pick_problem_types(
    num_problems: int,
    problem_types: Optional[Sequence[str]],
) -> List[str]:
    pool = list(problem_types) if problem_types else ["number_line", "circle", "bar"]
    if not pool:
        pool = ["number_line", "circle", "bar"]
    # Alternate directions for number_line when we generate them
    out: List[str] = []
    for i in range(num_problems):
        out.append(random.choice(pool))
    return out


def _make_problem(kind: str, max_denom_nl: int, max_denom_circle: int, max_depth_bar: int) -> dict:
    if kind == "number_line":
        return generate_number_line_problem(max_denom_nl)
    if kind == "circle":
        return generate_circle_problem(max_denom_circle)
    if kind == "bar":
        return generate_bar_problem(max_depth_bar)
    raise ValueError(f"unknown problem kind: {kind}")


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------


def draw_number_line(
    c: canvas.Canvas,
    x: float,
    y_axis: float,
    width: float,
    prob: dict,
    font_size: int = 9,
) -> None:
    """Horizontal axis 0–1 with ticks and letters on interior ticks."""
    denom = prob["denom"]
    tick_spacing = width / denom

    # Main line + arrow hint past 1
    arrow_extra = 8
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8)
    c.line(x, y_axis, x + width + arrow_extra, y_axis)
    # small arrowhead
    ax = x + width + arrow_extra
    c.line(ax, y_axis, ax - 4, y_axis + 3)
    c.line(ax, y_axis, ax - 4, y_axis - 3)

    tick_h_small = 5
    tick_h_big = 8

    for i in range(denom + 1):
        tx = x + i * tick_spacing
        is_whole = i == 0 or i == denom
        th = tick_h_big if is_whole else tick_h_small
        c.line(tx, y_axis, tx, y_axis + th)

        if is_whole:
            c.setFont(FONT_BOLD, font_size)
            label = "0" if i == 0 else "1"
            c.drawCentredString(tx, y_axis - 14, label)
        else:
            c.setFont(FONT_BOLD, font_size + 1)
            letter = LETTERS[i - 1]
            c.setFillColorRGB(0.1, 0.35, 0.75)
            c.drawCentredString(tx, y_axis + th + 4, letter)
            c.setFillColorRGB(0, 0, 0)

    c.setFont(FONT, font_size)


def draw_circle_diagram(
    c: canvas.Canvas,
    cx: float,
    cy: float,
    radius: float,
    prob: dict,
) -> None:
    """Pie: wedges from top, clockwise; first `shaded` sectors filled grey."""
    denom = prob["denom"]
    shaded = prob["shaded"]
    start0 = 90.0
    step = 360.0 / denom

    for i in range(denom):
        a0 = start0 - i * step
        a1 = start0 - (i + 1) * step
        extent = a1 - a0
        x0, y0 = cx - radius, cy - radius
        x1, y1 = cx + radius, cy + radius
        if i < shaded:
            c.setFillColorRGB(*SHADE_GREY)
            c.wedge(x0, y0, x1, y1, a0, extent, stroke=0, fill=1)
        else:
            c.setFillColorRGB(1, 1, 1)
            c.wedge(x0, y0, x1, y1, a0, extent, stroke=0, fill=1)

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8)
    c.circle(cx, cy, radius, stroke=1, fill=0)


def draw_bar_diagram(
    c: canvas.Canvas,
    x: float,
    y_bottom: float,
    draw_w: float,
    draw_h: float,
    prob: dict,
) -> None:
    """Shaded rectangles from normalized cell list."""
    cells = prob["cells"]
    shaded = prob["shaded_idx"]

    c.setLineWidth(0.6)
    for i, (nx, ny, nw, nh) in enumerate(cells):
        px = x + nx * draw_w
        py = y_bottom + ny * draw_h
        pw = nw * draw_w
        ph = nh * draw_h
        if i in shaded:
            c.setFillColorRGB(*SHADE_GREY)
            c.rect(px, py, pw, ph, stroke=0, fill=1)
        else:
            c.setFillColorRGB(1, 1, 1)
            c.rect(px, py, pw, ph, stroke=0, fill=1)
        c.setStrokeColorRGB(0, 0, 0)
        c.rect(px, py, pw, ph, stroke=1, fill=0)
    c.setFillColorRGB(0, 0, 0)


def _draw_eq_blank(c: canvas.Canvas, x: float, y: float, blank_w: float, font_size: int) -> float:
    c.setFont(FONT, font_size)
    eq_w = c.stringWidth(" = ", FONT, font_size)
    c.drawString(x, y, " = ")
    bx = x + eq_w
    c.setStrokeColorRGB(0.65, 0.65, 0.65)
    c.setDash(2, 2)
    c.line(bx, y - 3, bx + blank_w, y - 3)
    c.setDash()
    c.setStrokeColorRGB(0, 0, 0)
    return eq_w + blank_w + 4


def draw_problem_block(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    col_width: float,
    prob: dict,
    index: int,
    font_size: int = 11,
) -> None:
    """Draw one problem: number + diagram + prompt + blank."""
    c.setFont(FONT_BOLD, font_size)
    label = f"{index}."
    c.drawString(x, y_top - 2, label)
    lx = x + c.stringWidth(label, FONT_BOLD, font_size) + 6

    kind = prob["kind"]
    small_fs = max(font_size - 1, 9)

    if kind == "number_line":
        # Layout (top → bottom): problem label, letter space, axis tick, integer labels, gap, question
        # axis sits 36 pt below y_top so letters comfortably clear the "1." label
        axis_y = y_top - 36
        line_w = col_width - 8
        draw_number_line(c, x, axis_y, line_w, prob, font_size=9)
        # "0"/"1" integer labels: baseline at axis_y - 14, text body top ~axis_y - 7
        # Leave 14 pt gap below that text body before the question text baseline
        qy = axis_y - 14 - small_fs - 14  # = axis_y - (14 + small_fs + 14)

        c.setFont(FONT, small_fs)
        if prob["direction"] == "find_letter":
            c.drawString(lx, qy, "Która litera oznacza ułamek")
            cx = lx + c.stringWidth("Która litera oznacza ułamek ", FONT, small_fs) + 4
            fw = draw_fraction(c, cx, qy, prob["numer"], prob["denom_ans"], small_fs)
            cx += fw + 6
            _draw_eq_blank(c, cx, qy, 28, small_fs)
        else:
            c.drawString(lx, qy, "Jaki ułamek oznacza litera ")
            cx = lx + c.stringWidth("Jaki ułamek oznacza litera ", FONT, small_fs)
            c.setFont(FONT_BOLD, small_fs)
            c.drawString(cx, qy, prob["letter"])
            cx += c.stringWidth(prob["letter"], FONT_BOLD, small_fs) + 4
            c.setFont(FONT, small_fs)
            _draw_eq_blank(c, cx, qy, 40, small_fs)

    elif kind == "circle":
        r = min(30.0, col_width / 5)
        cx = x + col_width / 2
        cy = y_top - 8 - r
        draw_circle_diagram(c, cx, cy, r, prob)
        qy = y_top - 16 - 2 * r - 6
        c.setFillColorRGB(0, 0, 0)
        c.setFont(FONT, small_fs)
        c.drawCentredString(x + col_width / 2, qy, "Jaki ułamek obrazuje zakreskowany fragment koła?")
        c.setFont(FONT, small_fs)
        tw = c.stringWidth(" = ", FONT, small_fs)
        bx = x + col_width / 2 - (tw + 50) / 2
        _draw_eq_blank(c, bx, qy - 16, 44, small_fs)

    else:  # bar
        bh = 44.0
        bw = min(col_width - 20, 200.0)
        bx0 = x + (col_width - bw) / 2
        y_bottom = y_top - 8 - bh
        draw_bar_diagram(c, bx0, y_bottom, bw, bh, prob)
        qy = y_bottom - 18
        c.setFillColorRGB(0, 0, 0)
        c.setFont(FONT, small_fs)
        c.drawCentredString(
            x + col_width / 2,
            qy,
            "Jaki ułamek powierzchni prostokąta jest zakreskowany?",
        )
        tw = c.stringWidth(" = ", FONT, small_fs)
        bx = x + col_width / 2 - (tw + 50) / 2
        _draw_eq_blank(c, bx, qy - 16, 44, small_fs)


def draw_answer_block(
    c: canvas.Canvas,
    x: float,
    y: float,
    prob: dict,
    index: int,
    font_size: int = 10,
) -> None:
    """Compact answer line for key below cut line."""
    c.setFont(FONT, font_size)
    lab = f"{index}."
    c.drawString(x, y, lab)
    ax = x + c.stringWidth(lab, FONT, font_size) + 4

    if prob["kind"] == "number_line":
        if prob["direction"] == "find_letter":
            c.setFont(FONT_BOLD, font_size)
            c.drawString(ax, y, prob["letter"])
        else:
            draw_fraction(c, ax, y, prob["numer"], prob["denom_ans"], font_size)
    else:
        draw_fraction(c, ax, y, prob["numer"], prob["denom_ans"], font_size)


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------


def build_pdf(
    filename: str,
    num_problems: int = 20,
    title: str = "Ułamki – oś liczbowa i diagramy",
    problem_types: Optional[Sequence[str]] = None,
    max_denom_number_line: int = 10,
    max_denom_circle: int = 8,
    max_depth_bar: int = 3,
    seed: Optional[int] = None,
) -> str:
    if seed is not None:
        random.seed(seed)

    kinds = _pick_problem_types(num_problems, problem_types)
    problems: List[dict] = []
    for i, k in enumerate(kinds):
        p = _make_problem(k, max_denom_number_line, max_denom_circle, max_depth_bar)
        # Alternate number-line question direction for variety
        if p["kind"] == "number_line":
            p["direction"] = "find_letter" if i % 2 == 0 else "find_fraction"
        problems.append(p)

    sheet_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    width, height = LETTER
    c = canvas.Canvas(filename, pagesize=LETTER)
    margin_x = 0.75 * inch
    top_y = height - 0.75 * inch
    bottom_margin = 0.5 * inch

    answer_zone_h = 1.75 * inch
    cut_line_y = bottom_margin + answer_zone_h
    problems_start_y = top_y - 60
    problems_end_y = cut_line_y + 20

    font_size = 11
    col_width = (width - 2 * margin_x) / 2
    row_height = 115
    usable = problems_start_y - problems_end_y
    rows_per_col = max(1, int(usable // row_height))
    page_capacity = rows_per_col * 2

    ans_font = 10
    ans_row_h = 26
    ans_cols = 5
    ans_col_w = (width - 2 * margin_x) / ans_cols
    ans_top_y = cut_line_y - 22

    page_problems: List[List[dict]] = []
    for i in range(0, num_problems, page_capacity):
        page_problems.append(problems[i : i + page_capacity])

    for page_idx, page_probs in enumerate(page_problems):
        if page_idx > 0:
            c.showPage()

        c.setFont(FONT_BOLD, 18)
        c.drawCentredString(width / 2, top_y, title)
        draw_sheet_id(c, width - margin_x, top_y + 2, sheet_id)

        per_col = math.ceil(len(page_probs) / 2)
        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            col = 0 if i < per_col else 1
            row = i if col == 0 else i - per_col
            px = margin_x + col * col_width
            py = problems_start_y - row * row_height
            draw_problem_block(c, px, py, col_width, prob, global_idx, font_size)

        draw_cut_line(c, cut_line_y, margin_x, width)
        draw_sheet_id(c, width - margin_x, cut_line_y - 13, sheet_id)

        for i, prob in enumerate(page_probs):
            global_idx = sum(len(pp) for pp in page_problems[:page_idx]) + i + 1
            ac = (i % ans_cols)
            ar = i // ans_cols
            ax = margin_x + ac * ans_col_w
            ay = ans_top_y - ar * ans_row_h
            draw_answer_block(c, ax, ay, prob, global_idx, ans_font)

    c.save()
    return os.path.abspath(filename)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

VALID_TYPES = ("number_line", "circle", "bar")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a PDF worksheet: fractions on a number line, pie charts, subdivided rectangles.",
    )
    parser.add_argument(
        "-n",
        "--count",
        "--num-problems",
        type=int,
        default=20,
        dest="count",
        help="Number of problems (default: 20)",
    )
    parser.add_argument("-o", "--output", type=str, default=None, help="Output PDF path")
    parser.add_argument("--title", type=str, default="Ułamki – oś liczbowa i diagramy", help="Worksheet title")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument(
        "--type",
        action="append",
        dest="types",
        default=None,
        metavar="KIND",
        help=f"Problem kind to include (repeatable): {', '.join(VALID_TYPES)}. Default: all mixed.",
    )
    parser.add_argument("--max-denom-number-line", type=int, default=10, help="Max denominator on number line")
    parser.add_argument("--max-denom-circle", type=int, default=8, help="Max pie sectors")
    parser.add_argument("--max-depth-bar", type=int, default=3, help="Max recursion depth for rectangle splits")

    args = parser.parse_args()

    types: Optional[List[str]] = None
    if args.types:
        types = []
        for t in args.types:
            for part in t.split(","):
                part = part.strip()
                if not part:
                    continue
                if part not in VALID_TYPES:
                    parser.error(f"unknown --type {part!r}; use: {', '.join(VALID_TYPES)}")
                types.append(part)
        if not types:
            types = None

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"fractions_visual_{ts}.pdf"

    path = build_pdf(
        filename=args.output,
        num_problems=args.count,
        title=args.title,
        problem_types=types,
        max_denom_number_line=args.max_denom_number_line,
        max_denom_circle=args.max_denom_circle,
        max_depth_bar=args.max_depth_bar,
        seed=args.seed,
    )
    print(f"Worksheet saved to: {path}")
    print(f"  {args.count} problems")


if __name__ == "__main__":
    main()
