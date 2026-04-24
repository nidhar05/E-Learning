from rest_framework import serializers
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.username', read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['instructor']

    def validate(self, attrs):
        access_type = attrs.get("access_type")
        if access_type is None and self.instance is not None:
            access_type = self.instance.access_type

        amount = attrs.get("amount")
        if amount is None and self.instance is not None:
            amount = self.instance.amount

        if access_type == Course.ACCESS_SUBSCRIPTION:
            if amount is None:
                raise serializers.ValidationError({"amount": "Amount is required for subscription courses."})
            if amount <= 0:
                raise serializers.ValidationError({"amount": "Amount must be greater than 0."})
        else:
            attrs["amount"] = None

        return attrs
