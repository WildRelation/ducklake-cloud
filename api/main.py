import os
import secrets
import tempfile
from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from database import get_conn, init_db

API_KEY = os.getenv("API_KEY", "change-me")

app = FastAPI(title="DuckLake Cloud API")


def verify_key(x_api_key: str = Header(...)):
    if not secrets.compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(status_code=401, detail="Ogiltig API-nyckel")


@app.on_event("startup")
def startup():
    init_db()
    con = get_conn()
    if con.execute("SELECT COUNT(*) FROM lake.kunder").fetchone()[0] == 0:
        con.executemany("INSERT INTO lake.kunder VALUES (?, ?, ?, ?)", [
            (1, "Anna Svensson",   "anna@example.com",  "070-1234567"),
            (2, "Erik Johansson",  "erik@example.com",  "073-9876543"),
            (3, "Maria Lindqvist", "maria@example.com", "076-5551234"),
        ])
        con.executemany("INSERT INTO lake.produkter VALUES (?, ?, ?, ?)", [
            (1, "Laptop",      9999.0, 15),
            (2, "Hörlurar",     799.0, 50),
            (3, "Tangentbord", 1299.0, 30),
        ])
        con.executemany("INSERT INTO lake.ordrar (id, kund_id, produkt_id, antal) VALUES (?, ?, ?, ?)", [
            (1, 1, 1, 1), (2, 1, 2, 2), (3, 2, 3, 1),
        ])
    con.close()


# ── MODELS ────────────────────────────────────────────────────────────────────

class NyKund(BaseModel):
    namn: str
    email: str
    telefon: Optional[str] = None

class NyProdukt(BaseModel):
    namn: str
    pris: float
    lagersaldo: Optional[int] = 0

class NyOrder(BaseModel):
    kund_id: int
    produkt_id: int
    antal: int


# ── KUNDER ────────────────────────────────────────────────────────────────────

@app.get("/api/kunder")
def get_kunder():
    con = get_conn()
    rows = con.execute("SELECT id, namn, email, telefon FROM lake.kunder ORDER BY id").fetchall()
    con.close()
    return [{"id": r[0], "namn": r[1], "email": r[2], "telefon": r[3]} for r in rows]


@app.post("/api/kunder", status_code=201, dependencies=[Depends(verify_key)])
def ny_kund(kund: NyKund):
    con = get_conn()
    nid = con.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM lake.kunder").fetchone()[0]
    con.execute("INSERT INTO lake.kunder VALUES (?, ?, ?, ?)", [nid, kund.namn, kund.email, kund.telefon])
    con.close()
    return {"id": nid, "namn": kund.namn, "email": kund.email}


@app.delete("/api/kunder/{kund_id}", dependencies=[Depends(verify_key)])
def radera_kund(kund_id: int):
    con = get_conn()
    con.execute("DELETE FROM lake.kunder WHERE id = ?", [kund_id])
    con.close()
    return {"deleted": kund_id}


# ── PRODUKTER ─────────────────────────────────────────────────────────────────

@app.get("/api/produkter")
def get_produkter():
    con = get_conn()
    rows = con.execute("SELECT id, namn, pris, lagersaldo FROM lake.produkter ORDER BY id").fetchall()
    con.close()
    return [{"id": r[0], "namn": r[1], "pris": r[2], "lagersaldo": r[3]} for r in rows]


@app.post("/api/produkter", status_code=201, dependencies=[Depends(verify_key)])
def ny_produkt(produkt: NyProdukt):
    con = get_conn()
    nid = con.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM lake.produkter").fetchone()[0]
    con.execute("INSERT INTO lake.produkter VALUES (?, ?, ?, ?)", [nid, produkt.namn, produkt.pris, produkt.lagersaldo])
    con.close()
    return {"id": nid, "namn": produkt.namn, "pris": produkt.pris}


@app.delete("/api/produkter/{produkt_id}", dependencies=[Depends(verify_key)])
def radera_produkt(produkt_id: int):
    con = get_conn()
    con.execute("DELETE FROM lake.produkter WHERE id = ?", [produkt_id])
    con.close()
    return {"deleted": produkt_id}


# ── ORDRAR ────────────────────────────────────────────────────────────────────

@app.get("/api/ordrar")
def get_ordrar():
    con = get_conn()
    rows = con.execute("""
        SELECT o.id, k.namn, p.namn, o.antal, o.skapad
        FROM lake.ordrar o
        JOIN lake.kunder k    ON k.id = o.kund_id
        JOIN lake.produkter p ON p.id = o.produkt_id
        ORDER BY o.id
    """).fetchall()
    con.close()
    return [{"id": r[0], "kund": r[1], "produkt": r[2], "antal": r[3], "skapad": str(r[4])} for r in rows]


@app.post("/api/ordrar", status_code=201, dependencies=[Depends(verify_key)])
def ny_order(order: NyOrder):
    con = get_conn()
    nid = con.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM lake.ordrar").fetchone()[0]
    con.execute("INSERT INTO lake.ordrar (id, kund_id, produkt_id, antal) VALUES (?, ?, ?, ?)",
                [nid, order.kund_id, order.produkt_id, order.antal])
    con.close()
    return {"id": nid, "kund_id": order.kund_id, "produkt_id": order.produkt_id, "antal": order.antal}


# ── DATASETS ──────────────────────────────────────────────────────────────────

@app.get("/api/datasets")
def lista_datasets():
    con = get_conn()
    tabeller = con.execute("SELECT table_name FROM duckdb_tables() WHERE database_name = 'lake'").fetchall()
    con.close()
    return [{"namn": r[0]} for r in tabeller]


@app.get("/api/datasets/{namn}")
def hamta_dataset(namn: str, limit: int = 100):
    con = get_conn()
    tabeller = [r[0] for r in con.execute("SELECT table_name FROM duckdb_tables() WHERE database_name = 'lake'").fetchall()]
    if namn not in tabeller:
        con.close()
        raise HTTPException(status_code=404, detail=f"Dataset '{namn}' hittades inte")
    rows = con.execute(f"SELECT * FROM lake.{namn} LIMIT {limit}").fetchall()
    kolumner = [desc[0] for desc in con.description]
    con.close()
    return {"namn": namn, "kolumner": kolumner, "data": [dict(zip(kolumner, r)) for r in rows]}


@app.post("/api/datasets/upload", status_code=201, dependencies=[Depends(verify_key)])
async def ladda_upp(fil: UploadFile = File(...), tabellnamn: str = Form(...)):
    if not tabellnamn.isidentifier():
        raise HTTPException(status_code=400, detail="Ogiltigt tabellnamn")
    suffix = ".csv" if fil.filename.endswith(".csv") else ".parquet"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await fil.read())
        tmp_path = tmp.name
    try:
        con = get_conn()
        if suffix == ".csv":
            con.execute(f"CREATE TABLE lake.{tabellnamn} AS SELECT * FROM read_csv_auto(?)", [tmp_path])
        else:
            con.execute(f"CREATE TABLE lake.{tabellnamn} AS SELECT * FROM read_parquet(?)", [tmp_path])
        con.close()
    finally:
        os.unlink(tmp_path)
    return {"namn": tabellnamn, "status": "skapad"}


# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.get("/healthz")
def health():
    return {"status": "ok"}
