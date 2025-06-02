from .views import *
from django.urls import path

app_name = "base"

urlpatterns = [
    path("", index, name="index"),
]