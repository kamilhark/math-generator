#!/usr/bin/env python3
"""
Streamlit web app — Math Worksheet Generator
Exposes all PDF generators with a friendly UI.
"""

import tempfile
import os
import streamlit as st

st.set_page_config(
    page_title="Generator Zadań Matematycznych",
    page_icon="📐",
    layout="centered",
)

st.title("📐 Generator Zadań Matematycznych")
st.caption("Twórz gotowe do druku arkusze PDF z zadaniami na ułamki.")

CATEGORIES = {
    "🔢  Ułamki zwykłe": {
        "➕➖  Dodawanie i odejmowanie": "addsub",
        "✖️➗  Mnożenie i dzielenie": "muldiv",
        "🔄  Zamiana ułamków niewłaściwych i mieszanych": "convert",
        "🧮  Działania mieszane (z nawiasami)": "mixed_ops",
        "📊  Ułamki na osi i diagramach": "fractions_visual",
        "🟰  Ułamki równoważne (uzupełnij okienko)": "equiv",
        "⚖️  Porównywanie ułamków (<, =, >)": "compare",
    },
    "🔟  Ułamki dziesiętne": {
        "🔄  Zamiana ułamków dziesiętnych": "decimal_convert",
    },
}

category = st.radio("Kategoria", list(CATEGORIES.keys()), horizontal=True)
generators = CATEGORIES[category]
choice = st.selectbox("Rodzaj arkusza", list(generators.keys()))
kind = generators[choice]

st.divider()

# ---------------------------------------------------------------------------
# Shared controls
# ---------------------------------------------------------------------------
num_problems = st.number_input("Liczba zadań", min_value=4, max_value=20, value=10, step=2)
seed = None

worksheet_title = {
    "addsub":           "Dodawanie i odejmowanie ułamków",
    "muldiv":           "Mnożenie i dzielenie ułamków",
    "convert":          "Ułamki niewłaściwe i liczby mieszane",
    "mixed_ops":        "Działania na ułamkach z nawiasami",
    "fractions_visual": "Ułamki – oś liczbowa i diagramy",
    "equiv":            "Uzupełnij ułamki równoważne",
    "compare":          "Porównaj ułamki: wpisz <, = lub >",
    "decimal_convert":  "Ułamki dziesiętne – zamiana",
}[kind]

# ---------------------------------------------------------------------------
# Generator-specific controls
# ---------------------------------------------------------------------------
extra_kwargs: dict = {}

if kind == "fractions_visual":
    fv_labels = {
        "number_line": "Oś liczbowa (litery)",
        "circle": "Koło (wykres kołowy)",
        "bar": "Prostokąt (podział)",
    }
    fv_choice = st.multiselect(
        "Rodzaje zadań (puste = wszystkie losowo)",
        options=list(fv_labels.keys()),
        format_func=lambda k: fv_labels[k],
        default=list(fv_labels.keys()),
    )
    extra_kwargs["problem_types"] = fv_choice if fv_choice else None

if kind == "decimal_convert":
    from generate_decimal_convert import LEVELS
    level_labels = {
        'A': 'Poziom A – ułamki dziesiętne (10, 100)',
        'B': 'Poziom B – ułamki dziesiętne (100, 1000, 10000)',
        'C': 'Poziom C – liczby mieszane z ułamkami dziesiętnymi',
        'D': 'Poziom D – mianowniki 2, 4, 5',
        'E': 'Poziom E – mianowniki 8, 20, 25, 50, 500',
        'MISTRZ': 'Mistrz – mianowniki 12, 40, 125 (z upraszczaniem)',
    }
    extra_kwargs["level"] = st.selectbox(
        "Poziom trudności",
        options=LEVELS,
        format_func=lambda k: level_labels[k],
    )


# ---------------------------------------------------------------------------
# Generate PDF and offer single-click download
# ---------------------------------------------------------------------------

def build_pdf_bytes(kind, num_problems, worksheet_title, **kwargs):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        if kind == "addsub":
            from generate_addsub import build_pdf
            build_pdf(filename=tmp_path, num_problems=num_problems, title=worksheet_title)
        elif kind == "muldiv":
            from generate_muldiv import build_pdf
            build_pdf(filename=tmp_path, num_problems=num_problems, title=worksheet_title)
        elif kind == "convert":
            from generate_convert import build_pdf
            build_pdf(filename=tmp_path, num_problems=num_problems, title=worksheet_title)
        elif kind == "mixed_ops":
            from generate_mixed_ops import build_pdf
            build_pdf(filename=tmp_path, num_problems=num_problems, title=worksheet_title)
        elif kind == "fractions_visual":
            from generate_fractions_visual import build_pdf
            build_pdf(
                filename=tmp_path,
                num_problems=num_problems,
                title=worksheet_title,
                problem_types=kwargs.get("problem_types"),
            )
        elif kind == "equiv":
            from generate_equiv import build_pdf
            build_pdf(filename=tmp_path, num_problems=num_problems, title=worksheet_title)
        elif kind == "compare":
            from generate_compare import build_pdf
            build_pdf(filename=tmp_path, num_problems=num_problems, title=worksheet_title)
        elif kind == "decimal_convert":
            from generate_decimal_convert import build_pdf
            build_pdf(
                filename=tmp_path,
                num_problems=num_problems,
                title=worksheet_title,
                level=kwargs.get("level", "A"),
            )
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


st.divider()
pdf_bytes = build_pdf_bytes(kind, int(num_problems), worksheet_title, **extra_kwargs)
st.download_button(
    label="🖨️  Generuj i pobierz arkusz",
    data=pdf_bytes,
    file_name=f"arkusz_{kind}.pdf",
    mime="application/pdf",
    type="primary",
    use_container_width=True,
)
