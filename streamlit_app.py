import os
from pathlib import Path

import django
import streamlit as st

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mathsolver.settings")
django.setup()

from solver.services import solve_math_problem  # noqa: E402


BASE_DIR = Path(__file__).resolve().parent
CSS_PATH = BASE_DIR / "frontend" / "static" / "css" / "styles.css"


def load_css():
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


st.set_page_config(
    page_title="AI Mathematical Solver",
    page_icon="sum",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css()

st.markdown(
    """
    <section class="hero">
      <div>
        <p class="eyebrow">Django powered symbolic solver</p>
        <h1>AI Mathematical Solver</h1>
        <p class="lede">Solve everyday math, algebra, calculus, matrices, and algorithm-style expressions with clear steps.</p>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Examples")
    examples = [
        "solve x^2 - 5*x + 6 = 0",
        "derivative of sin(x) + x^3 with respect to x",
        "integral of 2*x + cos(x) with respect to x",
        "limit of sin(x)/x as x -> 0",
        "factor x^3 - 6*x^2 + 11*x - 6",
        "A laptop costs 1200 with a 15 percent discount",
        "investment 5000 at 8 percent for 3 years",
        "determinant of [[1, 2], [3, 4]]",
    ]
    chosen = st.selectbox("Try a problem", examples)
    st.caption("You can edit the prompt in the main input before solving.")

problem = st.text_area(
    "Enter your mathematical problem",
    value=chosen,
    height=130,
    placeholder="Example: solve x^2 - 9 = 0, or a car travels 150 km in 3 hours, find speed",
)

col_a, col_b = st.columns([1, 5])
with col_a:
    solve = st.button("Solve", type="primary", use_container_width=True)
with col_b:
    st.markdown('<div class="hint">Supports expressions, equations, derivatives, integrals, limits, matrices, percentages, rates, and interest.</div>', unsafe_allow_html=True)

if solve and problem.strip():
    result = solve_math_problem(problem)
    st.markdown('<div class="result-grid">', unsafe_allow_html=True)
    left, right = st.columns([2, 3])
    with left:
        st.markdown("### Answer")
        st.markdown(f"<div class='answer'>{result['answer']}</div>", unsafe_allow_html=True)
        st.metric("Problem type", result["category"])
        if result.get("expression"):
            st.code(result["expression"], language="python")
    with right:
        st.markdown("### Step-by-step reasoning")
        for index, step in enumerate(result["steps"], start=1):
            st.markdown(f"<div class='step'><strong>{index}</strong><span>{step}</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
elif solve:
    st.warning("Enter a problem first.")

st.markdown(
    """
    <footer>
      <span>Django backend module:</span> <code>solver.services.solve_math_problem</code>
      <span>API endpoint:</span> <code>POST /api/solve/</code>
    </footer>
    """,
    unsafe_allow_html=True,
)
