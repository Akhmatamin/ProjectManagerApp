# Project Manager API

A REST API for collaborative project and document management. The service lets users register, create projects, grant members `read` or `write` access, invite them via links, and store project documents in Amazon S3.

After startup, the interactive API specification is available at [`/docs`](http://127.0.0.1:8000/docs).

## Features

- JWT authentication: registration, login, refresh, and refresh-token revocation;
- password changes and email-code password recovery;
- project creation, retrieval, update, and deletion;
- invitations for existing users and time-limited invitation links;
- member access control with `read` and `write` permissions;
- project document upload, retrieval, replacement, and deletion;
- PostgreSQL for primary data, Redis for temporary data, and S3 for files.

## Tech Stack

- Python 3.12+, FastAPI, and Uvicorn;
- asynchronous SQLAlchemy + asyncpg, PostgreSQL, and Alembic;
- Redis;
- Dishka for dependency injection;
- PyJWT and Argon2 (`pwdlib`) for authentication;
- Amazon S3 (`sqlalchemy-file`, `apache-libcloud`) for file storage;
- Resend for email delivery;
- Docker Compose and Nginx for deployment.

## Architecture

```text
app/
├── auth/        # authentication, refresh tokens, password recovery
├── users/       # user model and data access
├── projects/    # projects, members, permissions, and invitations
├── documents/   # document operations
└── shared/      # configuration, database, Redis, S3, security, and DI
migrations/      # Alembic migrations
nginx/           # reverse-proxy configuration
streamlit/       # invitation helper application
tests/            # auth, project, and document tests
```

## Local Quick Start

### Prerequisites

- Python **3.12** or later;
- [uv](https://docs.astral.sh/uv/);
- an available PostgreSQL instance and Redis instance;
- an Amazon S3 bucket and AWS credentials;
- a [Resend](https://resend.com/) API key for sending email.

### 1. Install dependencies

```bash
uv sync
```

### 2. Create `.env`

Configuration is automatically read from `.env` in the repository root. Use this template and replace placeholder values:

```dotenv
# PostgreSQL
DATABASE_HOST=127.0.0.1
DATABASE_PORT=5432
DATABASE_NAME=project_manager
DATABASE_USER=postgres
DATABASE_PASSWORD=change-me

# JWT
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_LIFETIME=30
REFRESH_TOKEN_LIFETIME=7

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
RESET_CODE_EXPIRE_SECONDS=300

# Email / invitations
RESEND_API_KEY=re_replace_me
RESEND_FROM=onboarding@resend.dev
FRONTEND_BASE_URL=http://localhost:3000
BACKEND_BASE_URL=http://127.0.0.1:8000
INVITE_LINK_EXPIRE_SECONDS=260000

# Amazon S3
AWS_ACCESS_KEY_ID=replace-me
AWS_SECRET_ACCESS_KEY=replace-me
AWS_REGION=eu-north-1
S3_BUCKET_NAME=my-project-bucket-documents
```

> Do not commit `.env`: it contains passwords, the JWT secret, and AWS credentials. In production, use your orchestrator's environment-secret management.

### 3. Apply database migrations

```bash
uv run alembic upgrade head
```

### 4. Start the API

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify that the service is running:

```bash
curl http://127.0.0.1:8000/docs
```

## Run with Docker Compose

`docker-compose.yml` starts the API, Redis, and Nginx images. PostgreSQL is **not included** in the Compose configuration, so prepare an external or local PostgreSQL database that the API container can reach before starting.

1. Create `.env` using the template above.
2. Set `REDIS_HOST=redis`, because Redis is available inside Docker Compose by its service name.
3. Set `DATABASE_HOST` to the address of a PostgreSQL instance reachable from the Docker container.
4. Apply migrations to that database.
5. Start the services:

```bash
docker compose up -d
docker compose ps
```

Nginx exposes the application on port `80`. To view logs:

```bash
docker compose logs -f api
```

## API

All protected endpoints require an access JWT in the following header:

```http
Authorization: Bearer <access_token>
```

Exact request and response models, along with examples, are available in Swagger UI at [`/docs`](http://127.0.0.1:8000/docs).

### Authentication

| Method | Route | Description | Authorization |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | Register a user | — |
| `POST` | `/auth/login` | Log in and receive tokens | — |
| `POST` | `/auth/logout` | Revoke a refresh token | — |
| `POST` | `/auth/refresh` | Refresh the token pair | — |
| `PUT` | `/auth/change_password` | Change the password | JWT |
| `POST` | `/auth/forgot_password` | Request a recovery code | — |
| `POST` | `/auth/reset_password` | Reset a password using a code | — |

### Projects and Members

| Method | Route | Description | Authorization |
| --- | --- | --- | --- |
| `POST` | `/projects/` | Create a project | JWT |
| `GET` | `/projects/` | List projects available to the user | JWT |
| `GET` | `/project/{project_id}/info` | Get project details | JWT |
| `PUT` | `/project/{project_id}/info` | Update project details | JWT |
| `DELETE` | `/project/{project_id}` | Delete a project | JWT |
| `POST` | `/project/{project_id}/invite` | Invite a user; `user` and `permission` are query parameters | JWT |
| `GET` | `/project/{project_id}/share` | Get an invitation link; `email` and `permission` are query parameters | JWT |
| `POST` | `/project/join` | Join a project using the `token` query parameter | JWT |

### Documents

| Method | Route | Description | Authorization |
| --- | --- | --- | --- |
| `POST` | `/project/{project_id}/documents` | Upload a file (`multipart/form-data`, `file` field) | JWT |
| `GET` | `/project/{project_id}/documents` | List project documents | JWT |
| `GET` | `/document/{document_id}` | Download a document; supports `is_resized` | JWT |
| `PUT` | `/document/{document_id}` | Replace a file (`multipart/form-data`, `file` field) | JWT |
| `DELETE` | `/document/{document_id}` | Delete a document | JWT |

## Data and External Services

| Component | Purpose |
| --- | --- |
| PostgreSQL | Users, projects, members, documents, and refresh tokens |
| Redis | Refresh tokens and password-recovery codes |
| Amazon S3 | Document files |
| Resend | Password recovery and invitation emails |

The S3 storage is initialized when the application starts. The AWS identity must have permissions to work with the configured bucket.

## Migrations

```bash
# Apply all migrations
uv run alembic upgrade head

# Create a migration after changing models
uv run alembic revision --autogenerate -m "describe schema change"

# Roll back the latest migration
uv run alembic downgrade -1
```

Migrations are located in `migrations/versions/`; Alembic configuration is in `alembic.ini`.

## Testing

```bash
# Run all tests
uv run pytest

# Run a specific module
uv run pytest tests/auth/

# Run with verbose output
uv run pytest -v
```

## Security and Production Notes

- Use a unique, long `SECRET_KEY`; never use the example value.
- Do not expose AWS credentials, database passwords, or the Resend API key in the repository or logs.
- Set `FRONTEND_BASE_URL` and `BACKEND_BASE_URL` to actual HTTPS URLs before publishing invitation links.
- CORS currently permits every origin (`allow_origins=["*"]`). Restrict it to trusted domains before production.
- Nginx is configured with a `100M` request-body limit; account for it when uploading files.

## License

No license is currently specified in the repository. Add a `LICENSE` file before distributing the project.

