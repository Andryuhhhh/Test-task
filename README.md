# API организационной структуры

API для управления подразделениями и сотрудниками в древовидной организационной структуре.

## Стек

- Python 3.14
- Django 6
- Django REST Framework
- PostgreSQL
- Docker Compose
- pytest, pytest-django, pytest-cov

## Запуск через Docker

Собрать и запустить приложение:

```bash
docker compose up --build
```

API будет доступно по адресу:

```text
http://localhost:8000/api/
```

Миграции применяются автоматически при запуске контейнера `web`.

## Локальный запуск

Установить зависимости:

```bash
pip install -r requirements.txt
```

Локально должен быть запущен PostgreSQL со следующими настройками:

```text
DB: test_task
USER: postgres
PASSWORD: postgres
HOST: 127.0.0.1
PORT: 5432
```

Применить миграции и запустить сервер:

```bash
python manage.py migrate
python manage.py runserver
```

## API endpoints

Создать подразделение:

```http
POST /api/departments/
```

Получить подразделение с сотрудниками и поддеревом:

```http
GET /api/departments/{id}/?depth=2&include_employees=true
```

Обновить подразделение:

```http
PATCH /api/departments/{id}/
```

Удалить подразделение:

```http
DELETE /api/departments/{id}/?mode=cascade
DELETE /api/departments/{id}/?mode=reassign&reassign_to_department_id={target_id}
```

Создать сотрудника в подразделении:

```http
POST /api/departments/{id}/employees/
```

Примеры запросов находятся в файле `request.http`.

## Валидация

- `name` подразделения обрезается по краям и не может быть пустым.
- Названия подразделений уникальны внутри одного родителя.
- Названия корневых подразделений уникальны.
- `full_name` и `position` сотрудника обрезаются по краям и не могут быть пустыми.
- Подразделение нельзя сделать родителем самого себя.
- Подразделение нельзя переместить внутрь собственного поддерева.

## Тесты

Запустить тесты с coverage:

```bash
python -m pytest
```

Настройки coverage находятся в файле `.coveragerc`.
