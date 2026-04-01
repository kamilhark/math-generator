# Generator Zadań Matematycznych

Generates printable PDF worksheets with fraction problems for 12-year-old students. Each worksheet includes a cut-off answer key at the bottom of the page.

Six types of worksheets are available:

| Generator | Description |
|---|---|
| `generate_addsub.py` | Addition & subtraction of mixed numbers and improper fractions |
| `generate_muldiv.py` | Multiplication & division of mixed numbers and improper fractions |
| `generate_convert.py` | Converting between improper fractions and mixed numbers |
| `generate_mixed_ops.py` | Mixed operations with parentheses (order-of-operations practice) |
| `generate_fractions_visual.py` | Fractions on a number line (letters), pie charts, subdivided rectangles |
| `generate_equiv.py` | Equivalent fractions — fill in the missing numerator or denominator |
| `generate_compare.py` | Fraction comparison — place <, =, or > between two fractions |

## Setup

```bash
pip install -r requirements.txt
```

## Web App

The easiest way to use the generators is via the Streamlit web app:

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser. Select a worksheet type, choose the number of problems (up to 20), and click **Generuj i pobierz arkusz** to download a ready-to-print PDF.

## Command-line Usage

Each generator can also be run directly from the command line.

```bash
# Addition & subtraction
python generate_addsub.py -n 20 -o worksheet.pdf

# Multiplication & division
python generate_muldiv.py -n 20 -o worksheet.pdf

# Improper ↔ mixed conversion
python generate_convert.py -n 20 -o worksheet.pdf

# Mixed operations with parentheses
python generate_mixed_ops.py -n 20 -o worksheet.pdf

# Visual fraction tasks (number line, pie, subdivided rectangle)
python generate_fractions_visual.py -n 20 -o worksheet.pdf

# Equivalent fractions — fill in the missing number
python generate_equiv.py -n 20 -o worksheet.pdf

# Fraction comparison — place <, =, or >
python generate_compare.py -n 20 -o worksheet.pdf
```

### Common options (all generators)

| Flag | Default | Description |
|---|---|---|
| `-n` / `--num-problems` | 20 | Number of problems |
| `-o` / `--output` | `<name>_<timestamp>.pdf` | Output filename |
| `--title` | *(Polish title)* | Title printed on the worksheet |
| `--seed` | *(random)* | Random seed for reproducibility |

### `generate_addsub.py` / `generate_muldiv.py`

| Flag | Default | Description |
|---|---|---|
| `--max-whole` | 4 / 3 | Largest whole-number part |
| `--max-denom` | 8 / 6 | Largest denominator |
| `--ops` | `+,-` / `x,/` | Operations to include |

### `generate_convert.py`

| Flag | Default | Description |
|---|---|---|
| `--max-whole` | 5 | Largest whole-number part |
| `--max-denom` | 10 | Largest denominator |

### `generate_fractions_visual.py`

| Flag | Default | Description |
|---|---|---|
| `-n` / `--count` | 20 | Number of problems |
| `--type` | *(repeatable)* | `number_line`, `circle`, or `bar` (omit for a random mix) |
| `--max-denom-number-line` | 10 | Largest tick spacing denominator on the axis |
| `--max-denom-circle` | 8 | Largest number of pie sectors |
| `--max-depth-bar` | 3 | Deepest binary split depth for rectangles |

### `generate_equiv.py`

| Flag | Default | Description |
|---|---|---|
| `--max-denom` | 9 | Largest denominator of the base fraction |
| `--max-mult` | 12 | Largest multiplier used to build the equivalent fraction |

### `generate_compare.py`

| Flag | Default | Description |
|---|---|---|
| `--max-denom` | 12 | Largest denominator |
| `--types` | *(all)* | Comma-separated subset of: `same_denom`, `same_numer`, `different`, `equal` |

## Dependencies

- [ReportLab](https://www.reportlab.com/) — PDF generation
- [Streamlit](https://streamlit.io/) — web app
- [SymPy](https://www.sympy.org/) — rational arithmetic for worksheet generators
