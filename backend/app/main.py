from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
import json
from .agents import get_agent_system

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
        "version": "0.2.0",
        "features": [
            "File upload (up to 50 files)",
            "Multi-agent file processing with LangGraph",
            "WebSocket for real-time communication",
            "Google Gemini integration"
        ]
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
                # Читаем содержимое файла (только текстовые)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except:
                    content = "[Binary file]"
                
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(file_path),
                    "content": content
                })
    
    return {
        "count": len(files),
        "files": files
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket для реал-тайм коммуникации с multi-agent системой
    
    Пример сообщения:
    {
        "command": "Add TODO comment to file1.txt",
        "files": {
            "file1.txt": "content here",
            "file2.py": "print('hello')"
        }
    }
    """
    await websocket.accept()
    
    # Приветственное сообщение
    await websocket.send_json({
        "type": "connection",
        "message": "Connected to Multi-Agent File Editor",
        "status": "ready"
    })
    
    try:
        # Инициализация multi-agent системы
        try:
            agent_system = get_agent_system()
        except ValueError as e:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "hint": "Set GOOGLE_API_KEY environment variable"
            })
            await websocket.close()
            return
        
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_json()
            
            command = data.get("command", "")
            files = data.get("files", {})
            
            if not command:
                await websocket.send_json({
                    "type": "error",
                    "message": "No command provided"
                })
                continue
            
            # Отправляем статус начала обработки
            await websocket.send_json({
                "type": "processing",
                "message": f"Processing command: {command}",
                "files_count": len(files)
            })
            
            # Обработка команды через multi-agent систему
            try:
                result = agent_system.process_command(command, files)
                
                # Отправляем результат
                await websocket.send_json({
                    "type": "result",
                    "status": result["status"],
                    "result": result["result"],
                    "updated_files": result["updated_files"],
                    "messages": result["messages"]
                })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing command: {str(e)}"
                })
    
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Unexpected error: {str(e)}"
            })
        except:
            pass


@app.post("/process")
async def process_command(data: dict):
    """
    HTTP endpoint для обработки команд (альтернатива WebSocket)
    """
    command = data.get("command", "")
    files = data.get("files", {})
    
    if not command:
        return {"error": "No command provided"}
    
    try:
        agent_system = get_agent_system()
        result = agent_system.process_command(command, files)
        return result
    except ValueError as e:
        return {
            "error": str(e),
            "hint": "Set GOOGLE_API_KEY environment variable"
        }
    except Exception as e:
        return {
            "error": f"Error processing command: {str(e)}"
        }
