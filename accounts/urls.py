from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import  LogoutView

from .views import UserRegistration, LogoutAPIView ,Login

urlpatterns = [
    path('login/', Login),
    path('logout/', csrf_exempt(LogoutView.as_view()), name="logout"),
    path('register/', csrf_exempt(UserRegistration.as_view())),
]
