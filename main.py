import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from embedder import VectorStore
from retriever import Retriever
from chatbot import Chatbot, LMStudioBackend, GeminiBackend, QwenBackend

load_dotenv()

# --- Config ---
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "PDF_collection"
VECTOR_SIZE = 1024
EMBED_MODEL = "text-embedding-qwen3-0.6b-text-embedding"
LMS_MODEL = "nvidia/nemotron-3-nano-4b"
UPLOAD_DIR = "./uploaded_pdfs"

Path(UPLOAD_DIR).mkdir(exist_ok=True)

app = FastAPI()
app.mount("/ui", StaticFiles(directory="ui"), name="ui")

# --- Khởi tạo global ---
vector_store = VectorStore(
    collection_name=COLLECTION_NAME,
    vector_size=VECTOR_SIZE,
    qdrant_url=QDRANT_URL,
    embed_model_name=EMBED_MODEL,
)
retriever = Retriever(vector_store=vector_store)
chatbot_instance = Chatbot(retriever=retriever)

# Mặc định dùng LMStudio
try:
    chatbot_instance.set_backend(LMStudioBackend(LMS_MODEL))
    current_backend = {"type": "lmstudio", "model": LMS_MODEL}
except Exception:
    current_backend = {"type": None, "model": None}


# ── Routes ──

@app.get("/", response_class=HTMLResponse)
def root():
    with open("ui/index.html", encoding="utf-8") as f:
        return f.read()


@app.get("/list-files")
def list_files():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".pdf")]
    return JSONResponse({"files": files})


@app.get("/current-model")
def current_model():
    return JSONResponse(current_backend)


@app.post("/upload")
async def upload_pdfs(files: list[UploadFile] = File(...)):
    saved = []
    for file in files:
        dest = Path(UPLOAD_DIR) / file.filename
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        saved.append(file.filename)

    vector_store.load_and_index(pdf_dir=UPLOAD_DIR)
    return JSONResponse({"status": "ok", "indexed": saved})


class SetModelRequest(BaseModel):
    type: str          # "lmstudio" | "gemini"
    model: str         # tên model cụ thể


@app.post("/set-model")
def set_model(req: SetModelRequest):
    global current_backend
    try:
        if req.type == "lmstudio":
            backend = LMStudioBackend(req.model)
        elif req.type == "gemini":
            backend = GeminiBackend(req.model)
        elif req.type == "qwen":
            backend = QwenBackend(req.model)
        else:
            return JSONResponse({"error": f"Loại backend không hợp lệ: {req.type}"}, status_code=400)

        chatbot_instance.set_backend(backend)
        current_backend = {"type": req.type, "model": req.model}
        return JSONResponse({"status": "ok", "type": req.type, "model": req.model})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class AskRequest(BaseModel):
    question: str


@app.post("/ask")
def ask(req: AskRequest):
    try:
        answer = chatbot_instance.ask(req.question)
        return JSONResponse({"answer": answer})
    except Exception as e:
        return JSONResponse({"error": f"Lỗi: {str(e)}"}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
