# Quick Deployment Guide

## Prerequisites

- Python 3.8+
- PostgreSQL 12+ (or SQLite for development)
- Redis 6.0+ (optional, for production)
- Google AI API credentials

## Local Development Setup

1. **Clone and Setup Environment**
```bash
cd ai_test_case_generator
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment Variables**
Create `.env` file:
```bash
# Database (SQLite for development)
DATABASE_URL=sqlite:///app.db

# Google AI Configuration
GOOGLE_AI_API_KEY=your_api_key_here
GOOGLE_AI_PROJECT_ID=your_project_id_here

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# Application
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5001
```

3. **Initialize Database**
```bash
python src/manage.py db init
python src/manage.py db migrate
python src/manage.py db upgrade
```

4. **Start Application**
```bash
python src/main.py
```

Access the application at http://localhost:5001

## Docker Deployment

1. **Build and Run with Docker Compose**
```bash
docker-compose up -d
```

2. **Initialize Database in Container**
```bash
docker-compose exec web python src/manage.py db upgrade
```

## Production Deployment

1. **Update Environment Variables**
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/0
FLASK_ENV=production
FLASK_DEBUG=False
```

2. **Install Production Dependencies**
```bash
pip install gunicorn psycopg2-binary
```

3. **Run with Gunicorn**
```bash
gunicorn --bind 0.0.0.0:5001 --workers 4 src.main:app
```

## Health Check

Verify deployment:
```bash
curl http://localhost:5001/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-20T17:00:00Z",
  "version": "1.0.0"
}
```

## Troubleshooting

- **Database Connection Issues**: Check DATABASE_URL and ensure database server is running
- **AI Service Errors**: Verify GOOGLE_AI_API_KEY is valid and has appropriate permissions
- **Port Conflicts**: Change PORT environment variable if 5001 is in use
- **Permission Errors**: Ensure application user has read/write access to required directories

For detailed documentation, see README.md

