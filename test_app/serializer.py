from rest_framework import serializers
from .models import Department, Employee

class EmpSerializer(serializers.ModelSerializer):      # Сериализатор для модели "Employee"
    pass

class DeptSerializer(serializers.ModelSerializer):         # Сереиалайзер дял модeли Департамент
    pass