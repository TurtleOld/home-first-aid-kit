from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .reference_parser.views import DrugLookupFormsView, DrugLookupParseView
from .views import ChangeLogViewSet, MedicineViewSet, ShoppingItemViewSet

router = DefaultRouter(trailing_slash=False)
router.register("medicines", MedicineViewSet, basename="medicine")
router.register("shopping-items", ShoppingItemViewSet, basename="shopping-item")
router.register("changelog", ChangeLogViewSet, basename="changelog")

urlpatterns = [
    path("", include(router.urls)),
    path("drug-lookup/forms", DrugLookupFormsView.as_view(), name="drug-lookup-forms"),
    path("drug-lookup/parse", DrugLookupParseView.as_view(), name="drug-lookup-parse"),
]
