from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.imgUpload, name='imgUpload'),
    path('analyze/', views.analyze, name='analyze'),
]
