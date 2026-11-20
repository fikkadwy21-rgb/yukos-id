from django.urls import path
from . import views

app_name = "prediksi"

urlpatterns = [
    path("", views.index, name="index"),
]
