from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.response import Response

from .models import Department, Employee
from .serializers import DepartmentCreateSerializer, DepartmentUpdateSerializer, DepartmentTreeSerializer, EmployeeCreateSerializer, EmployeeSerializer


class DepartmentListCreateView(ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentCreateSerializer


class EmployeeInDepartmentCreateView(CreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeCreateSerializer

    def perform_create(self, serializer):
        department = get_object_or_404(Department, id=self.kwargs['pk'])
        serializer.save(department=department)


class DepartmentRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return DepartmentUpdateSerializer
        return DepartmentTreeSerializer

    def retrieve(self, request, *args, **kwargs):
        department = self.get_object()

        depth = int(request.query_params.get('depth', 1))
        depth = min(depth, 5)

        include_employees = request.query_params.get('include_employees', 'true')
        include_employees = include_employees.lower() in ('true', '1', 'yes')

        data = {
            'department': DepartmentTreeSerializer(department).data,
            'employees': [],
            'children': [],
        }

        if include_employees:
            employees = department.employees.order_by('created_at', 'full_name')
            data['employees'] = EmployeeSerializer(employees, many=True).data

        if depth > 0:
            children = department.children.order_by('name')
            data['children'] = [
                self.get_department_tree(child, depth - 1, include_employees)
                for child in children
            ]

        return Response(data)

    def get_department_tree(self, department, depth, include_employees):
        data = DepartmentTreeSerializer(department).data

        if include_employees:
            employees = department.employees.order_by('created_at', 'full_name')
            data['employees'] = EmployeeSerializer(employees, many=True).data
        else:
            data['employees'] = []

        if depth <= 0:
            data['children'] = []
            return data

        children = department.children.order_by('name')
        data['children'] = [
            self.get_department_tree(child, depth - 1, include_employees)
            for child in children
        ]

        return data

    def partial_update(self, request, *args, **kwargs):
        department = self.get_object()

        serializer = self.get_serializer(
            department,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        new_parent = serializer.validated_data.get('parent')

        if new_parent == department:
            return Response(
                {'detail': 'Department cannot be parent of itself.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_parent and self.is_child_department(department, new_parent):
            return Response(
                {'detail': 'Cannot move department inside its own subtree.'},
                status=status.HTTP_409_CONFLICT,
            )

        serializer.save()
        return Response(DepartmentTreeSerializer(department).data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        department = self.get_object()
        mode = request.query_params.get('mode', 'cascade')

        if mode == 'cascade':
            department.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if mode == 'reassign':
            reassign_to_department_id = request.query_params.get(
                'reassign_to_department_id'
            )

            if not reassign_to_department_id:
                return Response(
                    {'detail': 'reassign_to_department_id is required.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            target_department = get_object_or_404(
                Department,
                id=reassign_to_department_id,
            )

            subtree_ids = self.get_subtree_ids(department)

            if target_department.id in subtree_ids:
                return Response(
                    {'detail': 'Cannot reassign employees to deleted department subtree.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Employee.objects.filter(department_id__in=subtree_ids).update(
                department=target_department
            )

            department.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': 'Invalid mode. Use cascade or reassign.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get_subtree_ids(self, department):
        ids = [department.id]

        for child in department.children.all():
            ids.extend(self.get_subtree_ids(child))

        return ids

    def is_child_department(self, department, possible_child):
        return possible_child.id in self.get_subtree_ids(department)