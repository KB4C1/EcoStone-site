import os
import json
import random
import shutil
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.hash import bcrypt
from dotenv import load_dotenv

# ====== CONFIG ======
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

# ===== APP INIT ======
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Замінити на фронт у продакшені
    allow_methods=["*"],
    allow_headers=["*"]
)

# ===== FRONTEND =====
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

# ===== AUTH =====
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username != ADMIN_USERNAME:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != ADMIN_USERNAME or not bcrypt.verify(form_data.password, ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": ADMIN_USERNAME}, expires_delta=access_token_expires)
    return {"access_token": token, "token_type": "bearer"}

# ===== PRODUCTS =====
class Product(BaseModel):
    id: str
    name: str
    price_per_kg: float
    image_path: str

PRODUCTS_FILE = "products.json"
IMAGE_DIR = "product_images"
os.makedirs(IMAGE_DIR, exist_ok=True)
app.mount("/product_images", StaticFiles(directory=IMAGE_DIR), name="product_images")

def read_data():
    if not os.path.exists(PRODUCTS_FILE):
        return {"products": []}
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

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
def create_product(
    name: str = Form(...),
    price_per_kg: float = Form(...),
    image: UploadFile = File(...),
    user: str = Depends(get_current_user)
):
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
def update_product(
    product_id: str,
    name: str = Form(...),
    price_per_kg: float = Form(...),
    image: UploadFile = File(None),
    user: str = Depends(get_current_user)
):
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
def delete_product(product_id: str, user: str = Depends(get_current_user)):
    data = read_data()
    before_count = len(data["products"])
    data["products"] = [p for p in data["products"] if p["id"] != product_id]
    if len(data["products"]) == before_count:
        raise HTTPException(status_code=404, detail="Product not found")
    save_data(data)
    notify_listeners()
    return {"detail": "Deleted"}

@app.get("/status")
def get_status():
    try:
        data = read_data()
        return {"status_code": 200, "status": "OK", "products_count": len(data.get("products", []))}
    except Exception as e:
        return {"status_code": 500, "status": f"Server Error: {str(e)}", "products_count": 0}
