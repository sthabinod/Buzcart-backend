
from django.db.models import Sum
from commerce.models import Order
SUCCESS_STATUSES = ("completed", "paid")
def get_total_spent(user):
    orders_qs = Order.objects.filter(user=user)
    total_spent = (
        orders_qs.filter(status__in=SUCCESS_STATUSES)
        .aggregate(total=Sum("total"))
        .get("total") or 0
    )
    return total_spent