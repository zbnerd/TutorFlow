# TutorFlow Backend

FastAPI backend for TutorFlow AI platform.

## Architecture

Clean Architecture with 4 layers:
- **domain/**: Business entities and ports
- **application/**: Use cases and DTOs
- **infrastructure/**: Database, external APIs
- **api/**: FastAPI route handlers

## Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:
```bash
python -m alembic upgrade head
```

4. Start development server:
```bash
python main.py
```

## Running Tests

```bash
pytest
```

## API Documentation

When running in development mode:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
