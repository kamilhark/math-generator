#!/usr/bin/env python3
"""
Streamlit web app — Math Worksheet Generator
Exposes all four PDF generators with a friendly UI.
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

GENERATORS = {
    "➕➖  Dodawanie i odejmowanie": "addsub",
    "✖️➗  Mnożenie i dzielenie": "muldiv",
    "🔄  Zamiana ułamków niewłaściwych i mieszanych": "convert",
    "🧮  Działania mieszane (z nawiasami)": "mixed_ops",
}

choice = st.selectbox("Wybierz rodzaj arkusza", list(GENERATORS.keys()))
kind = GENERATORS[choice]

st.divider()

# ---------------------------------------------------------------------------
# Shared controls
# ---------------------------------------------------------------------------
num_problems = st.number_input("Liczba zadań", min_value=4, max_value=20, value=20, step=2)
seed = None

worksheet_title = {
    "addsub":    "Dodawanie i odejmowanie ułamków",
    "muldiv":    "Mnożenie i dzielenie ułamków",
    "convert":   "Ułamki niewłaściwe i liczby mieszane",
    "mixed_ops": "Działania na ułamkach z nawiasami",
}[kind]

# ---------------------------------------------------------------------------
# Generator-specific controls
# ---------------------------------------------------------------------------
extra_kwargs: dict = {}


# ---------------------------------------------------------------------------
# Generate PDF and offer single-click download
# ---------------------------------------------------------------------------

def build_pdf_bytes(kind, num_problems, worksheet_title):
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
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


st.divider()
pdf_bytes = build_pdf_bytes(kind, int(num_problems), worksheet_title)
st.download_button(
    label="🖨️  Generuj i pobierz arkusz",
    data=pdf_bytes,
    file_name=f"arkusz_{kind}.pdf",
    mime="application/pdf",
    type="primary",
    use_container_width=True,
)
