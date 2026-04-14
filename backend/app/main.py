import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.v1 import tasks, admin, prompts, license, providers, user, session
from app.db.database import engine, Base
from app.db.migrations import apply_startup_migrations
from app.core.config import STATIC_DIR, GENERATED_IMAGES_DIR, CORS_ORIGINS

app = FastAPI(
    title="欧美内衣AI生图平台 API",
    description="SaaS 平台的后端核心 API",
    version="3.0.0",
)


@app.on_event("startup")
async def init_db():
    """启动时创建数据库表、补齐轻量迁移并准备静态目录"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await apply_startup_migrations(conn)
    os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(tasks.router)
app.include_router(admin.router)
app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["提示词策略"])
app.include_router(license.router)
app.include_router(providers.router)
app.include_router(user.router)
app.include_router(session.router)


@app.get("/")
def read_root():
    if os.path.isfile(SPA_INDEX):
        return FileResponse(SPA_INDEX)
    return {"message": "Welcome to Lingerie AI API v3.0"}


@app.get("/api/v1/download/{filename:path}")
async def download_file(filename: str):
    safe_name = os.path.basename(filename)
    filepath = os.path.join(GENERATED_IMAGES_DIR, safe_name)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        filepath,
        filename=safe_name,
        media_type="application/octet-stream",
    )


SPA_INDEX = os.path.join(STATIC_DIR, "index.html")
if os.path.isfile(SPA_INDEX):
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(SPA_INDEX)
