from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("polling-unit/", views.polling_unit_results, name="polling_unit_results"),
    path("lga-summary/", views.lga_summary, name="lga_summary"),
    path("new-polling-unit/", views.new_polling_unit, name="new_polling_unit"),
    path("api/lgas/", views.api_lgas, name="api_lgas"),
    path("api/wards/", views.api_wards, name="api_wards"),
    path("api/polling-units/", views.api_polling_units, name="api_polling_units"),
]
