# Fraction Worksheet Generator

Generates printable PDF worksheets with fraction addition and subtraction problems using **mixed numbers** (e.g. 2⅔) and **improper fractions** (e.g. 5/2). Each worksheet includes a full answer key.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Generate a 20-problem worksheet (default)
python generate.py

# Custom number of problems
python generate.py -n 30

# Addition only
python generate.py --ops +

# Subtraction only
python generate.py --ops -

# Set output filename
python generate.py -o my_worksheet.pdf

# Set a random seed for reproducibility
python generate.py --seed 42

# Limit difficulty (max whole number = 5, max denominator = 8)
python generate.py --max-whole 5 --max-denom 8

# Custom title
python generate.py --title "Fractions Quiz — Chapter 5"
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `-n` / `--num-problems` | 20 | Number of problems |
| `-o` / `--output` | `worksheet_<timestamp>.pdf` | Output filename |
| `--max-whole` | 9 | Largest whole-number part |
| `--max-denom` | 12 | Largest denominator |
| `--ops` | `+,-` | Operations (comma-separated) |
| `--title` | `Fraction Worksheet` | Title printed on the worksheet |
| `--seed` | *(random)* | Random seed |
