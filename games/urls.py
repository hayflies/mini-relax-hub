from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("guestbook/", views.guestbook_page, name="guestbook"),
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("games/total-click/", views.total_click_page, name="total_click"),
    path("games/total-click/count/", views.total_click_count, name="total_click_count"),
    path("games/total-click/increment/", views.increment_total_click, name="increment_total_click"),
    path("games/drawing/", views.drawing_page, name="drawing"),
    path("games/reaction/", views.reaction_test_page, name="reaction_test"),
    path("games/reaction/save/", views.save_reaction_time, name="save_reaction_time"),
    path("games/word/", views.word_game_page, name="word_game"),
    path("games/word/submit/", views.submit_word_guess, name="submit_word_guess"),
    path("games/word/reset/", views.reset_word_game, name="reset_word_game"),
]
