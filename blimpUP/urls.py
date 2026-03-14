from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("relogin", views.relogin_view, name="relogin"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("register_blimp", views.register_blimp, name="register_blimp"),
    path("blimp/<int:id>", views.blimp_view, name="blimp"),
    path("sign_up", views.sign_up, name="sign_up"),
    path("trip_requests", views.trip_requests, name="trip_requests"),
    path("my_trips", views.my_trips, name="my_trips"),
    path("my_blimps", views.my_blimps, name="my_blimps"),
    path("review/<int:id>", views.review, name="review"),
    path("edit_blimp/<int:id>", views.edit_blimp, name="edit_blimp"),
    path("delete_blimp/<int:id>", views.delete_blimp, name="delete_blimp")
]
