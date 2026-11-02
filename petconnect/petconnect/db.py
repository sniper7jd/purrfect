"""Query helpers shared across apps."""

from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce


def count_related(model, fk_field, outer="pk", **filters):
    """Correlated COUNT subquery, so list pages count related rows without N+1 queries
    and without the row multiplication of joining several reverse relations at once."""
    counts = (
        model.objects.filter(**{fk_field: OuterRef(outer)}, **filters)
        .order_by()
        .values(fk_field)
        .annotate(n=Count("pk"))
        .values("n")
    )
    return Coalesce(Subquery(counts, output_field=IntegerField()), 0)
