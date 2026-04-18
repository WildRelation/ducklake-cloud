# Modul 04 — Python API

## Hur Python ansluter till DuckLake

```
HTTP-anrop → FastAPI → duckdb-bibliotek → DuckLake (PostgreSQL + MinIO)
```

Python ansluter **direkt** till DuckLake inuti samma process — ingen separat DuckDB-server behövs.

---

## Filstruktur

```
api/
├── main.py        ← HTTP-endpoints (vad som händer vid varje anrop)
├── database.py    ← Anslutning till DuckLake
└── requirements.txt
```

### database.py — ansvar

Hanterar **allt** som har med DuckLake-anslutningen att göra:

1. Läser miljövariabler (host, lösenord etc.)
2. Skapar DuckDB-anslutning
3. Laddar extensions (ducklake, postgres, httpfs)
4. Skapar secrets för PostgreSQL och MinIO
5. Kopplar ihop katalogen med lagringen via `ATTACH`
6. Skapar tabeller om de inte finns (`init_db`)

```python
def get_conn():
    con = duckdb.connect()          # Ny in-memory DuckDB
    con.execute("LOAD ducklake")    # Ladda DuckLake-extension
    con.execute("LOAD postgres")    # Ladda PostgreSQL-extension

    # Säg åt DuckDB hur det ansluter till PostgreSQL
    con.execute("CREATE OR REPLACE SECRET (...)")

    # Koppla ihop katalog och lagring
    con.execute("ATTACH 'ducklake:postgres:dbname=...' AS lake (...)")

    return con
```

**Viktigt:** Varje HTTP-anrop skapar en ny connection och stänger den efteråt.

### main.py — ansvar

Hanterar **HTTP-anropen**:

1. Tar emot GET/POST/DELETE
2. Verifierar API-nyckel för skrivoperationer
3. Kör SQL via `get_conn()`
4. Returnerar JSON

```python
@app.get("/api/kunder")          # GET-endpoint
def get_kunder():
    with get_conn() as con:      # Öppna anslutning — stängs automatiskt
        rows = con.execute("SELECT * FROM lake.kunder").fetchall()
    return rows                  # Returnera JSON
```

> `with get_conn() as con:` garanterar att anslutningen stängs även om ett fel uppstår — detta kallas context manager och är ett säkrare mönster än `con.close()`.

---

## FastAPI

FastAPI är ett Python-ramverk för att bygga REST API:er snabbt.

### Varför FastAPI?

- Automatisk API-dokumentation på `/docs`
- Inbyggd validering av indata
- Asynkront — hanterar många anrop samtidigt
- Enkelt att lära sig

### Endpoint-typer

```python
@app.get("/api/kunder")                           # Hämta
@app.post("/api/kunder", status_code=201)         # Skapa
@app.delete("/api/kunder/{id}")                   # Radera
```

### Skydda endpoints med API-nyckel

```python
def verify_key(x_api_key: str = Header(...)):
    if not secrets.compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(status_code=401)

# Lägg till dependencies=[Depends(verify_key)] på skyddade endpoints
@app.post("/api/kunder", dependencies=[Depends(verify_key)])
```

---

## Skapa en ny tabell och endpoint

### Steg 1 — Definiera tabellen i database.py

```python
def init_db():
    con = get_conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS lake.min_tabell (
            id      INTEGER,
            namn    VARCHAR NOT NULL,
            värde   DOUBLE
        )
    """)
    con.close()
```

### Steg 2 — Skapa endpoints i main.py

```python
class NyRad(BaseModel):
    namn: str
    värde: float

@app.get("/api/min_tabell")
def get_rader():
    with get_conn() as con:
        rows = con.execute("SELECT id, namn, värde FROM lake.min_tabell").fetchall()
    return [{"id": r[0], "namn": r[1], "värde": r[2]} for r in rows]

@app.post("/api/min_tabell", status_code=201, dependencies=[Depends(verify_key)])
def ny_rad(rad: NyRad):
    with get_conn() as con:
        nid = con.execute("SELECT COALESCE(MAX(id),0)+1 FROM lake.min_tabell").fetchone()[0]
        con.execute("INSERT INTO lake.min_tabell VALUES (?,?,?)", [nid, rad.namn, rad.värde])
    return {"id": nid, "namn": rad.namn}
```

---

## requirements.txt

```
fastapi==0.136.0      # Webbramverket
uvicorn==0.44.0       # ASGI-server som kör FastAPI
duckdb==1.5.2         # DuckDB-biblioteket
minio==7.2.15         # MinIO-klient (för att skapa buckets)
python-multipart==0.0.20  # Krävs för formulärdata
```

---

➡️ [Gå till läxor för modul 04](laxor/04-laxor.md)
