from __future__ import annotations

from django import forms

from .models import Order


class OrderFilterForm(forms.Form):
    search = forms.CharField(required=False, label="Search")
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses"), *Order.ProductionStatus.choices],
    )
    assigned_to_me = forms.BooleanField(
        required=False,
        label="Only my orders",
    )


class OrderBaseForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "customer_name",
            "description",
            "quantity",
            "due_date",
            "production_status",
            "assigned_staff",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


class OrderCreateForm(OrderBaseForm):
    order_number = forms.CharField(max_length=64)

    class Meta(OrderBaseForm.Meta):
        fields = ["order_number", *OrderBaseForm.Meta.fields]


class OrderUpdateForm(OrderBaseForm):
    pass
