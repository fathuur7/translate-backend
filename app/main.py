from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import translate_router
# from app.routers import auth_routes

app = FastAPI(
    title="Video Subtitle and Translation API",
    description="API untuk mentranskripsi dan menerjemahkan video menjadi file subtitle (.srt).",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)


app.include_router(translate_router.router)
# app.include_router(auth_routes.auth_router)


# Mount static folder supaya file yang disimpan lokal dapat diakses
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", tags=["General"])
def read_root():
    return {
        "message": "Selamat datang di Video Translator API. Kunjungi /docs untuk dokumentasi interaktif."
    }
