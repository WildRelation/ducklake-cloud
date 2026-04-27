# Tutorial — DuckLake lokalt med Python API

## Förutsättningar

- Docker + Docker Compose
- Python 3.10+

---

## Del 1 — Sätt upp DuckLake lokalt

### Steg 1 — Starta tjänsterna

Kör följande kommando i denna mapp:

```bash
docker compose up -d
```

Detta startar tre tjänster:

| Tjänst | Syfte | Port |
|--------|-------|------|
| PostgreSQL | DuckLake-katalog (metadata) | 5432 |
| MinIO | Parquet-lagring (S3) | 9000 / 9001 |
| mc | Skapar bucket automatiskt | — |

MinIO-konsolen når du på `http://localhost:9001` (användare: `ducklake`, lösenord: `minioadmin`).

---

### Steg 2 — Öppna DuckDB-shell

```bash
docker run --rm -it \
  --network host \
  -v $(pwd):/workspace \
  -w /workspace \
  duckdb/duckdb /duckdb -init setup.sql -ui
```

DuckDB UI öppnas i webbläsaren och `setup.sql` körs automatiskt — du är nu ansluten till ditt DuckLake.

---

### Steg 3 — Verifiera

Kör i DuckDB-skalet:

```sql
CREATE TABLE kunder (id INTEGER, namn VARCHAR, email VARCHAR);
INSERT INTO kunder VALUES (1, 'Anna', 'anna@example.com');
SELECT * FROM kunder;
```

Om du ser raden fungerar DuckLake — metadata sparas i PostgreSQL och data som Parquet-filer i MinIO.

---

## Del 2 — Python API

*Kommer snart.*
