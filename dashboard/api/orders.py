from __future__ import annotations

import json
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from orders.forms import OrderCreateForm, OrderUpdateForm
from orders.models import Order


def serialize_order(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "description": order.description,
        "quantity": order.quantity,
        "due_date": order.due_date.isoformat() if order.due_date else None,
        "production_status": order.production_status,
        "assigned_staff": order.assigned_staff_id,
        "updated_at": order.updated_at.isoformat(),
        "external_reference": order.external_reference,
    }


@method_decorator(csrf_exempt, name="dispatch")
class OrderCollectionView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> JsonResponse:
        queryset = Order.objects.all()
        status_filter = request.GET.get("status")
        search = request.GET.get("search")
        if status_filter:
            queryset = queryset.filter(production_status=status_filter)
        if search:
            queryset = queryset.filter(order_number__icontains=search)
        return JsonResponse({"results": [serialize_order(order) for order in queryset]})

    def post(self, request: HttpRequest) -> JsonResponse:
        payload = json.loads(request.body or "{}")
        form = OrderCreateForm(payload)
        if form.is_valid():
            order = form.save(commit=False)
            order._acting_user = request.user
            order.save()
            return JsonResponse(serialize_order(order), status=201)
        return JsonResponse({"errors": form.errors}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class OrderDetailView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int) -> JsonResponse:
        order = get_object_or_404(Order, pk=pk)
        return JsonResponse(serialize_order(order))

    def put(self, request: HttpRequest, pk: int) -> JsonResponse:
        order = get_object_or_404(Order, pk=pk)
        payload = json.loads(request.body or "{}")
        form = OrderUpdateForm(payload, instance=order)
        if form.is_valid():
            order._previous_status = order.production_status
            order._acting_user = request.user
            form.save()
            return JsonResponse(serialize_order(order))
        return JsonResponse({"errors": form.errors}, status=400)

    def delete(self, request: HttpRequest, pk: int) -> JsonResponse:
        order = get_object_or_404(Order, pk=pk)
        order.delete()
        return JsonResponse({}, status=204)


@method_decorator(csrf_exempt, name="dispatch")
class AssignOrderView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> JsonResponse:
        order = get_object_or_404(Order, pk=pk)
        payload = json.loads(request.body or "{}")
        user_id = payload.get("user_id")
        if not user_id:
            return JsonResponse({"error": "user_id is required"}, status=400)
        order._previous_status = order.production_status
        order._acting_user = request.user
        order.assigned_staff_id = user_id
        order.save(update_fields=["assigned_staff", "updated_at"])
        return JsonResponse(serialize_order(order))
