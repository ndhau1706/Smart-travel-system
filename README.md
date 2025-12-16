# 🍜 Food Chatbot - Restaurant Recommendation System

AI-powered chatbot giúp tìm quán ăn ngon tại TP.HCM.

---

## 🎯 Tổng quan

**Module chatbot này là SUB-MODULE** trong hệ thống lớn hơn:

```
┌──────────────────────────────┐
│    Parent Module (Auth)      │
│  - Login/Register            │
│  - Guest Limits (10 msg)     │
│  - User Management           │
└──────────┬───────────────────┘
           │ session_id
           ↓
┌──────────────────────────────┐
│    Chatbot Module            │
│  - Chat API                  │
│  - Restaurant Search (RAG)   │
│  - 2000+ restaurants HCM     │
└──────────────────────────────┘
```

**Chatbot KHÔNG xử lý:**
- ❌ Authentication (login/register)
- ❌ Guest message limits
- ❌ User profiles

**Chatbot CHỈ LO:**
- ✅ Chat với user
- ✅ Tìm quán ăn phù hợp
- ✅ Lưu chat history

---

## 📁 Cấu trúc

```
chatbotfood/
├── 📄 HUONG_DAN_CHAY.md        ← BẮT ĐẦU TỪ ĐÂY!
├── 📄 API_CHO_FRONTEND.md      ← Cho frontend team
├── 📄 INTEGRATION_GUIDE.md     ← Tích hợp với parent module
│
├── food-chatbot-backend/       ← Backend API
│   ├── main.py                 
│   ├── start.sh                ← Script khởi động
│   ├── config/
│   ├── services/
│   │   └── rag_pipeline.py     ← Core logic
│   ├── routes/
│   │   ├── chat.py             ← Chat endpoint
│   │   └── sessions.py         
│   └── database/
│       └── chatbot.db
│
└── frontendchatbot/            ← Frontend UI
    ├── index.html              ← Full version (có auth)
    ├── index_simple.html       ← Simple version (không auth)
    ├── script.js
    └── script_simple.js
```

---

## 🚀 Quick Start

### Đọc file này trước:
```bash
📖 HUONG_DAN_CHAY.md
```

Hoặc:

### 1. Chạy Backend
```bash
cd food-chatbot-backend
bash start.sh
```

Backend chạy tại: `http://localhost:8000`

### 2. Chạy Frontend
```bash
cd frontendchatbot
python3 -m http.server 3000
```

Frontend: `http://localhost:3000/index.html`

---

## 📚 Documentation

| File | Dành cho | Nội dung |
|------|----------|----------|
| **HUONG_DAN_CHAY.md** | Tester, Developer | Cách chạy backend & frontend |
| **API_CHO_FRONTEND.md** | Frontend Team | API endpoints, request/response |
| **INTEGRATION_GUIDE.md** | System Architect | Tích hợp chatbot vào parent module |

---

## ✨ Features

### Core
- 🤖 AI chatbot với RAG (Retrieval-Augmented Generation)
- 🔍 Tìm kiếm hybrid (BM25 + FAISS vector search)
- 📍 Location-based sorting (GPS)
- ⭐ Filter theo rating, giá, món ăn, quận
- 👥 Group size detection (buffet cho X người)
- 🕐 Open/closed status
- 💬 Chat history per user

### Database
- 2057 restaurants ở TP.HCM
- Dữ liệu từ Google Maps
- Cập nhật: Dec 2025

---

## 🛠️ Tech Stack

### Backend
- FastAPI (Python)
- SQLite + aiosqlite
- Sentence Transformers (embeddings)
- FAISS (vector search)
- BM25 (keyword search)
- Ollama/LLM (response generation)

### Frontend
- Vanilla JavaScript
- HTML/CSS
- Fetch API
- Geolocation API

---

## 🎯 Use Cases

### ✅ Queries hoạt động tốt:
- "tìm quán phở ngon"
- "buffet cho 8 người"
- "quán cơm tấm quận 1"
- "quán có rating cao"
- "quán đang mở cửa" (giờ hành chính)
- "tìm quán hải sản gần đây" (cần GPS)

### ⚠️ Có limitations:
- Đặt bàn (booking) → Không support
- Review chi tiết từng món → Chỉ có overview
- So sánh giá cụ thể → Chỉ có price_level
- Menu đầy đủ → Không có

---

## 🔧 Configuration

### Backend Settings
File: `food-chatbot-backend/config/settings.py`

```python
MAX_RESULTS = 10           # Số quán trả về
CACHE_ENABLED = True       # Enable caching
CACHE_TTL_HOURS = 24      # Cache lifetime
```

### Frontend API URL
File: `frontendchatbot/script.js`

```javascript
const API_URL = 'http://localhost:8000';
```

---

## 🧪 Testing

### Test API với curl:
```bash
# Tạo session
SESSION=$(curl -s -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","language":"vi"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Chat
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"tìm quán phở\",\"session_id\":\"$SESSION\"}"
```

---

## 🐛 Known Issues

### 1. Kết quả ít hơn 10 quán
**Nguyên nhân:** Filter relevance quá strict với một số keywords.

**Workaround:** Thử query cụ thể hơn, hoặc điều chỉnh `_filter_relevant_results()` trong `rag_pipeline.py`.

### 2. Location warning không hiện
**Nguyên nhân:** LLM không append location_note đúng cách.

**Status:** Đang investigate. Tạm thời bot vẫn trả kết quả không sort by distance.

### 3. Guest limit không enforce
**Giải pháp:** Parent module phải handle guest limits (10 messages).

---

## 📦 Dependencies

### Backend
```bash
pip install fastapi uvicorn aiosqlite
pip install sentence-transformers faiss-cpu
pip install rank-bm25
```

### Frontend
Không cần install, chỉ cần web browser.

---

## 🚀 Deployment Notes

### Production Checklist:
- [ ] Update CORS origins trong `main.py`
- [ ] Thay SQLite bằng PostgreSQL
- [ ] Add Redis cache
- [ ] Setup monitoring (Prometheus/Grafana)
- [ ] SSL certificates
- [ ] Rate limiting
- [ ] API authentication tokens

---

## 🤝 Collaboration

### Cho Frontend Team:
Đọc **`API_CHO_FRONTEND.md`**

### Cho Backend Team:
Đọc `food-chatbot-backend/README.md`

### Cho System Integration:
Đọc **`INTEGRATION_GUIDE.md`**

---

## 📞 Support

Có vấn đề? Check docs:
1. `HUONG_DAN_CHAY.md` - Cách chạy
2. `API_CHO_FRONTEND.md` - API reference
3. `INTEGRATION_GUIDE.md` - Tích hợp hệ thống

---

## 📝 Version

- **Version:** 1.0.0
- **Last Updated:** Dec 16, 2025
- **Database:** 2057 restaurants HCM
- **Python:** 3.8+
- **Node.js:** Not required

---

**Built with ❤️ for food lovers in Ho Chi Minh City**
