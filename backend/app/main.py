from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil

app = FastAPI(title="Multi-Agent File Editor")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Путь для хранения файлов
FILES_DIR = "/app/files"
os.makedirs(FILES_DIR, exist_ok=True)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Multi-Agent File Editor API",
        "version": "0.1.0"
    }


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Загрузка до 50 файлов.
    Каждый файл сохраняется в /app/files/
    """
    if len(files) > 50:
        return {"error": "Maximum 50 files allowed"}
    
    uploaded = []
    for file in files:
        file_path = os.path.join(FILES_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded.append({
            "filename": file.filename,
            "size": os.path.getsize(file_path)
        })
    
    return {
        "status": "success",
        "uploaded_count": len(uploaded),
        "files": uploaded
    }


@app.get("/files")
async def list_files():
    """
    Список всех загруженных файлов
    """
    files = []
    if os.path.exists(FILES_DIR):
        for filename in os.listdir(FILES_DIR):
            file_path = os.path.join(FILES_DIR, filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(file_path)
                })
    
    return {
        "count": len(files),
        "files": files
    }


# TODO: добавить WebSocket для агентов
# TODO: интеграция LangGraph для multi-agent системы
