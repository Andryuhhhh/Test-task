from django.urls import path

# from test_task.urls import urlpatterns
from .views import DepartmentRetrieveUpdateDestroyView, EmployeeInDepartmentCreateView, DepartmentListCreateView


urlpatterns = [
    path('departments/', DepartmentListCreateView.as_view()),
    path('departments/<int:pk>/', DepartmentRetrieveUpdateDestroyView.as_view()),
    path('departments/<int:pk>/employees/', EmployeeInDepartmentCreateView.as_view()),
]



