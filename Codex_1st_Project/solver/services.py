from __future__ import annotations

import math
import re
from dataclasses import dataclass

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


@dataclass
class SolverResult:
    problem: str
    category: str
    answer: str
    steps: list[str]
    expression: str | None = None

    def as_dict(self) -> dict:
        return {
            "problem": self.problem,
            "category": self.category,
            "answer": self.answer,
            "steps": self.steps,
            "expression": self.expression,
        }


def solve_math_problem(problem: str) -> dict:
    cleaned = _normalize_problem(problem)
    try:
        result = _route_problem(problem, cleaned)
    except Exception as exc:  # Keep the UI helpful instead of crashing on novel prompts.
        result = SolverResult(
            problem=problem,
            category="Needs clarification",
            answer="I could not solve this exactly yet.",
            steps=[
                "I tried to parse the problem with the symbolic math engine.",
                f"The parser reported: {exc}",
                "Try writing the equation or expression explicitly, for example `solve x^2 - 5x + 6 = 0`.",
            ],
            expression=cleaned,
        )
    return result.as_dict()


def _route_problem(original: str, cleaned: str) -> SolverResult:
    lower = original.lower()

    word_result = _try_real_world_problem(original)
    if word_result:
        return word_result

    if "derivative" in lower or lower.startswith("differentiate"):
        return _differentiate(original, cleaned)
    if "integral" in lower or lower.startswith("integrate"):
        return _integrate(original, cleaned)
    if "limit" in lower:
        return _limit(original, cleaned)
    if "factor" in lower:
        return _factor(original, cleaned)
    if "simplify" in lower:
        return _simplify(original, cleaned)
    if "matrix" in lower or _looks_like_matrix(cleaned):
        return _matrix(original, cleaned)
    if "=" in cleaned or lower.startswith("solve"):
        return _solve_equation(original, cleaned)
    return _evaluate_expression(original, cleaned)


def _normalize_problem(problem: str) -> str:
    text = problem.strip()
    replacements = {
        "^": "**",
        "pi": "pi",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\bplus\b", "+", text, flags=re.I)
    text = re.sub(r"\bminus\b", "-", text, flags=re.I)
    text = re.sub(r"\btimes\b|\bmultiplied by\b", "*", text, flags=re.I)
    text = re.sub(r"\bdivided by\b", "/", text, flags=re.I)
    return text


def _extract_math_text(cleaned: str, keywords: list[str]) -> str:
    expr = cleaned
    for keyword in keywords:
        expr = re.sub(keyword, "", expr, flags=re.I).strip()
    expr = expr.strip(": ")
    return expr


def _sympify(expr: str):
    return parse_expr(
        expr,
        local_dict=_symbol_locals(expr),
        transformations=TRANSFORMATIONS,
        evaluate=True,
    )


def _symbol_locals(expr: str) -> dict:
    names = set(re.findall(r"\b[a-zA-Z]\w*\b", expr))
    allowed = {"sin", "cos", "tan", "sqrt", "log", "ln", "exp", "pi", "E"}
    locals_map = {name: sp.Symbol(name) for name in names if name not in allowed}
    locals_map["ln"] = sp.log
    return locals_map


def _pick_symbol(expr: str):
    parsed = _sympify(expr)
    symbols = sorted(parsed.free_symbols, key=lambda item: item.name)
    return symbols[0] if symbols else sp.Symbol("x")


def _evaluate_expression(original: str, cleaned: str) -> SolverResult:
    expr = _extract_math_text(cleaned, [r"^calculate", r"^evaluate", r"^what is"])
    parsed = _sympify(expr)
    simplified = sp.simplify(parsed)
    numeric = sp.N(simplified)
    return SolverResult(
        problem=original,
        category="Expression evaluation",
        answer=str(simplified if numeric == simplified else numeric),
        steps=[
            f"Parsed the expression as `{sp.sstr(parsed)}`.",
            f"Simplified it to `{sp.sstr(simplified)}`.",
            f"Computed a numeric form: `{sp.sstr(numeric)}`.",
        ],
        expression=sp.sstr(parsed),
    )


def _solve_equation(original: str, cleaned: str) -> SolverResult:
    expr = _extract_math_text(cleaned, [r"^solve", r"^find"])
    if "=" in expr:
        left, right = expr.split("=", 1)
        equation = sp.Eq(_sympify(left), _sympify(right))
        symbols = sorted(equation.free_symbols, key=lambda item: item.name)
    else:
        parsed = _sympify(expr)
        equation = sp.Eq(parsed, 0)
        symbols = sorted(parsed.free_symbols, key=lambda item: item.name)

    symbol = symbols[0] if symbols else sp.Symbol("x")
    solutions = sp.solve(equation, symbol)
    return SolverResult(
        problem=original,
        category="Equation solving",
        answer=f"{symbol} = {solutions}",
        steps=[
            f"Rewrote the problem as `{sp.sstr(equation)}`.",
            f"Selected `{symbol}` as the unknown variable.",
            "Used symbolic solving to isolate the variable.",
            f"Solution set: `{solutions}`.",
        ],
        expression=sp.sstr(equation),
    )


def _differentiate(original: str, cleaned: str) -> SolverResult:
    expr = _extract_math_text(cleaned, [r"derivative of", r"differentiate", r"with respect to [a-zA-Z]\w*"])
    symbol = _variable_after_phrase(cleaned, "with respect to") or _pick_symbol(expr)
    parsed = _sympify(expr)
    derivative = sp.diff(parsed, symbol)
    return SolverResult(
        problem=original,
        category="Calculus derivative",
        answer=sp.sstr(derivative),
        steps=[
            f"Parsed the function as `{sp.sstr(parsed)}`.",
            f"Differentiated with respect to `{symbol}`.",
            f"Result: `{sp.sstr(derivative)}`.",
        ],
        expression=sp.sstr(parsed),
    )


def _integrate(original: str, cleaned: str) -> SolverResult:
    expr = _extract_math_text(cleaned, [r"integral of", r"integrate", r"with respect to [a-zA-Z]\w*"])
    symbol = _variable_after_phrase(cleaned, "with respect to") or _pick_symbol(expr)
    parsed = _sympify(expr)
    integral = sp.integrate(parsed, symbol)
    return SolverResult(
        problem=original,
        category="Calculus integral",
        answer=f"{sp.sstr(integral)} + C",
        steps=[
            f"Parsed the integrand as `{sp.sstr(parsed)}`.",
            f"Integrated with respect to `{symbol}`.",
            "Added `+ C` for the constant of integration.",
        ],
        expression=sp.sstr(parsed),
    )


def _limit(original: str, cleaned: str) -> SolverResult:
    expr = _extract_math_text(cleaned, [r"limit of", r"limit"])
    match = re.search(r"as\s+([a-zA-Z]\w*)\s*(?:->|to)\s*([^\s]+)", expr, flags=re.I)
    if match:
        variable = sp.Symbol(match.group(1))
        target = _sympify(match.group(2))
        expr = expr[: match.start()].strip()
    else:
        variable = _pick_symbol(expr)
        target = 0
    parsed = _sympify(expr)
    value = sp.limit(parsed, variable, target)
    return SolverResult(
        problem=original,
        category="Calculus limit",
        answer=sp.sstr(value),
        steps=[
            f"Parsed the expression as `{sp.sstr(parsed)}`.",
            f"Evaluated the limit as `{variable}` approaches `{target}`.",
            f"Limit value: `{sp.sstr(value)}`.",
        ],
        expression=sp.sstr(parsed),
    )


def _factor(original: str, cleaned: str) -> SolverResult:
    expr = _extract_math_text(cleaned, [r"factor"])
    parsed = _sympify(expr)
    factored = sp.factor(parsed)
    return SolverResult(
        problem=original,
        category="Algebra factoring",
        answer=sp.sstr(factored),
        steps=[
            f"Parsed `{sp.sstr(parsed)}`.",
            "Applied symbolic factorization.",
            f"Factored form: `{sp.sstr(factored)}`.",
        ],
        expression=sp.sstr(parsed),
    )


def _simplify(original: str, cleaned: str) -> SolverResult:
    expr = _extract_math_text(cleaned, [r"simplify"])
    parsed = _sympify(expr)
    simplified = sp.simplify(parsed)
    return SolverResult(
        problem=original,
        category="Algebra simplification",
        answer=sp.sstr(simplified),
        steps=[
            f"Parsed `{sp.sstr(parsed)}`.",
            "Combined like terms and applied algebraic identities.",
            f"Simplified result: `{sp.sstr(simplified)}`.",
        ],
        expression=sp.sstr(parsed),
    )


def _matrix(original: str, cleaned: str) -> SolverResult:
    expr = _extract_math_text(cleaned, [r"matrix", r"determinant of", r"inverse of"])
    matrix = sp.Matrix(sp.sympify(expr))
    lower = original.lower()
    if "determinant" in lower:
        answer = matrix.det()
        action = "computed the determinant"
    elif "inverse" in lower:
        answer = matrix.inv()
        action = "computed the inverse"
    else:
        answer = matrix.rref()[0]
        action = "reduced the matrix to row echelon form"
    return SolverResult(
        problem=original,
        category="Linear algebra",
        answer=sp.sstr(answer),
        steps=[
            f"Parsed the matrix as `{sp.sstr(matrix)}`.",
            f"Applied linear algebra operations and {action}.",
            f"Result: `{sp.sstr(answer)}`.",
        ],
        expression=sp.sstr(matrix),
    )


def _try_real_world_problem(original: str) -> SolverResult | None:
    lower = original.lower()
    numbers = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", original)]
    if len(numbers) < 2:
        return None

    if any(word in lower for word in ["discount", "sale", "off"]):
        price, percent = numbers[0], numbers[1]
        final = price * (1 - percent / 100)
        return SolverResult(
            problem=original,
            category="Real-world percentage",
            answer=f"{final:.2f}",
            steps=[
                f"Original value: {price}.",
                f"Discount rate: {percent}%, so the multiplier is {1 - percent / 100:.4f}.",
                f"Final value = {price} * {1 - percent / 100:.4f} = {final:.2f}.",
            ],
        )

    if any(word in lower for word in ["interest", "loan", "investment"]):
        principal, rate = numbers[0], numbers[1]
        years = numbers[2] if len(numbers) > 2 else 1
        amount = principal * math.pow(1 + rate / 100, years)
        return SolverResult(
            problem=original,
            category="Real-world compound interest",
            answer=f"{amount:.2f}",
            steps=[
                f"Principal: {principal}.",
                f"Annual rate: {rate}% for {years} year(s).",
                f"Compound amount = {principal} * (1 + {rate}/100)^{years} = {amount:.2f}.",
            ],
        )

    if any(word in lower for word in ["speed", "distance", "time"]):
        first, second = numbers[0], numbers[1]
        if "speed" in lower and "distance" in lower:
            value = first / second
            label = "speed"
        elif "distance" in lower:
            value = first * second
            label = "distance"
        else:
            value = first / second
            label = "time"
        return SolverResult(
            problem=original,
            category="Real-world rate problem",
            answer=f"{label} = {value:.4g}",
            steps=[
                "Identified this as a distance-rate-time relationship.",
                "Used `distance = speed * time` and rearranged for the requested quantity.",
                f"Computed {label}: {value:.4g}.",
            ],
        )
    return None


def _variable_after_phrase(text: str, phrase: str):
    match = re.search(fr"{phrase}\s+([a-zA-Z]\w*)", text, flags=re.I)
    return sp.Symbol(match.group(1)) if match else None


def _looks_like_matrix(text: str) -> bool:
    return text.strip().startswith("[[") and text.strip().endswith("]]")
