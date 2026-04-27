from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_conn, init_db, ensure_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bucket()
    init_db()
    yield


app = FastAPI(title="DuckLake API", lifespan=lifespan)


class NewCustomer(BaseModel):
    name: str
    email: str


@app.get("/customers")
def get_customers():
    with get_conn() as con:
        rows = con.execute(
            "SELECT id, name, email FROM my_lake.customers ORDER BY id"
        ).fetchall()
    return [{"id": r[0], "name": r[1], "email": r[2]} for r in rows]


@app.post("/customers", status_code=201)
def create_customer(customer: NewCustomer):
    with get_conn() as con:
        new_id = con.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM my_lake.customers"
        ).fetchone()[0]
        con.execute(
            "INSERT INTO my_lake.customers VALUES (?, ?, ?)",
            [new_id, customer.name, customer.email]
        )
    return {"id": new_id, "name": customer.name, "email": customer.email}


@app.put("/customers/{customer_id}")
def update_customer(customer_id: int, customer: NewCustomer):
    with get_conn() as con:
        affected = con.execute(
            "SELECT COUNT(*) FROM my_lake.customers WHERE id = ?", [customer_id]
        ).fetchone()[0]
        if affected == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        con.execute(
            "UPDATE my_lake.customers SET name = ?, email = ? WHERE id = ?",
            [customer.name, customer.email, customer_id]
        )
    return {"id": customer_id, "name": customer.name, "email": customer.email}


@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int):
    with get_conn() as con:
        con.execute("DELETE FROM my_lake.customers WHERE id = ?", [customer_id])
    return {"deleted": customer_id}


@app.get("/healthz")
def health():
    return {"status": "ok"}
