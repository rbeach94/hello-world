from __future__ import annotations

from django.urls import path

from . import views
from dashboard.api import orders as api_views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="list"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="detail"),
    path("<int:pk>/update/", views.update_order, name="update"),

    # API endpoints
    path("api/", api_views.OrderCollectionView.as_view(), name="api-list-create"),
    path("api/<int:pk>/", api_views.OrderDetailView.as_view(), name="api-detail"),
    path("api/<int:pk>/assign/", api_views.AssignOrderView.as_view(), name="api-assign"),
]
