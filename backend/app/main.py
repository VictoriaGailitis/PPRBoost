import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.ping.router import router as ping_router
from api.auth.router import auth as auth_router
from api.chat.router import chat as chat_router
from api.rating.router import rating as rating_router
from api.streaming.router import router as streaming_router
from api.system_prompt.router import system_prompt as system_prompt_router

from core.database import Base, engine
from dotenv import load_dotenv

load_dotenv()

#* Инициализация базы данных
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API",
    root_path="/api"
)

app.mount("/data", StaticFiles(directory="data"), name="data")

origins = os.getenv("ORIGINS").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#* ROUTERS
app.include_router(ping_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(rating_router)
app.include_router(streaming_router)
app.include_router(system_prompt_router)