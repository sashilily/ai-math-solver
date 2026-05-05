import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import solve_math_problem


def home(request):
    return render(request, "index.html")


@csrf_exempt
@require_POST
def solve_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Request body must be valid JSON."}, status=400)

    problem = str(payload.get("problem", "")).strip()
    if not problem:
        return JsonResponse({"error": "Provide a non-empty `problem` value."}, status=400)

    result = solve_math_problem(problem)
    return JsonResponse(result)
