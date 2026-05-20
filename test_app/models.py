from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=200)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField()

class Employee(models.Model):
    departament = models.ForeignKey(Department)
    full_name = models.Charfield(max_lenght=200)
    position = models.CharField(max_length=15)
    hired_at = models.Datetime()
    created_at = models.DateTime()
