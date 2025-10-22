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
from .models import Order


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
        Order.objects.select_related("assigned_staff").prefetch_related("audit_trail__user")
    )

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["form"] = OrderUpdateForm(instance=self.object)
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
