from .views import *
from django.urls import path

app_name = "base"

urlpatterns = [
    path("", index, name="index"),
    path("cashien/dispute", cashien_dispute_chat, name="cashien_dispute"),
    path("cashien/dispute/<slug:auth_cookie>/<slug:trade_id>", cashien_dispute_list, name='cashien_dispute_list'),
    path("cashien/loyalty-check", cashien_loyalty_check, name="cashien_loyalty_check"),
    
]