# 🚀 Hướng Dẫn Chạy Food Chatbot

## Yêu Cầu Hệ Thống

- **Python 3.8+**
- **Ollama** (với model llama3.1:8b đã cài đặt)

## 📦 Bước 1: Chạy Backend

```bash
cd food-chatbot-backend
bash start.sh
```

**Backend sẽ chạy tại:** `http://localhost:8000`  
**API Docs:** `http://localhost:8000/docs`

⏳ **Thời gian khởi động:** ~20-25 giây (load AI models)

### Kiểm Tra Backend Đã Chạy:

```bash
curl http://localhost:8000/docs
```

Nếu thấy HTML response → Backend đã sẵn sàng!

---

## 🌐 Bước 2: Chạy Frontend

**Mở terminal mới** (không đóng terminal backend):

```bash
cd frontendchatbot
python3 -m http.server 3000
```

**Frontend sẽ chạy tại:** `http://localhost:3000`

### Hoặc mở trực tiếp file HTML:

```bash
cd frontendchatbot

# macOS
open index.html

# Linux
xdg-open index.html

# Windows
start index.html
```

---

## ✅ Bước 3: Test Thử Chatbot

1. Mở trình duyệt: `http://localhost:3000`
2. Thử các câu hỏi:
   - **"Tìm quán phở"**
   - **"Quán lẩu giá rẻ"**
   - **"Buffet quận 1"**
   - **"Quán cà phê sân vườn"**
   - **"Quán ăn chay gần tôi"**

---

## ⛔ Bước 4: Dừng Hệ Thống

### Dừng Backend:

```bash
lsof -ti:8000 | xargs kill -9
```

### Dừng Frontend:

```bash
lsof -ti:3000 | xargs kill -9
```

**Hoặc:** Nhấn `Ctrl+C` trong terminal đang chạy.

---

## 📁 Cấu Trúc Project

```
chatbotfood/
├── food-chatbot-backend/         # Backend API (FastAPI + Ollama)
│   ├── config/                   # Cấu hình (settings.py, .env, synonyms.py)
│   ├── services/                 # Logic chính (RAG, search, LLM)
│   ├── database/                 # SQLite database (2057 restaurants)
│   ├── data/                     # BM25 & FAISS indexes
│   ├── routes/                   # API endpoints
│   ├── utils/                    # Text processing, helpers
│   ├── main.py                   # Entry point
│   ├── start.sh                  # Quick start script
│   └── requirements.txt          # Python dependencies
│
├── frontendchatbot/              # Frontend web UI
│   ├── index.html                # Giao diện chính
│   ├── script.js                 # Logic frontend
│   └── style.css                 # Styling
│
├── API_CHO_FRONTEND.md           # 📡 API documentation cho frontend devs
├── README.md                     # 📖 Project overview
├── summary.txt                   # 📊 Test results & features
└── HUONG_DAN_CHAY.md            # 📝 File này (hướng dẫn chạy)
```

---

## 🔧 Troubleshooting

### ❌ Backend không khởi động

**Kiểm tra port 8000 đã bị chiếm:**
```bash
lsof -ti:8000
```
Nếu có output → kill process: `lsof -ti:8000 | xargs kill -9`

**Kiểm tra Ollama đang chạy:**
```bash
ollama list
```
Nếu lỗi → Start Ollama: `ollama serve &`

**Xem log chi tiết:**
```bash
cd food-chatbot-backend
tail -f backend.log
```

### ❌ Frontend không hiển thị

**Kiểm tra backend đã chạy:**
```bash
curl http://localhost:8000/docs
```

**Mở Developer Console (F12)** để xem lỗi JavaScript.

### ❌ Chatbot trả lời sai

**Kiểm tra cấu hình:**
```bash
cat food-chatbot-backend/.env | grep WEIGHT
```

Đảm bảo:
- `SEMANTIC_WEIGHT=0.0`
- `BM25_WEIGHT=1.0`

**Rebuild indexes:**
```bash
cd food-chatbot-backend
source venv/bin/activate
python init_system.py
```

---

## 📚 Tài Liệu Khác

- **API_CHO_FRONTEND.md** - Chi tiết API endpoints cho frontend developers
- **summary.txt** - Báo cáo test results và danh sách chức năng
- **README.md** - Project overview và technical details

---

## 💡 Lưu Ý Quan Trọng

✅ **Database:** 2057 nhà hàng ở TP.HCM  
✅ **Search Engine:** BM25 (keyword-based) cho độ chính xác cao  
✅ **LLM:** Ollama llama3.1:8b  
✅ **Languages:** Vietnamese + English support  
✅ **Cache:** 5 phút TTL (tăng tốc độ response)

⚠️ **Semantic search hiện tại DISABLED** do gây kết quả không chính xác. Chỉ dùng BM25 keyword search.

---

## 🎯 Độ Chính Xác

| Test Case | Accuracy |
|-----------|----------|
| Phở       | 80%      |
| Lẩu       | 100%     |
| Buffet    | 100%     |
| Bún       | 80%      |
| Cà phê    | 60%      |
| Chay      | 100%     |
| **Overall** | **~85%** |

---

**Happy Testing! 🎉**

Nếu gặp vấn đề, xem file `summary.txt` để biết thêm chi tiết.
