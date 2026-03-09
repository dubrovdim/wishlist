from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create_wishlist, name='create_wishlist'),
    path('list/<uuid:pk>/', views.wishlist_detail, name='wishlist_detail'),
    path('list/<uuid:pk>/add/', views.add_item, name='add_item'),
    path('item/<int:item_id>/reserve/', views.reserve_item, name='reserve_item'),
]