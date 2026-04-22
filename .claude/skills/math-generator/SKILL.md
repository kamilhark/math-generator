---
name: math-generator
description: Create a new math worksheet generator for this project. Use this skill whenever the user wants to add a new type of math problem, worksheet, exercise, or generator — even if they say "add a generator", or describe a math concept they want worksheets for. This project generates Polish math worksheets for 12-year-olds as PDFs.
---

# Math Generator Skill

This project generates printable Polish math worksheets (PDF) for 12-year-old students. Each generator lives in `generate_<type>.py` and follows a strict 4-part pattern. Follow it exactly.
Make sure any new generator is suitable for 12-year-old kid, the difficulty of the tasks need to be adjusted to that age. 
Ensure the answers are also not too complicated, avoid big numbers.

## Project conventions

**File naming**: `generate_<type>.py` — use lowercase, underscores (e.g. `generate_powers.py`)

**Standard imports:**
```python
#!/usr/bin/env python3
import argparse, random, os, string
from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from sympy import Rational

from common import (
    FONT, FONT_BOLD,
    draw_fraction, draw_mixed_or_improper, draw_cut_line,
    draw_sheet_id, draw_answer_value, simplify, rational_parts
)
```

Only import from `common` what you actually use.

**Layout constants** (use these verbatim unless the generator needs something special):
```python
PAGE_W, PAGE_H = LETTER          # 612 × 792 points
MARGIN_X       = 0.75 * inch
MARGIN_Y_TOP   = 0.5 * inch
ANSWER_ZONE    = 1.75 * inch     # space below cut line for answer key
ROW_H          = 44              # points between problem rows (adjust for tall content)
FONT_SIZE      = 12              # problems
ANS_FONT_SIZE  = 9               # answer key
```

## The 4-part pattern

Every generator has exactly these four sections, in order.

### Part 1 — Problem generation

```python
def generate_problem(...) -> tuple:
    """Return all data needed to draw one problem and its answer."""
    # Use sympy.Rational for arithmetic — never float
    # Return a tuple: all display parts + answer parts
    # For subtraction, ensure non-negative results (swap if needed)
```

Helper functions (e.g. `random_fraction()`) go above `generate_problem`.

### Part 2 — PDF drawing

```python
def draw_problem(c, x, y, prob, index, font_size=FONT_SIZE):
    """Draw one problem on the worksheet."""
    # c is a reportlab Canvas
    # (x, y) is the baseline position
    # prob is the tuple from generate_problem()
    # index is the 1-based problem number

def draw_answer(c, x, y, prob, index, font_size=ANS_FONT_SIZE):
    """Draw the answer below the cut line."""
    # If common.draw_answer_value() fits, prefer it
```

For fractions, use `common.draw_fraction()` and `common.draw_mixed_or_improper()`.
For plain text/numbers, use `c.drawString()` with the registered `FONT` / `FONT_BOLD`.

### Part 3 — PDF builder

```python
def build_pdf(filename, num_problems=20, ..., title="Polish title here", seed=None):
    """Build the worksheet PDF. Returns absolute path."""
    if seed is not None:
        random.seed(seed)

    sheet_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    problems = [generate_problem(...) for _ in range(num_problems)]

    c = canvas.Canvas(filename, pagesize=LETTER)
    usable_h = PAGE_H - MARGIN_Y_TOP*2 - ANSWER_ZONE
    per_page = int(usable_h // ROW_H)

    for page_idx in range(0, num_problems, per_page):
        if page_idx > 0:
            c.showPage()
        page_probs = problems[page_idx : page_idx + per_page]

        # --- header ---
        y = PAGE_H - MARGIN_Y_TOP
        c.setFont(FONT_BOLD, 14)
        c.drawString(MARGIN_X, y, title)
        draw_sheet_id(c, PAGE_W - MARGIN_X - 60, y, sheet_id)
        y -= 28

        # --- problems ---
        for i, prob in enumerate(page_probs):
            draw_problem(c, MARGIN_X, y, prob, page_idx + i + 1)
            y -= ROW_H

        # --- cut line + answers ---
        cut_y = MARGIN_Y_TOP + ANSWER_ZONE
        draw_cut_line(c, cut_y, MARGIN_X, PAGE_W)
        ans_y = cut_y - 18
        for i, prob in enumerate(page_probs):
            draw_answer(c, MARGIN_X + (i % 5) * 110, ans_y - (i // 5) * 18,
                        prob, page_idx + i + 1)
        draw_sheet_id(c, MARGIN_X, MARGIN_Y_TOP, sheet_id)

    c.save()
    return os.path.abspath(filename)
```

Adjust the answer layout (5-per-row is a default) to fit the answer size.

### Part 4 — CLI

```python
def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p = argparse.ArgumentParser()
    p.add_argument("-n", "--num-problems", type=int, default=20)
    p.add_argument("-o", "--output", default=f"worksheet_{ts}.pdf")
    p.add_argument("--title", default="Default Polish Title")
    p.add_argument("--seed", type=int)
    # Add generator-specific args here
    args = p.parse_args()
    path = build_pdf(args.output, args.num_problems, ..., args.title, args.seed)
    print(f"Saved: {path}")

if __name__ == "__main__":
    main()
```

## Registering in app.py

After creating the generator file, add it to `app.py` in **two places**:

1. **`CATEGORIES` dict** — pick the right top-level category or add one:
```python
CATEGORIES = {
    "🔢  Ułamki zwykłe": { ... },
    "🔟  Ułamki dziesiętne": { ... },
    # add new category here if needed
}
```

2. **`build_pdf_bytes()` dispatch** — add an `elif` branch:
```python
elif kind == "my_new_type":
    from generate_my_new_type import build_pdf
    build_pdf(tmp.name, n, ..., title=title, seed=seed)
```

## Polish titles

Use Polish for default worksheet titles. Examples from the project:
- "Dodawanie i odejmowanie ułamków"
- "Mnożenie i dzielenie ułamków"
- "Porównywanie ułamków"

Ask the user for a Polish title or translate the concept if unsure.

## Checklist before finishing

- [ ] File named `generate_<type>.py`
- [ ] All 4 parts present in order
- [ ] SymPy used for all arithmetic (no floats)
- [ ] `seed` parameter wired through to `random.seed()`
- [ ] `sheet_id` generated and drawn on both header and answer zone
- [ ] `draw_cut_line` called
- [ ] Registered in `app.py` (both `CATEGORIES` and `build_pdf_bytes`)
- [ ] Default Polish title set
