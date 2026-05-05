from solver.services import solve_math_problem


def test_solves_quadratic_equation():
    result = solve_math_problem("solve x^2 - 5x + 6 = 0")

    assert result["category"] == "Equation solving"
    assert "2" in result["answer"]
    assert "3" in result["answer"]


def test_speed_word_problem_uses_distance_over_time():
    result = solve_math_problem("A car travels 150 km in 3 hours, find speed")

    assert result["category"] == "Real-world rate problem"
    assert result["answer"] == "speed = 50"


def test_discount_word_problem_finds_percent_near_percent_word():
    result = solve_math_problem("A 15 percent discount on a 1200 laptop")

    assert result["category"] == "Real-world percentage"
    assert result["answer"] == "1020.00"


def test_interest_word_problem_handles_rate_before_principal():
    result = solve_math_problem("8 percent interest on 5000 for 3 years")

    assert result["category"] == "Real-world compound interest"
    assert result["answer"] == "6298.56"
