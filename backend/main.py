import json
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import random
import shutil
import asyncio
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

app = FastAPI()
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ===== Структура товару =====
class Product(BaseModel):
    id: str
    name: str
    price_per_kg: float
    image_path: str

# ===== JSON файл =====
PRODUCTS_FILE = "products.json"
USERS_FILE = "users.json"

def read_data():
    if not os.path.exists(PRODUCTS_FILE):
        return {"products": []}
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ===== Папка для фото =====
IMAGE_DIR = "product_images"
os.makedirs(IMAGE_DIR, exist_ok=True)
app.mount("/product_images", StaticFiles(directory=IMAGE_DIR), name="product_images")

# ===== SSE =====
listeners: List[asyncio.Queue] = []

@app.get("/products/updates")
async def products_updates(request: Request):
    async def event_generator():
        queue = asyncio.Queue()
        listeners.append(queue)
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
        finally:
            listeners.remove(queue)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

def notify_listeners():
    data = read_data()["products"]
    for queue in listeners:
        queue.put_nowait(data)

# ===== CRUD =====
@app.get("/products", response_model=List[Product])
def get_products():
    data = read_data()
    return [
        Product(
            id=p["id"],
            name=p["name"],
            price_per_kg=p["price_per_kg"],
            image_path=f"/product_images/{p['image_path']}"
        )
        for p in data["products"]
    ]

@app.post("/products")
def create_product(name: str = Form(...), price_per_kg: float = Form(...), image: UploadFile = File(...)):
    data = read_data()
    product_id = str(random.randint(1, 999999))
    ext = os.path.splitext(image.filename)[1]
    image_filename = f"{product_id}{ext}"
    with open(os.path.join(IMAGE_DIR, image_filename), "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    product = {"id": product_id, "name": name, "price_per_kg": price_per_kg, "image_path": image_filename}
    data["products"].append(product)
    save_data(data)
    notify_listeners()
    return product

@app.put("/products/{product_id}")
def update_product(product_id: str, name: str = Form(...), price_per_kg: float = Form(...), image: UploadFile = File(None)):
    data = read_data()
    product = next((p for p in data["products"] if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product["name"] = name
    product["price_per_kg"] = price_per_kg
    if image:
        ext = os.path.splitext(image.filename)[1]
        image_filename = f"{product_id}{ext}"
        with open(os.path.join(IMAGE_DIR, image_filename), "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        product["image_path"] = image_filename
    save_data(data)
    notify_listeners()
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    data = read_data()
    before_count = len(data["products"])
    data["products"] = [p for p in data["products"] if p["id"] != product_id]
    if len(data["products"]) == before_count:
        raise HTTPException(status_code=404, detail="Product not found")
    save_data(data)
    notify_listeners()
    return {"detail": "Deleted"}

@app.get("/products/images/{image_name}")
def get_image(image_name: str):
    path = os.path.join(IMAGE_DIR, image_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)

@app.get("/status")
def get_status():
    try:
        data = read_data()
        count = len(data.get("products", []))
        return JSONResponse({"status_code": 200, "status": "OK", "products_count": count})
    except Exception as e:
        return JSONResponse({"status_code": 500, "status": f"Server Error: {str(e)}", "products_count": 0})
