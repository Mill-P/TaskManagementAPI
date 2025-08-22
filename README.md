# Task Management API

A RESTful API built with FastAPI for managing tasks with intelligent suggestions based on task patterns.

## Features

- **Complete CRUD Operations**: Create, read, update, and delete tasks
- **Advanced Filtering**: Filter tasks by status, due date ranges
- **Flexible Sorting**: Sort by creation date or due date in ascending/descending order
- **Smart Suggestions**: Smart task suggestions based on existing task patterns
- **Data Validation**: Comprehensive input validation and error handling

## Quick Start

### Installation

1. Clone or download the project files
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
fastapi dev main.py
```

4. Access the API:
   - **API Docs (Swagger UI)**: http://localhost:8000/docs
   - **Alternative Docs**: http://localhost:8000/redoc
   - **API Base URL**: http://localhost:8000

## API Endpoints

### Tasks Management

#### 1. Create Task

```http
POST /tasks/
Content-Type: application/json

{
    "title": "Complete project documentation",
    "description": "Write comprehensive API documentation",
    "due_date": "2025-12-31T23:59:59",
    "status": "pending"
}
```

**Response:**

```json
{
  "id": 1,
  "title": "Complete project documentation",
  "description": "Write comprehensive API documentation",
  "due_date": "2025-12-31T23:59:59",
  "status": "pending",
  "creation_date": "2025-05-25T22:05:50",
  "modified_date": "2025-05-25T22:05:50"
}
```

#### 2. Get All Tasks (with filtering and sorting)

```http
GET /tasks/?status=pending&sort_by=due_date&sort_order=asc
```

**Query Parameters:**

- `status`: Filter by status (`pending`, `in_progress`, `completed`)
- `due_date_from`: Filter tasks due from this date (YYYY-MM-DD)
- `due_date_to`: Filter tasks due until this date (YYYY-MM-DD)
- `sort_by`: Sort field (`creation_date`, `due_date`)
- `sort_order`: Sort direction (`asc`, `desc`)

**Response:**

```json
[
  {
    "id": 1,
    "title": "Complete project documentation",
    "description": "Write comprehensive API documentation",
    "creation_date": "2025-05-24T10:30:00",
    "due_date": "2025-12-31T23:59:59",
    "status": "pending"
  }
]
```

#### 3. Get Single Task

```http
GET /tasks/1
```

**Response:**

```json
{
  "id": 1,
  "title": "Complete project documentation",
  "description": "Write comprehensive API documentation",
  "due_date": "2025-12-31T23:59:59",
  "status": "pending",
  "creation_date": "2025-05-24T10:30:00",
  "modified_date": "2025-05-24T10:30:00"
}
```

#### 4. Update Task

```http
PUT /tasks/1
Content-Type: application/json

{
    "status": "in_progress",
    "description": "Updated description"
}
```

#### 5. Delete Task

```http
DELETE /tasks/1
```

**Response:**

```json
{
  "message": "Task with id: 1 deleted successfully"
}
```

### Smart Features

#### 6. Get Smart Task Suggestions

```http
GET /tasks/suggestions/smart
```

**Response:**

```json
[
  {
    "suggested_title": "Project Review Meeting"
  },
  {
    "suggested_title": "Documentation Follow-up"
  }
]
```

#### 7. Get Task Statistics

```http
GET /tasks/statistics/overview
```

**Response:**

```json
{
  "total_tasks": 25,
  "pending_tasks": 8,
  "in_progress_tasks": 5,
  "completed_tasks": 12,
  "tasks_due_soon": 3,
  "completion_rate": 0.48
}
```

## Task Model

### Fields

- **id**: Unique identifier (auto-generated)
- **title**: Task title (required, max 200 characters)
- **description**: Task description (optional, max 1000 characters)
- **due_date**: Optional due date (must be in the future)
- **status**: Task status with predefined values
- **creation_date**: Automatically set when task is created
- **modified_date**: Automatically updated when task is modified

### Status Options

- `pending`: Task is created but not started
- `in_progress`: Task is being worked on
- `completed`: Task is finished

## Error Handling

The API provides comprehensive error responses:

### Common Error Codes

- **400 Bad Request**: Invalid input data or validation errors
- **404 Not Found**: Task not found
- **422 Unprocessable Entity**: Request data validation failed

### Error Response Format

```json
{
  "detail": "Task not found"
}
```

## Data Validation

### Input Validation Rules

- Task titles must be 1-200 characters
- Descriptions are limited to 1000 characters
- Due dates must be in the future
- Status values are restricted to predefined enums

### Automatic Data Handling

- Creation dates are automatically set
- Default status is "pending"
- SQL injection protection through SQLAlchemy ORM

## Database

- **Engine**: SQLite (tasks.db)
- **ORM**: SQLAlchemy
- **Auto-creation**: Database and tables are created automatically on first run

## Development Features

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API testing
  - Request/response examples
  - Model schemas

### Logging and Monitoring

- Built-in FastAPI request/response logging
- Database session management
- Error tracking and reporting

## Architecture

### Key Components

- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation and serialization
- **SQLite**: Lightweight database


hi
