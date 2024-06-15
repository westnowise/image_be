from django.urls import path
from . import views


urlpatterns = [
    path('object', views.main, name='main'),
    path('animal', views.main2, name='main'),
]