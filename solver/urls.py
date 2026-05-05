from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("api/solve/", views.solve_api, name="solve_api"),
]
