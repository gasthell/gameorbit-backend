import os
import sys
import socket
import platform
import psutil
from fastapi import FastAPI
from importlib.util import find_spec
from fastapi.middleware.cors import CORSMiddleware

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gameorbit.settings')
import django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth.models import User
from fastapi_app.routes.payment_routes import router as payment_router
from fastapi_app.routes.auth_routes import router as auth_router
from fastapi_app.routes.game_routes import router as game_router
from fastapi_app.routes.info_routes import router as info_router
from django.db import connections, OperationalError
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameorbit.settings")

from gameorbit.wsgi import application

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://gameorbit.kz"],  # or ["*"] for all origins (not recommended for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/mkjffkxgxd/static", StaticFiles(directory=os.path.abspath("../app/staticfiles"), html=True), name="static")
app.mount("/mkjffkxgxd", WSGIMiddleware(application))
app.mount("/images/images/images", StaticFiles(directory=os.path.abspath("../app/images")), name="images")
app.mount("/images/images", StaticFiles(directory=os.path.abspath("../app/images")), name="images")
app.mount("/images", StaticFiles(directory=os.path.abspath("../app/images")), name="images")

app.include_router(payment_router, prefix="/email", tags=["users"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(game_router, prefix="/game", tags=["game"])
app.include_router(info_router, prefix="/info", tags=["info"])

@app.get("/")
def root():
    return {"detail":"Not Found"}

@app.get("/health", tags=["health"])
def health_check():
    health = {"status": "ok"}
    # DB check
    try:
        db_conn = connections['default']
        db_conn.cursor()
        health["db"] = "connected"
    except OperationalError:
        health["db"] = "disconnected"
        health["status"] = "error"
    # Hostname
    health["hostname"] = socket.gethostname()
    # OS info
    health["os"] = platform.system()
    health["os_version"] = platform.version()
    # Memory usage
    mem = psutil.virtual_memory()
    health["memory_total_mb"] = round(mem.total / 1024 / 1024, 2)
    health["memory_used_mb"] = round(mem.used / 1024 / 1024, 2)
    health["memory_percent"] = mem.percent
    # CPU usage
    health["cpu_percent"] = psutil.cpu_percent(interval=0.1)
    return health
