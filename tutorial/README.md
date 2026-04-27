# Tutorial — DuckLake Locally with Python API

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

---

## Getting the files

Clone the repository and navigate to the tutorial folder:

```bash
git clone https://github.com/wildrelation/ducklake-cloud.git
cd ducklake-cloud/tutorial
```

---

## Part 1 — Set Up DuckLake Locally

### Step 1 — Start the services

Run the following command inside the `tutorial/` folder:

```bash
docker compose up -d
```

This starts three services:

| Service | Purpose | Port |
|---------|---------|------|
| PostgreSQL | DuckLake catalog (metadata) | 5432 |
| MinIO | Parquet storage (S3) | 9000 / 9001 |
| mc | Creates the bucket automatically | — |

The MinIO console is available at `http://localhost:9001` (user: `ducklake`, password: `minioadmin`).

Wait a few seconds for the services to start before continuing.

---

### Step 2 — Open the DuckDB shell

**Linux/macOS:**

```bash
chmod +x shell.sh
./shell.sh
```

**Windows (PowerShell):**

```powershell
./shell.ps1
```

The DuckDB UI opens in your browser and `setup.sql` runs automatically — you are now connected to your DuckLake.

---

### Step 3 — Verify

Run the following in the DuckDB shell:

```sql
CREATE TABLE test (id INTEGER, message VARCHAR);
INSERT INTO test VALUES (1, 'DuckLake is working!');
SELECT * FROM test;
```

If you see the row, DuckLake is working — metadata is stored in PostgreSQL and data as Parquet files in MinIO.

You can drop the table when you are done:

```sql
DROP TABLE test;
```

Exit the shell with `.exit`.

---

## Part 2 — Python API

Make sure the services from Part 1 are still running (`docker compose up -d`).

### Project structure

All API files are inside the `api/` folder:

```
tutorial/
├── compose.yaml
├── setup.sql
├── shell.sh / shell.ps1
└── api/
    ├── requirements.txt   — Python dependencies
    ├── database.py        — DuckLake connection
    └── main.py            — FastAPI endpoints
```

---

### Step 1 — Create a virtual environment and install dependencies

Navigate to the `api/` folder:

```bash
cd api
```

Create and activate a virtual environment:

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### Step 2 — database.py

This file handles the connection to DuckLake. It connects DuckDB to PostgreSQL (catalog) and MinIO (Parquet storage) using the DuckLake extension.

Open `database.py` and read through it. Key points:

- All configuration is read from environment variables with sensible defaults for local development
- `get_conn()` creates a new DuckDB connection, loads the DuckLake and PostgreSQL extensions, and attaches the lake
- `init_db()` creates the `customers` table if it does not exist yet

> A new DuckDB connection is created for each request. This is intentional — DuckLake uses snapshots and requires a fresh connection to see the latest data.

---

### Step 3 — main.py

Open `main.py` and read through it. It is a FastAPI application with three endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/customers` | Get all customers |
| POST | `/customers` | Create a new customer |
| PUT | `/customers/{id}` | Update a customer |
| DELETE | `/customers/{id}` | Delete a customer |

On startup, the app calls `ensure_bucket()` (creates the MinIO bucket if missing) and `init_db()` (creates the table if missing).

---

### Step 4 — Run the API

```bash
uvicorn main:app --reload
```

The API is now available at `http://localhost:8000`.  
Interactive docs (Swagger UI): `http://localhost:8000/docs`

---

### Step 5 — Test the API

You can use the Swagger UI at `http://localhost:8000/docs` to test all endpoints in the browser.

Or use `curl` from the terminal:

**Get all customers:**

```bash
curl http://localhost:8000/customers
```

**Create a customer:**

Linux/macOS:
```bash
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"name": "Anna", "email": "anna@example.com"}'
```

Windows (PowerShell):
```powershell
curl -X POST http://localhost:8000/customers `
  -H "Content-Type: application/json" `
  -d '{"name": "Anna", "email": "anna@example.com"}'
```

**Update a customer:**

Linux/macOS:
```bash
curl -X PUT http://localhost:8000/customers/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Anna Updated", "email": "anna.updated@example.com"}'
```

Windows (PowerShell):
```powershell
curl -X PUT http://localhost:8000/customers/1 `
  -H "Content-Type: application/json" `
  -d '{"name": "Anna Updated", "email": "anna.updated@example.com"}'
```

**Delete a customer:**

```bash
curl -X DELETE http://localhost:8000/customers/1
```

---

### Step 6 — Stop everything

Stop the API with `Ctrl+C`, then stop the Docker services:

```bash
docker compose down
```

To also delete all stored data:

```bash
docker compose down -v
```
