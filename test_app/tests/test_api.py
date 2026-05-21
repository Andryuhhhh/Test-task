import pytest
from rest_framework import status
from rest_framework.test import APIClient

from test_app.models import Department, Employee


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_department(api_client):
    response = api_client.post(
        '/api/departments/',
        {'name': 'Engineering', 'parent': None},
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == 'Engineering'
    assert response.data['parent'] is None
    assert Department.objects.filter(name='Engineering').exists()


@pytest.mark.django_db
def test_create_department_trims_name(api_client):
    response = api_client.post(
        '/api/departments/',
        {'name': '  Engineering  ', 'parent': None},
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == 'Engineering'
    assert Department.objects.get().name == 'Engineering'


@pytest.mark.django_db
def test_create_department_rejects_blank_name(api_client):
    response = api_client.post(
        '/api/departments/',
        {'name': '   ', 'parent': None},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Department.objects.count() == 0


@pytest.mark.django_db
def test_department_name_must_be_unique_in_same_parent(api_client):
    root = Department.objects.create(name='Engineering')
    Department.objects.create(name='Backend', parent=root)

    response = api_client.post(
        '/api/departments/',
        {'name': 'Backend', 'parent': root.id},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_department_name_can_repeat_in_different_parents(api_client):
    engineering = Department.objects.create(name='Engineering')
    product = Department.objects.create(name='Product')
    Department.objects.create(name='Backend', parent=engineering)

    response = api_client.post(
        '/api/departments/',
        {'name': 'Backend', 'parent': product.id},
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_root_department_name_must_be_unique(api_client):
    Department.objects.create(name='Engineering')

    response = api_client.post(
        '/api/departments/',
        {'name': 'Engineering', 'parent': None},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_employee_in_department(api_client):
    department = Department.objects.create(name='Engineering')

    response = api_client.post(
        f'/api/departments/{department.id}/employees/',
        {
            'full_name': 'Ivan Petrov',
            'position': 'Developer',
            'hired_at': '2026-05-21',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['full_name'] == 'Ivan Petrov'
    assert response.data['department'] == department.id
    assert Employee.objects.count() == 1


@pytest.mark.django_db
def test_create_employee_rejects_blank_full_name(api_client):
    department = Department.objects.create(name='Engineering')

    response = api_client.post(
        f'/api/departments/{department.id}/employees/',
        {
            'full_name': '   ',
            'position': 'Developer',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Employee.objects.count() == 0


@pytest.mark.django_db
def test_create_employee_rejects_blank_position(api_client):
    department = Department.objects.create(name='Engineering')

    response = api_client.post(
        f'/api/departments/{department.id}/employees/',
        {
            'full_name': 'Ivan Petrov',
            'position': '   ',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Employee.objects.count() == 0


@pytest.mark.django_db
def test_create_employee_in_missing_department_returns_404(api_client):
    response = api_client.post(
        '/api/departments/999/employees/',
        {
            'full_name': 'Ivan Petrov',
            'position': 'Developer',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_department_tree_with_employees_and_children(api_client):
    root = Department.objects.create(name='Engineering')
    backend = Department.objects.create(name='Backend', parent=root)
    Department.objects.create(name='Platform', parent=backend)
    Employee.objects.create(
        department=root,
        full_name='Ivan Petrov',
        position='Developer',
    )

    response = api_client.get(
        f'/api/departments/{root.id}/?depth=2&include_employees=true'
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data['department']['name'] == 'Engineering'
    assert len(response.data['employees']) == 1
    assert len(response.data['children']) == 1
    assert response.data['children'][0]['name'] == 'Backend'
    assert response.data['children'][0]['children'][0]['name'] == 'Platform'


@pytest.mark.django_db
def test_get_department_tree_without_employees(api_client):
    department = Department.objects.create(name='Engineering')
    Employee.objects.create(
        department=department,
        full_name='Ivan Petrov',
        position='Developer',
    )

    response = api_client.get(
        f'/api/departments/{department.id}/?include_employees=false'
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data['employees'] == []


@pytest.mark.django_db
def test_cannot_move_department_inside_own_subtree(api_client):
    root = Department.objects.create(name='Engineering')
    backend = Department.objects.create(name='Backend', parent=root)

    response = api_client.patch(
        f'/api/departments/{root.id}/',
        {'parent': backend.id},
        format='json',
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    root.refresh_from_db()
    assert root.parent is None


@pytest.mark.django_db
def test_cannot_make_department_parent_of_itself(api_client):
    department = Department.objects.create(name='Engineering')

    response = api_client.patch(
        f'/api/departments/{department.id}/',
        {'parent': department.id},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_delete_department_cascade(api_client):
    root = Department.objects.create(name='Engineering')
    child = Department.objects.create(name='Backend', parent=root)
    Employee.objects.create(
        department=child,
        full_name='Ivan Petrov',
        position='Developer',
    )

    response = api_client.delete(f'/api/departments/{root.id}/?mode=cascade')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Department.objects.count() == 0
    assert Employee.objects.count() == 0


@pytest.mark.django_db
def test_delete_department_reassigns_employees(api_client):
    source = Department.objects.create(name='Engineering')
    child = Department.objects.create(name='Backend', parent=source)
    target = Department.objects.create(name='HR')
    employee = Employee.objects.create(
        department=child,
        full_name='Ivan Petrov',
        position='Developer',
    )

    response = api_client.delete(
        f'/api/departments/{source.id}/'
        f'?mode=reassign&reassign_to_department_id={target.id}'
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    employee.refresh_from_db()
    assert employee.department == target
    assert not Department.objects.filter(id=source.id).exists()
    assert not Department.objects.filter(id=child.id).exists()
