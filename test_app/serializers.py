from rest_framework import serializers
from .models import Department, Employee


def validate_not_blank(value):
    value = value.strip()
    if not value:
        raise serializers.ValidationError('This field cannot be blank.')
    return value


class DepartmentValidationMixin:
    def validate_name(self, value):
        return validate_not_blank(value)

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        name = attrs.get('name', instance.name if instance else None)
        parent = attrs.get('parent', instance.parent if instance else None)

        if name is None:
            return attrs

        queryset = Department.objects.filter(name=name, parent=parent)
        if instance:
            queryset = queryset.exclude(id=instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                {'name': 'Department with this name already exists in this parent.'}
            )

        return attrs


class DepartmentCreateSerializer(DepartmentValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Department
        fields= ['id', 'name', 'parent', 'created_at']
        read_only_fields = ['id', 'created_at']


class EmployeeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields= ['id', 'department', 'full_name', 'position', 'hired_at', 'created_at']
        read_only_fields = ['id', 'department', 'created_at']

    def validate_full_name(self, value):
        return validate_not_blank(value)

    def validate_position(self, value):
        return validate_not_blank(value)


class DepartmentUpdateSerializer(DepartmentValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Department
        fields= ['name', 'parent']


class EmployeeSerializer (serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields= ['id', 'department', 'full_name', 'position', 'hired_at', 'created_at']


class DepartmentTreeSerializer (serializers.ModelSerializer):
    class Meta:
        model = Department
        fields= ['id', 'name', 'parent', 'created_at']
