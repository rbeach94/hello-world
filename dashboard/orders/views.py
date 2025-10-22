from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .forms import OrderFilterForm, OrderUpdateForm
from .models import Order, OrderGarment


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    paginate_by = 25
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):  # type: ignore[override]
        queryset = super().get_queryset().select_related("assigned_staff")
        form = OrderFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data["search"]
            if search:
                queryset = queryset.filter(
                    Q(order_number__icontains=search)
                    | Q(customer_name__icontains=search)
                    | Q(description__icontains=search)
                )
            status = form.cleaned_data["status"]
            if status:
                queryset = queryset.filter(production_status=status)
            if form.cleaned_data["assigned_to_me"] and self.request.user.is_authenticated:
                queryset = queryset.filter(assigned_staff=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["filter_form"] = OrderFilterForm(self.request.GET)
        context["now"] = timezone.now()
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    queryset = (
        Order.objects.select_related("assigned_staff")
        .prefetch_related("audit_trail__user", "garments")
    )

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["form"] = OrderUpdateForm(instance=self.object)
        context["garments"] = self.object.garments.all()
        return context


@login_required
def update_order(request: HttpRequest, pk: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=pk)
    form = OrderUpdateForm(request.POST or None, instance=order)
    if request.method == "POST" and form.is_valid():
        order._previous_status = order.production_status
        order._acting_user = request.user
        form.save()
        messages.success(request, f"Order {order.order_number} updated successfully")
        return redirect(reverse("orders:detail", kwargs={"pk": order.pk}))
    return render(request, "orders/order_detail.html", {"order": order, "form": form})


class PurchasingListView(LoginRequiredMixin, ListView):
    model = OrderGarment
    template_name = "orders/purchasing_list.html"
    context_object_name = "garments"

    def get_queryset(self):  # type: ignore[override]
        return (
            OrderGarment.objects.filter(status=OrderGarment.GarmentStatus.NEEDS_ORDERING)
            .select_related("order", "order__assigned_staff")
            .order_by("order__due_date", "order__order_number")
        )


class StockListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/stock_list.html"
    context_object_name = "orders"

    def get_queryset(self):  # type: ignore[override]
        return (
            Order.objects.filter(
                production_status=Order.ProductionStatus.AWAITING_GARMENTS
            )
            .select_related("assigned_staff")
            .prefetch_related("garments")
            .order_by("due_date", "order_number")
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        order_id = request.POST.get("order_id")
        if not order_id:
            messages.error(request, "No order selected.")
            return redirect("orders:stock")
        order = get_object_or_404(Order, pk=order_id)
        if order.production_status != Order.ProductionStatus.AWAITING_GARMENTS:
            messages.warning(request, "Selected order is not awaiting garments.")
            return redirect("orders:stock")
        order._previous_status = order.production_status
        order._acting_user = request.user
        order.production_status = Order.ProductionStatus.READY
        order.save(update_fields=["production_status", "updated_at"])
        order.garments.update(status=OrderGarment.GarmentStatus.IN_STOCK)
        messages.success(request, f"Order {order.order_number} marked as Ready.")
        return redirect("orders:stock")


class ProductionListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/production_list.html"
    context_object_name = "orders"

    def get_queryset(self):  # type: ignore[override]
        queryset = (
            Order.objects.filter(production_status=Order.ProductionStatus.READY)
            .select_related("assigned_staff")
            .prefetch_related("garments")
            .order_by("due_date", "order_number")
        )
        decoration = self.request.GET.get("decoration")
        valid = {choice for choice, _ in Order.DecorationType.choices}
        if decoration in valid:
            queryset = queryset.filter(decoration_type=decoration)
        return queryset

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["decoration"] = self.request.GET.get("decoration", "")
        context["decoration_choices"] = [("", "All"), *Order.DecorationType.choices]
        return context
