"""Common utilities for fraction worksheet generators.

Shared font registration, math helpers, and PDF drawing primitives.
"""

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sympy import Rational

_FONT_CANDIDATES = [
    # macOS
    ("/System/Library/Fonts/Supplemental/Arial.ttf",
     "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    # Linux — fonts-liberation (apt)
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    # Linux — fonts-liberation alternate path
    ("/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
     "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"),
]

import os as _os
_regular, _bold = next(
    (r, b) for r, b in _FONT_CANDIDATES if _os.path.exists(r)
)
pdfmetrics.registerFont(TTFont("Font", _regular))
pdfmetrics.registerFont(TTFont("Font-Bold", _bold))

FONT = "Font"
FONT_BOLD = "Font-Bold"


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def as_rational(n, d=1):
    """Return a normalized SymPy Rational."""
    return Rational(int(n), int(d))


def rational_parts(value):
    """Return (numerator, denominator) as builtin ints."""
    value = as_rational(value.p, value.q) if hasattr(value, "p") else as_rational(value)
    return int(value.p), int(value.q)


def simplify(n, d):
    numer, denom = rational_parts(as_rational(n, d))
    return numer, denom


def mixed_to_rational(whole, rem, denom):
    """Build a Rational from a mixed number."""
    whole = int(whole)
    rem = abs(int(rem))
    denom = int(denom)
    sign = -1 if whole < 0 else 1
    whole_abs = abs(whole)
    return as_rational(sign * (whole_abs * denom + rem), denom)


def to_mixed(n, d):
    """Return (whole, numerator_remainder, denominator)."""
    numer, denom = rational_parts(as_rational(n, d))
    if numer == 0:
        return 0, 0, 1
    negative = numer < 0
    numer = abs(numer)
    whole, rem = divmod(numer, denom)
    if negative and (whole or rem):
        whole = -whole if whole else 0
        if rem and whole == 0:
            rem = -rem
    return whole, rem, denom


# ---------------------------------------------------------------------------
# PDF drawing primitives
# ---------------------------------------------------------------------------

def draw_fraction(c, x, y, numer, denom, font_size=14):
    """Draw numerator / bar / denominator centred at (x, y). Returns width."""
    ns, ds = str(abs(numer)), str(denom)
    c.setFont(FONT, font_size)
    nw = c.stringWidth(ns, FONT, font_size)
    dw = c.stringWidth(ds, FONT, font_size)
    w = max(nw, dw) + 4
    bar_y = y + font_size * 0.15
    c.drawCentredString(x + w / 2, bar_y + 3, ns)
    c.line(x, bar_y, x + w, bar_y)
    c.drawCentredString(x + w / 2, bar_y - font_size + 1, ds)
    return w


def draw_mixed_or_improper(c, x, y, numer, denom, style, font_size=14):
    """Draw a number as mixed or improper fraction. Handles negatives and denom==1."""
    neg = numer < 0
    numer = abs(numer)
    total_w = 0

    if neg:
        c.setFont(FONT, font_size)
        c.drawString(x, y, "−")
        mw = c.stringWidth("−", FONT, font_size)
        x += mw + 2
        total_w += mw + 2

    if denom == 1:
        ws = str(numer)
        c.setFont(FONT, font_size)
        c.drawString(x, y, ws)
        return total_w + c.stringWidth(ws, FONT, font_size)

    if style == "mixed":
        whole, rem, d = to_mixed(numer, denom)
        whole, rem = abs(whole), abs(rem)
        if whole:
            ws = str(whole)
            c.setFont(FONT, font_size)
            c.drawString(x, y, ws)
            ww = c.stringWidth(ws, FONT, font_size)
            x += ww + 2
            total_w += ww + 2
        if rem:
            fw = draw_fraction(c, x, y, rem, d, font_size)
            total_w += fw
        elif not whole:
            c.setFont(FONT, font_size)
            c.drawString(x, y, "0")
            total_w += c.stringWidth("0", FONT, font_size)
    else:
        fw = draw_fraction(c, x, y, numer, denom, font_size)
        total_w += fw

    return total_w


def draw_answer_value(c, x, y, ans_n, ans_d, index, font_size=11):
    """Draw a single answer as whole, fraction, or mixed number."""
    c.setFont(FONT, font_size)
    label = f"{index}."
    c.drawString(x, y, label)
    cx = x + c.stringWidth(label, FONT, font_size) + 4

    whole, rem, d = to_mixed(ans_n, ans_d)
    if rem == 0:
        c.drawString(cx, y, str(whole))
    elif whole == 0:
        n, d = simplify(ans_n, ans_d)
        draw_fraction(c, cx, y, n, d, font_size)
    else:
        ws = str(whole)
        c.drawString(cx, y, ws)
        cx += c.stringWidth(ws, FONT, font_size) + 2
        draw_fraction(c, cx, y, abs(rem), d, font_size)


# ---------------------------------------------------------------------------
# Page furniture
# ---------------------------------------------------------------------------

def draw_cut_line(c, y, margin_x, page_width):
    """Draw a dashed cut line with scissors symbol."""
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setDash(6, 4)
    c.line(margin_x, y, page_width - margin_x, y)
    c.setDash()
    c.setStrokeColorRGB(0, 0, 0)
    c.setFont(FONT, 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(margin_x, y + 3, "✂")
    c.setFillColorRGB(0, 0, 0)


def draw_sheet_id(c, x, y, sheet_id):
    c.setFont(FONT, 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawRightString(x, y, f"ID: {sheet_id}")
    c.setFillColorRGB(0, 0, 0)
