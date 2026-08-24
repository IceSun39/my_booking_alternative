# 🏨 Booking System API

A robust, fully containerized backend booking application built with **FastAPI**, **PostgreSQL**, **Celery**, and **Redis**. Designed with asynchronous architecture to handle database operations smoothly and offload heavy background tasks.

---

## 🚀 Key Features

* **Asynchronous REST API:** Built with FastAPI and SQLAlchemy (asyncpg) for high performance and non-blocking I/O.
* **Background Tasks:** Uses **Celery** and **Redis** to asynchronously send beautiful HTML email notifications upon booking confirmation (preventing API latency).
* **Authentication & Authorization:** Secure JWT-based authentication with Role-Based Access Control (`USER`, `ADMIN`, `OWNER`).
* **Database Migrations:** Automated schema management via **Alembic**.
* **Full Docker Support:** Containerized services (`web`, `celery-worker`, `postgres`, `redis`) orchestrated with Docker Compose in an isolated network.
* **Lightning-Fast Tooling:** Powered by `uv` for ultra-fast dependency management.

---

## 🛠 Tech Stack

* **Core:** Python 3.12+ / FastAPI
* **Database:** PostgreSQL 16
* **ORM:** SQLAlchemy 2.0 (Async)
* **Migrations:** Alembic
* **Task Queue / Broker:** Celery & Redis
* **Containerization:** Docker & Docker Compose

---

## 📦 Quick Start with Docker

### Prerequisites
Make sure you have **Docker** and **Docker Compose** installed on your machine. Also, ensure local services (like PostgreSQL or Redis/Valkey) running on your host system are stopped to avoid port conflicts (`5432`, `6379`).

### 1. Clone the repository
```bash
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name
```
### 2. Configure environment variables
Create a .env file in the root directory based on the following template:
```bash
# PostgreSQL Configuration
POSTGRES_USER=vlad
POSTGRES_PASSWORD=supersecret
POSTGRES_DB=booking_db
DATABASE_URL=postgresql+asyncpg://vlad:supersecret@postgres:5432/booking_db

# Redis & Celery Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Email Configuration (Gmail App Password)
EMAIL_PASSWORD=your_google_app_password

# JWT Security
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Build and run containers
```bash
docker compose up --build
```


### 4. Run database migrations
Open a separate terminal window and apply the database migrations inside the running container:
```bash
docker compose exec web uv run alembic upgrade head
```
### 5. Access the API
Open your browser and navigate to:

Interactive API Docs (Swagger UI): http://localhost:8000/docs

Alternative Docs (ReDoc): http://localhost:8000/redoc

### 👥 Managing Admin Users (Optional)
To promote a user to an administrator directly through the database:

1. Register a new user via the Swagger UI (/docs).

2. Access the PostgreSQL container:

```bash
docker compose exec postgres psql -U vlad -d booking_db
```

3. Update the user role:
```bash
UPDATE users SET role = 'ADMIN' WHERE username = 'your_username';
```

4. Exit the database CLI:
```bash
\q
```
### 📄 License
This project is open-source and available under the MIT License.