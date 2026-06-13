import django_filters
from .models import Application, Company


class ApplicationFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(choices=Application.Status.choices)
    work_mode = django_filters.MultipleChoiceFilter(choices=Application.WorkMode.choices)
    applied_after = django_filters.DateFilter(field_name="applied_date", lookup_expr="gte")
    applied_before = django_filters.DateFilter(field_name="applied_date", lookup_expr="lte")
    salary_min = django_filters.NumberFilter(field_name="salary_min", lookup_expr="gte")
    salary_max = django_filters.NumberFilter(field_name="salary_max", lookup_expr="lte")
    referral = django_filters.BooleanFilter()
    company_name = django_filters.CharFilter(field_name="company__name", lookup_expr="icontains")

    class Meta:
        model = Application
        fields = ["status", "work_mode", "referral", "company"]


class CompanyFilter(django_filters.FilterSet):
    industry = django_filters.CharFilter(lookup_expr="icontains")
    size = django_filters.MultipleChoiceFilter(choices=Company.Size.choices)

    class Meta:
        model = Company
        fields = ["industry", "size"]
