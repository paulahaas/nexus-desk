from django.urls import path

from tickets import views

app_name = "tickets"

urlpatterns = [
    path("", views.queue, name="queue"),
    path("<int:pk>/assumir/", views.assume_ticket, name="assume"),
]
