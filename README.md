# 🤖 RAG with UI

Hệ thống **Retrieval-Augmented Generation (RAG)** chạy hoàn toàn cục bộ, kèm giao diện chat trên trình duyệt. Tải lên tài liệu PDF, hệ thống tự động lập chỉ mục vào cơ sở dữ liệu vector, sau đó bạn có thể đặt câu hỏi — hệ thống tìm kiếm các đoạn văn liên quan và tạo ra câu trả lời có căn cứ bằng LLM cục bộ hoặc đám mây.

---

## ✨ Tính năng

- **Nhập liệu PDF** — Tải lên một hoặc nhiều file PDF qua giao diện web; tài liệu được tự động chia nhỏ, nhúng vector và lưu vào Qdrant.
- **Tìm kiếm ngữ nghĩa** — Câu hỏi được nhúng thành vector và so sánh với các đoạn tài liệu bằng độ tương đồng cosine qua Qdrant.
- **Hỗ trợ nhiều backend LLM** — Chuyển đổi giữa LM Studio (model cục bộ) và Qwen (Alibaba Cloud DashScope) ngay khi đang chạy — không cần khởi động lại.
- **Câu trả lời có trích dẫn** — System prompt yêu cầu model chỉ trả lời từ nội dung đã truy xuất, kèm trích dẫn metadata `(source:page)`.
- **Giao diện Web** — Giao diện HTML/CSS/JS được FastAPI phục vụ tại `http://localhost:8000`.
- **REST API** — Toàn bộ chức năng đều có thể truy cập qua các endpoint JSON để tích hợp hoặc viết script.

---

## 🏗️ Kiến trúc

```
rag-with-ui/
├── main.py          # Ứng dụng FastAPI — routes, khởi động, chuyển đổi backend
├── embedder.py      # Class VectorStore — đọc PDF, chia chunk, nhúng vector, upsert Qdrant
├── retriever.py     # Class Retriever — tìm kiếm ngữ nghĩa, tổng hợp context
├── chatbot.py       # Chatbot + các backend LLM (LMStudioBackend, QwenBackend)
├── ui/              # Frontend tĩnh (HTML, CSS, JS)
│   └── index.html
├── requirements.txt
└── .env             # API keys (DASHSCOPE_API_KEY, v.v.)
```

---

## 🔄 Luồng hoạt động (Workflow)

### Giai đoạn 1 — Lập chỉ mục (Nhập tài liệu)

Khi người dùng tải lên PDF qua giao diện hoặc gọi `POST /upload`:

1. **Đọc tài liệu** — `DirectoryLoader` (LangChain + Unstructured) đọc toàn bộ file `.pdf` trong thư mục `./uploaded_pdfs/`.
2. **Chia chunk** — `RecursiveCharacterTextSplitter` chia tài liệu thành các đoạn ~1200 ký tự với 200 ký tự chồng lấp, dùng các ký tự phân tách nhận biết Markdown để bảo toàn ranh giới ngữ nghĩa.
3. **Nhúng vector** — Mỗi đoạn được đưa vào model embedding của LM Studio (`text-embedding-qwen3-0.6b`) để tạo ra vector 1024 chiều.
4. **Lưu trữ** — Các đoạn và vector được upsert vào collection Qdrant (`PDF_collection`) theo lô 100, kèm metadata `source` và `page`.

### Giai đoạn 2 — Truy vấn (Đặt câu hỏi)

Khi người dùng gửi câu hỏi qua giao diện hoặc gọi `POST /ask`:

1. **Nhúng câu hỏi** — Câu hỏi được chuyển thành vector bằng cùng model embedding.
2. **Truy xuất** — Qdrant thực hiện tìm kiếm độ tương đồng cosine, trả về top-5 đoạn liên quan nhất có điểm số ≥ 0.2.
3. **Xây dựng context** — Các đoạn truy xuất được ghép thành một chuỗi context duy nhất với tiêu đề `[source:file | page:N]`.
4. **Sinh câu trả lời** — Context + câu hỏi được đưa vào template prompt nghiêm ngặt và gửi tới backend LLM đang hoạt động.
5. **Trả về kết quả** — Câu trả lời được làm sạch các thẻ suy luận (`<think>`, `<|...|>`) rồi gửi lại giao diện.

---

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Web Framework | FastAPI + Uvicorn |
| Cơ sở dữ liệu Vector | Qdrant (cục bộ, `http://localhost:6333`) |
| Nhúng vector | LM Studio SDK (`lmstudio`) |
| Đọc tài liệu | LangChain Community + Unstructured |
| Chia văn bản | LangChain `RecursiveCharacterTextSplitter` |
| LLM (cục bộ) | LM Studio — bất kỳ model GGUF nào (mặc định: `google/gemma-4-e2b`) |
| LLM (đám mây) | Qwen qua DashScope (qwen-plus, qwen-max, qwen-turbo) |
| Frontend | Vanilla HTML / CSS / JS |

---

## ⚙️ Yêu cầu trước khi cài đặt

Trước khi chạy dự án, hãy đảm bảo bạn đã có:

- **Python 3.11+**
- **[LM Studio](https://lmstudio.ai/)** đang chạy cục bộ với:
  - Model embedding đã tải: `text-embedding-qwen3-0.6b-text-embedding`
  - Model chat đã tải (ví dụ: `google/gemma-4-e2b`)
  - Local server được bật tại `http://localhost:1234`
- **[Qdrant](https://qdrant.tech/documentation/quick-start/)** đang chạy cục bộ tại `http://localhost:6333`

```bash
# Khởi động Qdrant qua Docker
docker run -p 6333:6333 qdrant/qdrant
```

---

## 🚀 Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/agent42-wp/rag-with-ui.git
cd rag-with-ui
```

### 2. Tạo và kích hoạt môi trường ảo

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
```

### 3. Cài đặt các thư viện

```bash
pip install -r requirements.txt
```

### 4. Cấu hình biến môi trường

Tạo file `.env` ở thư mục gốc của dự án:

```env
# Chỉ cần thiết khi dùng backend Qwen đám mây
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# Tùy chọn — hỗ trợ Gemini đã được comment sẵn, có thể mở rộng sau
# GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Khởi động ứng dụng

```bash
python main.py
```

Ứng dụng sẽ chạy tại **http://localhost:8000**.

---

## 📡 Tài liệu API

### `GET /`
Trả về giao diện web (`ui/index.html`).

### `GET /list-files`
Liệt kê tất cả file PDF hiện có trong thư mục upload.

**Phản hồi:**
```json
{ "files": ["report.pdf", "manual.pdf"] }
```

### `GET /current-model`
Trả về backend LLM và tên model đang hoạt động.

**Phản hồi:**
```json
{ "type": "lmstudio", "model": "google/gemma-4-e2b" }
```

### `POST /upload`
Tải lên một hoặc nhiều file PDF. Kích hoạt lập chỉ mục tự động vào Qdrant.

**Body:** `multipart/form-data` với một hoặc nhiều trường `files`.

**Phản hồi:**
```json
{ "status": "ok", "indexed": ["report.pdf"] }
```

### `POST /set-model`
Chuyển đổi backend LLM đang hoạt động mà không cần khởi động lại.

**Body:**
```json
{ "type": "lmstudio", "model": "google/gemma-4-e2b" }
```

Các loại được hỗ trợ: `"lmstudio"`, `"qwen"`. Với Qwen, các model hợp lệ là `qwen-plus`, `qwen-max`, `qwen-turbo`.

### `POST /ask`
Gửi câu hỏi và nhận câu trả lời có căn cứ từ pipeline RAG.

**Body:**
```json
{ "question": "Chính sách hoàn tiền được mô tả trong tài liệu là gì?" }
```

**Phản hồi:**
```json
{ "answer": "Theo tài liệu (source:manual.pdf | page:3), yêu cầu hoàn tiền phải được gửi trong vòng 30 ngày..." }
```

---

## 🔧 Cấu hình

Các hằng số quan trọng trong `main.py` có thể điều chỉnh cho phù hợp:

| Hằng số | Mặc định | Mô tả |
|---|---|---|
| `QDRANT_URL` | `http://localhost:6333` | URL của Qdrant server |
| `COLLECTION_NAME` | `PDF_collection` | Tên collection trong Qdrant |
| `VECTOR_SIZE` | `1024` | Phải khớp với số chiều đầu ra của model embedding |
| `EMBED_MODEL` | `text-embedding-qwen3-0.6b-text-embedding` | Tên model embedding trong LM Studio |
| `LMS_MODEL` | `google/gemma-4-e2b` | Model chat mặc định của LM Studio |
| `UPLOAD_DIR` | `./uploaded_pdfs` | Thư mục chứa PDF đã tải lên |

Tham số chia chunk có thể điều chỉnh trong `embedder.py → load_and_index()`:

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `chunk_size` | `1200` | Số ký tự tối đa mỗi chunk |
| `chunk_overlap` | `200` | Số ký tự chồng lấp giữa các chunk liên tiếp |

Tham số truy xuất có thể điều chỉnh trong `retriever.py → retrieve()`:

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `k` | `5` | Số lượng chunk cần truy xuất |
| `score_threshold` | `0.2` | Điểm tương đồng cosine tối thiểu |

---

## 💡 Cách hoạt động của Prompt

Hệ thống dùng một template prompt nghiêm ngặt, tập trung vào trích dẫn (định nghĩa trong `chatbot.py`):

```
You are a strict, citation-focused assistant for a private knowledge base.
RULES:
1. Use ONLY the provided content to answer.
2. If the answer is not clearly contained in the content, say:
   "I don't know based on the provided documents."
3. Do NOT use outside knowledge, guessing, or web information.
4. If applicable, cite source as (source:page) using the metadata.

Content:
[các đoạn truy xuất kèm metadata source/page]

Question: [câu hỏi của người dùng]
```

Thiết kế này đảm bảo model không hallucinate và luôn truy nguyên câu trả lời về tài liệu nguồn.

---

## 🗺️ Mở rộng dự án

**Thêm backend LLM mới** — Tạo một class có phương thức `respond(prompt: str) -> str` và thuộc tính `label`, sau đó đăng ký trong `main.py → set_model()`. Skeleton backend Gemini đã có sẵn trong `chatbot.py` (dưới dạng comment) để tham khảo.

**Thay đổi model embedding** — Cập nhật `EMBED_MODEL` và `VECTOR_SIZE` trong `main.py`. Hãy lập chỉ mục lại toàn bộ tài liệu sau khi thay model vì các vector cũ sẽ không tương thích.

**Hỗ trợ loại tài liệu khác** — `DirectoryLoader` hỗ trợ mọi định dạng mà Unstructured có thể parse (DOCX, HTML, TXT, v.v.). Thay đổi pattern `glob` trong `embedder.py → _load_docs()`.

---

## 📄 Giấy phép

Dự án này là mã nguồn mở. Xem chi tiết giấy phép trong repository.

---

## 🙏 Lời cảm ơn

Xây dựng với [FastAPI](https://fastapi.tiangolo.com/), [LangChain](https://python.langchain.com/), [Qdrant](https://qdrant.tech/), [LM Studio](https://lmstudio.ai/) và [Unstructured](https://unstructured.io/).
