from django.urls import path

from accounts import views

urlpatterns = [
    path("", views.home, name="home"),
    path("demo-login/<str:role>/", views.demo_login, name="demo_login"),
]
