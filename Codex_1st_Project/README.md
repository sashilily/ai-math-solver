# AI Mathematical Solver

A Python/Django-backed mathematical solver with a Streamlit web interface and custom HTML/CSS styling.

## What it solves

- Arithmetic and symbolic expression evaluation
- Algebraic equations and factoring
- Simplification
- Derivatives, integrals, and limits
- Matrix determinant, inverse, and row reduction
- Real-world percentage, rate, and compound-interest examples

## Run locally

Install Python 3.11+ first, then run:

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

In a second terminal, start the Streamlit web server:

```powershell
streamlit run streamlit_app.py
```

The Django API will be available at `http://127.0.0.1:8000/api/solve/`, and Streamlit will usually open at `http://localhost:8501`.

## API example

```json
{
  "problem": "solve x^2 - 5*x + 6 = 0"
}
```

## Project structure

- `solver/services.py` contains the main mathematical reasoning engine.
- `solver/views.py` exposes the Django web page and JSON API.
- `streamlit_app.py` serves the interactive frontend.
- `frontend/static/css/styles.css` contains the shared styling.
- `frontend/templates/index.html` is the simple Django landing/API page.
