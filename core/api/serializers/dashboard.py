from rest_framework import serializers


class DashboardPropertiesSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    occupied = serializers.IntegerField()
    vacant = serializers.IntegerField()
    under_maintenance = serializers.IntegerField()


class DashboardTenantsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    inactive = serializers.IntegerField()


class DashboardFinancialSerializer(serializers.Serializer):
    monthly_rental_income = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    mortgage_outstanding = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    monthly_mortgage_payment = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    current_month_income = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    current_month_expense = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    current_month_net = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )


class DashboardComplianceSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    expired = serializers.IntegerField()
    expiring_soon = serializers.IntegerField()


class DashboardDocumentsSerializer(serializers.Serializer):
    total = serializers.IntegerField()


class DashboardSubscriptionSerializer(serializers.Serializer):
    plan = serializers.CharField(allow_null=True)
    status = serializers.CharField(allow_null=True)
    current_period_end = serializers.DateTimeField(
        allow_null=True,
    )


class DashboardSupportSerializer(serializers.Serializer):
    open = serializers.IntegerField()
    in_progress = serializers.IntegerField()


class DashboardMortgagesSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    total_outstanding = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    fixed_rate = serializers.IntegerField()
    variable_rate = serializers.IntegerField()
    tracker = serializers.IntegerField()
    offset = serializers.IntegerField()


class DashboardSummarySerializer(serializers.Serializer):
    properties = DashboardPropertiesSerializer()
    mortgages = DashboardMortgagesSerializer()
    tenants = DashboardTenantsSerializer(required=False)
    financial = DashboardFinancialSerializer(required=False)
    compliance = DashboardComplianceSerializer(required=False)
    documents = DashboardDocumentsSerializer(required=False)
    subscription = DashboardSubscriptionSerializer(required=False)
    support = DashboardSupportSerializer(required=False)


class PropertyTypeSummarySerializer(serializers.Serializer):
    type = serializers.CharField()
    label = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class PropertyTypeDashboardSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    data = PropertyTypeSummarySerializer(many=True)


class ComplianceTypeSummarySerializer(serializers.Serializer):
    type = serializers.CharField()
    label = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class ComplianceTypeDashboardSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    data = ComplianceTypeSummarySerializer(many=True)


class IncomeExpenseMonthSerializer(serializers.Serializer):
    month = serializers.CharField()
    label = serializers.CharField()
    income = serializers.DecimalField(max_digits=20, decimal_places=2)
    expense = serializers.DecimalField(max_digits=20, decimal_places=2)
    net = serializers.DecimalField(max_digits=20, decimal_places=2)


class DashboardIncomeExpenseDashboardSerializer(serializers.Serializer):
    months = serializers.IntegerField()
    total_income = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=20, decimal_places=2)
    net = serializers.DecimalField(max_digits=20, decimal_places=2)
    data = IncomeExpenseMonthSerializer(many=True)
