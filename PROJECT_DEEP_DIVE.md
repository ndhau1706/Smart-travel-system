# Smart Travel System — Tài liệu phân tích dự án (Deep Dive)

> Phạm vi tài liệu: toàn bộ thư mục `d:\Smart-travel-system-main`  
> Repo Git thực tế nằm trong: `New_Frontend/` (thư mục gốc hiện tại không phải git repo)  
> Lưu ý bảo mật: tài liệu này **cố tình không in giá trị secrets** (mật khẩu, API key). Nếu bạn muốn mình viết bản “internal” có giá trị thật thì hãy nói rõ.

---

## 1) Tổng quan dự án

**Smart Travel System** là hệ thống web khám phá/đặt bàn nhà hàng, gồm:

- **Frontend**: React + TypeScript + Vite + Tailwind + Radix/shadcn (UI).
- **Backend**: Python FastAPI + SQLAlchemy async.
- **Data**:
  - Dev: SQLite (`backend/smart_travel.db`).
  - Prod: Cloud SQL (PostgreSQL) qua Unix socket `/cloudsql/...`.
  - Dataset seed: `backend/hcm_restaurants_with_local_images.json` (nguồn dữ liệu nhà hàng + comments/reviews).
- **Deploy**: Docker + Google Cloud Run; CI/CD tham chiếu: Google Cloud Build (`New_Frontend/cloudbuild.yaml`).

---

## 2) Cấu trúc thư mục & thành phần chính

### 2.1 Cây thư mục mức cao

```
Smart-travel-system-main/
├─ New_Frontend/                 # (git repo) Frontend + Backend + infra files
│  ├─ src/                       # React application
│  ├─ backend/                   # FastAPI application
│  ├─ docs/                      # Tài liệu (một phần đang lệch code)
│  ├─ Dockerfile                 # Docker frontend (Vite build -> Nginx)
│  ├─ nginx.conf                 # Nginx config phục vụ SPA
│  ├─ cloudbuild.yaml            # CI/CD GCP (build+deploy)
│  ├─ deploy-gcp.ps1             # Script deploy Cloud Run (Windows)
│  └─ ...
└─ plans/                        # Tài liệu phân tích/đề xuất kiến trúc
   ├─ architecture-analysis.md
   └─ upgrade-plan-10-points.md
```

### 2.2 Frontend (`New_Frontend/src/`)

Điểm nổi bật:
- Router: React Router DOM (BrowserRouter).
- UI: Tailwind + shadcn/ui components (Radix UI).
- Giao tiếp backend: `src/services/api.ts` (restaurants/reviews), `src/services/auth.ts` (auth/profile).
- Có “hướng” kiến trúc mới với React Query + Zustand (`src/hooks/*`, `src/stores/*`) nhưng **chưa wire vào app** (xem phần Issues).

Các cụm quan trọng:

```
src/
├─ pages/
│  ├─ Home/ Restaurants/ Bookings/ Reviews/ Chatbot/ ...
│  ├─ Account/ (ProfilePage, SettingsPage, PremiumPage)
│  └─ index.ts                   # barrel exports pages
├─ components/
│  ├─ ui/                        # shadcn/ui
│  ├─ AuthDialog.tsx             # Login/Register/OTP/Forgot
│  ├─ BookingDialog.tsx          # UI đặt bàn (hiện đang mock)
│  ├─ Navigation.tsx             # Sidebar navigation
│  └─ ...
├─ services/
│  ├─ api.ts                     # restaurants/reviews fetch
│  ├─ auth.ts                    # auth/profile fetch
│  └─ temp_test.ts               # file test tạm (hiện gọi endpoint chưa tồn tại)
├─ hooks/                        # React Query hooks (chưa dùng trong App)
├─ stores/                       # Zustand stores (chưa dùng trong App)
├─ lib/queryClient.ts            # React Query client + queryKeys
└─ context/SidebarContext.tsx
```

### 2.3 Backend (`New_Frontend/backend/`)

Điểm nổi bật:
- FastAPI app tại `backend/main.py`.
- Modules theo domain: `auth`, `users`, `restaurants`, `bookings`, `reviews`, `chat`, `contact`.
- Middleware:
  - CORS
  - Request logging (structured)
  - Rate limiting (in-memory)
  - Cache cleanup background task (in-memory)
- Admin endpoints (require admin JWT) để seed/migrate/fix data.

```
backend/
├─ app/
│  ├─ core/
│  │  ├─ config.py               # pydantic-settings
│  │  ├─ database.py             # SQLAlchemy async + Cloud SQL
│  │  ├─ security.py             # JWT helpers + current user dep
│  │  ├─ admin_auth.py           # admin-only dep
│  │  ├─ exceptions.py           # global exception handlers
│  │  ├─ logging_config.py       # structured logging + middleware
│  │  ├─ rate_limit.py           # middleware rate limit
│  │  └─ cache.py                # LRU cache TTL (in-memory)
│  ├─ modules/
│  │  ├─ auth/ users/ restaurants/ bookings/ reviews/ chat/ contact/
│  └─ shared/
│     ├─ schemas.py              # standard response helpers
│     └─ email_service.py        # Brevo transactional email (API/SMTP)
├─ main.py                       # entrypoint
├─ import_restaurants.py         # import dataset JSON -> DB
├─ seed_data.py                  # seed sample data nhỏ (dev)
├─ hcm_restaurants_with_local_images.json
├─ migrations/cloudsql_schema.sql
├─ tests/                        # pytest (async) + httpx ASGITransport
└─ requirements.txt
```

---

## 3) Setup môi trường & chạy local

### 3.1 Yêu cầu

- Node.js 18+ (Dockerfile dùng Node 20).
- Python 3.11+

### 3.2 Frontend dev

Tại `New_Frontend/`:

```bash
npm install
npm run dev
```

`vite.config.ts` cấu hình dev server port **3000**.

### 3.3 Backend dev

Tại `New_Frontend/backend/`:

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

Mặc định backend chạy port **8000** (theo `app/core/config.py`).

### 3.4 Biến môi trường (khuyến nghị)

Frontend (`New_Frontend/.env`):

```env
# QUY ƯỚC HIỆN TẠI CỦA CODE: base URL KHÔNG kèm /api
VITE_API_BASE_URL=http://localhost:8000
```

Backend (`New_Frontend/backend/.env`):

```env
DEBUG=True
DATABASE_URL=sqlite+aiosqlite:///./smart_travel.db
SECRET_KEY=...                         # không hardcode trong code khi production
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
BREVO_API_KEY=...
EMAIL_FROM=...
EMAIL_FROM_NAME=Smart Travel
BREVO_SMTP_HOST=smtp-relay.brevo.com   # optional
BREVO_SMTP_PORT=587                   # optional
BREVO_SMTP_USER=...                   # optional
BREVO_SMTP_PASSWORD=...               # optional
OTP_TTL_MIN=10
OTP_MAX_ATTEMPTS=5
OTP_RESEND_LIMIT_PER_HOUR=5
```

Ghi chú:
- Backend có chế độ Cloud SQL nếu set `CLOUD_SQL_CONNECTION_NAME` (+ DB_USER/DB_PASS/DB_NAME/DB_TYPE).
- Có biến `FORCE_SQLITE=true` để ép dùng SQLite ngay cả khi có Cloud SQL env.

---

## 4) Kiến trúc tổng thể & luồng dữ liệu

### 4.1 Kiến trúc mức hệ thống

```
Browser (React SPA)
  └─ fetch() -> FastAPI (/api/*)
        ├─ Auth (JWT + OTP email)
        ├─ Restaurants / Reviews / Bookings / Users / Chat
        └─ DB (SQLite dev / Cloud SQL Postgres prod)
```

### 4.2 Chuẩn response API

Backend chuẩn hoá response qua `backend/app/shared/schemas.py`:

- `success_response(data, message)`
- `error_response(code, message, details?)`
- `paginated_response(data, total, page, limit)`

Lưu ý: hiện tại nhiều endpoint trả **HTTP 200** ngay cả khi `success=false` (xem Issues).

---

## 5) Backend — phân tích chi tiết

### 5.1 Entry point: `backend/main.py`

Các việc chính:
- `lifespan()`:
  - `init_db()` -> `Base.metadata.create_all`
  - `seed_restaurants_if_needed()` (auto seed nếu DB trống / ảnh không chuẩn)
  - chạy background task cleanup cache
- Middleware:
  - `RequestLoggingMiddleware` (log request/response + `X-Request-ID`)
  - `RateLimitMiddleware` (100 req/min, 2000 req/hour, burst 20/sec; exclude docs/health)
  - CORS theo `settings.CORS_ORIGINS`
- Routers: `/api/auth`, `/api/users`, `/api/restaurants`, `/api/bookings`, `/api/reviews`, `/api/chat`, `/api/contact`, `/api/search`
- Admin tools: `/api/admin/*` + `/api/debug/db-info` (đều require admin JWT)

### 5.2 Core components

**Config** (`backend/app/core/config.py`)
- Dùng `pydantic-settings` đọc từ `.env`.
- Quan trọng: `SECRET_KEY`, `DATABASE_URL`, `CLOUD_SQL_CONNECTION_NAME`, `CORS_ORIGINS`, OTP/email settings.

**Database** (`backend/app/core/database.py`)
- Tạo async engine theo 2 mode:
  - Cloud SQL: build connection string dạng `postgresql+asyncpg://user:pass@/db?host=/cloudsql/INSTANCE`
  - SQLite: ép dùng file `backend/smart_travel.db` (absolute path)
- Dependency `get_db()` yield session và commit/rollback tự động.

**Security** (`backend/app/core/security.py`)
- bcrypt hashing via passlib.
- JWT access/refresh tokens:
  - access có claim `type="access"`
  - refresh có claim `type="refresh"`
  - `sub` = user_id
- Dependency `get_current_user_id()` (HTTP Bearer).
- Có `get_current_user_id_optional()` cho “anonymous allowed”.

**Admin Auth** (`backend/app/core/admin_auth.py`)
- `get_current_admin_user()` kiểm tra user tồn tại, active, role = ADMIN.

**Exceptions** (`backend/app/core/exceptions.py`)
- Global handler cho:
  - `AppException` (custom)
  - `HTTPException` / `StarletteHTTPException`
  - `RequestValidationError` (Pydantic body/query)
  - `Exception` (500 generic)

**Logging** (`backend/app/core/logging_config.py`)
- JSON logging khi production (DEBUG=false).
- Middleware log request + duration + request_id.

**Rate limiting** (`backend/app/core/rate_limit.py`)
- In-memory sliding window, theo client id (header `X-API-Key` hoặc IP).
- Lưu ý: Cloud Run scale nhiều instance -> rate-limit **không dùng chung** (mỗi instance 1 bộ nhớ).

**Cache** (`backend/app/core/cache.py`)
- LRU cache TTL in-memory + background cleanup.
- Hiện tại chưa thấy dùng decorator `@cached` nhiều trong routes.

### 5.3 Modules & endpoints (liệt kê theo runtime)

Danh sách route được trích trực tiếp từ FastAPI runtime (không tính `/docs`, `/openapi.json`):

| Method | Path |
|---|---|
| GET | `/` |
| GET | `/health` |
| GET | `/api/restaurants` |
| GET | `/api/restaurants/search` |
| GET | `/api/restaurants/{restaurant_id}` |
| GET | `/api/restaurants/{restaurant_id}/menu` |
| POST | `/api/auth/login` |
| POST | `/api/auth/register/start` |
| POST | `/api/auth/register/verify` |
| POST | `/api/auth/register` |
| POST | `/api/auth/refresh` |
| POST | `/api/auth/logout` |
| GET | `/api/auth/me` |
| POST | `/api/auth/forgot-password` |
| POST | `/api/auth/reset-password` |
| GET | `/api/users/profile` |
| PUT | `/api/users/profile` |
| PUT | `/api/users/password` |
| GET | `/api/users/addresses` |
| POST | `/api/users/addresses` |
| PUT | `/api/users/addresses/{address_id}` |
| DELETE | `/api/users/addresses/{address_id}` |
| GET | `/api/users/search-history` |
| POST | `/api/users/search-history` |
| GET | `/api/users/favorites` |
| POST | `/api/users/favorites` |
| DELETE | `/api/users/favorites/{favorite_id}` |
| GET | `/api/bookings` |
| GET | `/api/bookings/{booking_id}` |
| POST | `/api/bookings` |
| PUT | `/api/bookings/{booking_id}` |
| DELETE | `/api/bookings/{booking_id}` |
| GET | `/api/bookings/availability/check` |
| POST | `/api/reviews` |
| PUT | `/api/reviews/{review_id}` |
| DELETE | `/api/reviews/{review_id}` |
| POST | `/api/reviews/{review_id}/like` |
| GET | `/api/reviews/me` |
| GET | `/api/reviews/restaurant/{restaurant_id}` |
| POST | `/api/chat/message` |
| GET | `/api/chat/history` |
| GET | `/api/chat/{chat_id}` |
| DELETE | `/api/chat/{chat_id}` |
| POST | `/api/contact` |
| GET | `/api/search` |
| GET | `/api/debug/db-info` (admin) |
| POST | `/api/admin/seed-data` (admin) |
| POST | `/api/admin/seed-reviews` (admin) |
| POST | `/api/admin/migrate-db` (admin) |
| POST | `/api/admin/fix-encoding` (admin) |
| POST | `/api/admin/fix-json-fields` (admin) |
| GET | `/api/admin/check-data` (admin) |

Tài liệu API hiện có: `New_Frontend/backend/docs/API.md`.

### 5.4 Thuật toán/logic nổi bật

**OTP (đăng ký / quên mật khẩu)** — `app/modules/auth/routes.py`
- OTP 6 chữ số.
- Rate limit resend: `OTP_RESEND_LIMIT_PER_HOUR` (đếm record trong 1h).
- TTL: `OTP_TTL_MIN`, max attempts: `OTP_MAX_ATTEMPTS`.
- Flow:
  - `/register/start` -> gửi OTP
  - `/register/verify` -> verify OTP -> tạo user -> login
  - `/forgot-password` -> gửi OTP reset
  - `/reset-password` -> verify OTP -> đổi password

**Email sending** — `app/shared/email_service.py`
- Ưu tiên Brevo HTTP API nếu set `BREVO_API_KEY`, fallback Brevo SMTP relay nếu set `BREVO_SMTP_USER`/`BREVO_SMTP_PASSWORD`.
- Khi `DEBUG=True` mà thiếu config: email sẽ bị skip (phục vụ dev/tests). Production nên set Brevo config đầy đủ.

**Restaurant list/search** — `app/modules/restaurants/routes.py`
- Lọc nhà hàng active + ảnh hợp lệ (GCS/Unsplash) + loại URL Google Places `media?maxHeightPx` do hay 403.
- Search/filter bằng `ilike`, sort theo rating/price/name, phân trang.

**Review rating aggregation** — `app/modules/reviews/routes.py`
- Sau create/update/delete review: tính `avg(rating)` + `count` rồi update vào Restaurant.

**Chatbot** — `app/modules/chat/routes.py`
- Rule-based map `keyword -> response`, trả suggestions (chưa tích hợp AI).

**Seed dữ liệu**:
- `import_restaurants.py`: parse dataset -> normalize cuisine, opening hours, images; tạo restaurants + import comment thành reviews.
- `main.py` có thêm admin endpoint `/api/admin/seed-data` (logic khác, generate URL ảnh theo tên).

### 5.5 Database schema (từ model code)

Các bảng chính:
- `users`, `email_otps`
- `restaurants`, `menu_items`
- `reviews`
- `bookings`
- `chat_sessions`, `chat_messages`
- `user_addresses`, `favorite_restaurants`, `search_history`, `notifications`, `user_sessions`

Quan hệ chính:
- User 1–n Booking/Review/ChatSession/Address/Favorite/SearchHistory/Notification/Session
- Restaurant 1–n MenuItem/Booking/Review/Favorite
- ChatSession 1–n ChatMessage

Số liệu snapshot từ `backend/smart_travel.db` hiện có (local):
- `restaurants`: 2057
- `reviews`: 5997
- `menu_items`: 16
- `users`: 2

Lưu ý: file DB local này có dấu hiệu “schema drift” (thiếu một số bảng mới so với code).

---

## 6) Frontend — phân tích chi tiết

### 6.1 Cấu hình build/dev

- `vite.config.ts`:
  - `server.port = 3000`, `open=true`
  - output `build/`
  - alias fix dependency names (mang tính workaround)
- `tailwind.config.js`: theme variables + darkMode class.

### 6.2 Router & pages

Routes chính được khai báo trong `src/App.tsx`:
- `/` Home
- `/restaurants`, `/restaurants/:id`
- `/bookings`
- `/menu`
- `/chatbot`
- `/reviews`
- `/about`, `/contact`, `/policy`, `/thank-you`
- `/account/profile`, `/account/settings`, `/account/premium`

### 6.3 API layer (thực tế)

**`src/services/api.ts`**
- `fetchRestaurants(limit,page)` -> GET `/api/restaurants`
- `fetchRestaurantById(id)` -> GET `/api/restaurants/{id}`
- `fetchRestaurantReviews(restaurantId)` -> GET `/api/reviews/restaurant/{id}`
- `searchRestaurants(q)` -> GET `/api/restaurants/search?q=...`
- `getNewestRestaurants()` -> GET `/api/restaurants/newest` (**backend hiện không có endpoint này**)

**`src/services/auth.ts`**
- `login`, `registerStart`, `registerVerify`, `forgotPassword`, `resetPassword`
- `getProfile`, `updateProfile`, `changePassword`
- Lấy access token từ `localStorage["auth"]` để set `Authorization: Bearer ...`

### 6.4 Tính năng đã/ chưa “nối” backend

Đã nối backend:
- Auth (OTP), Profile/Settings (update profile/theme, change password)
- Restaurant list/detail + load reviews theo restaurant

Chưa nối backend (hiện mock UI):
- Bookings page + BookingDialog (chưa gọi `/api/bookings`)
- Reviews page tổng hợp (đang mock dữ liệu, chưa gọi `/api/reviews`)
- Chatbot UI (đang dùng canned responses ở frontend; chưa gọi `/api/chat/message`)

### 6.5 State management (hiện trạng)

Hiện tại app chủ yếu dùng:
- Local state trong `App.tsx`
- `SidebarContext`
- `localStorage` cho auth

Trong repo có sẵn nhưng **chưa được wire**:
- React Query client (`src/lib/queryClient.ts`)
- Zustand stores (`src/stores/authStore.ts`, `src/stores/uiStore.ts`)
- React Query hooks (`src/hooks/useAuth.ts`, `src/hooks/useRestaurants.ts`)

---

## 7) Deploy / Infra / CI-CD

### 7.1 Docker frontend (`New_Frontend/Dockerfile` + `nginx.conf`)

- Stage build: `node:20-alpine`, `npm ci`, `vite build` -> output `build/`
- Stage runtime: `nginx:alpine`, serve `build/` tại port 8080 (Cloud Run)
- SPA routing: `try_files $uri ... /index.html`

Khuyến nghị DX: nên có `.dockerignore` tại `New_Frontend/` để tránh copy `node_modules/` và `backend/` vào build context khi build local.

### 7.2 Docker backend (`New_Frontend/backend/Dockerfile`)

- `python:3.11-slim`, `pip install -r requirements.txt`
- Copy `app/`, `main.py`, `*.py`, dataset JSON
- Run `uvicorn main:app --port ${PORT:-8080}`

### 7.3 Cloud Build pipeline (`New_Frontend/cloudbuild.yaml`)

Pipeline làm:
1) Build + push backend image
2) Deploy backend Cloud Run (set env vars DB/secret)
3) Build + push frontend image (build-arg `VITE_API_BASE_URL`)
4) Deploy frontend Cloud Run

Điểm cần chú ý: pipeline hiện có xu hướng set `VITE_API_BASE_URL = <backend_url>/api` trong trường hợp `_API_BASE_URL` rỗng. Trong khi code frontend hiện tự thêm `/api/...` vào request -> dễ tạo lỗi `/api/api/...`.

### 7.4 Script deploy Windows (`New_Frontend/deploy-gcp.ps1`)

- Deploy backend từ source, auto generate `SECRET_KEY`.
- Deploy frontend từ source, set build env var `VITE_API_BASE_URL=$BACKEND_URL/api` (cùng rủi ro double `/api` như trên).

---

## 8) Backup & vận hành (gợi ý)

### 8.1 Database

- Dev (SQLite): backup bằng cách copy file `backend/smart_travel.db` khi backend dừng.
- Prod (Cloud SQL):
  - bật automated backups + PITR
  - schedule export ra GCS (SQL dump) theo ngày/tuần
  - có quy trình restore thử nghiệm định kỳ

### 8.2 Images (GCS)

- Bật bucket versioning + lifecycle policy (giữ version N ngày).
- Đặt naming convention ổn định (hiện code có hardcode bucket và format tên ảnh).

### 8.3 Logs/Monitoring

- Backend đã có structured logs + request id.
- Khuyến nghị thêm:
  - Sentry/Cloud Error Reporting
  - Metrics (latency, rate-limit hits, DB errors)

---

## 9) Testing

### 9.1 Backend

Có pytest async tại `backend/tests/`:

```bash
cd New_Frontend/backend
pytest
```

### 9.2 Frontend

Có vitest scripts trong `package.json` nhưng hiện chưa thấy test suite thực tế.

---

## 10) Vấn đề hiện tại (theo mức độ) & cách khắc phục

### Critical

1) **Lộ secrets trong git**
   - Các file đang chứa credentials thực và đang được track:
     - `New_Frontend/backend/run-env.yaml`
     - `New_Frontend/backend/env-vars.txt`
     - `New_Frontend/backend/env-vars.yaml`
   - Hành động khuyến nghị:
     - rotate toàn bộ secrets đã lộ (DB password, email API key, JWT secret…)
     - di chuyển secrets sang GCP Secret Manager
     - commit lại các file dạng `*.example` chỉ chứa key names (không có value)

2) **Mâu thuẫn quy ước `VITE_API_BASE_URL` (có/không có `/api`)**
   - Code frontend hiện **tự thêm `/api/...`**.
   - Một số tài liệu/script/pipeline lại set base URL **có `/api`** -> dẫn đến `/api/api/...`.
   - Cách khắc phục:
     - chọn 1 quy ước duy nhất và update README + `cloudbuild.yaml` + `deploy-gcp.ps1` tương ứng
     - (tốt hơn) thêm normalize ở frontend: nếu base URL kết thúc bằng `/api` thì strip.

### High

3) **Frontend gọi endpoint không tồn tại**
   - `getNewestRestaurants()` gọi `/api/restaurants/newest` nhưng backend không có.
   - `src/services/temp_test.ts` đang test endpoint này.
   - Cách khắc phục: implement endpoint `/api/restaurants/newest` hoặc xoá/đổi sang sort theo created_at/rating.

4) **Mismatch schema reviews (`reply`)**
   - Backend trả `reply` dạng object `{content, created_at, restaurant_name}`.
   - Frontend đang coi `reply` là string và render trực tiếp -> có thể ra `[object Object]`.

### Medium

5) **Docs lệch code**
   - `New_Frontend/docs/API_SCHEMA_DOCUMENTATION.md` mô tả các file không tồn tại (`src/types/*`, `src/services/api.service.ts`).

6) **Migrations chưa “production-grade”**
   - Có dependency `alembic` nhưng không dùng.
   - Endpoint `/api/admin/migrate-db` với SQLite hiện drop table reviews (rủi ro mất dữ liệu/đứt runtime).

7) **N+1 queries**
   - Bookings & Reviews enrichment đang query theo vòng lặp (có thể chậm khi data lớn).

8) **Frontend state management chưa thống nhất**
   - App dùng local state + localStorage trong khi repo có Zustand + React Query nhưng chưa được wire.

### Low

9) **Một số trang còn mock**
   - Bookings/Reviews/Chatbot chủ yếu mock UI; chưa tận dụng endpoints backend tương ứng.

10) **Hardcode một số tham số infra**
   - Hardcode bucket URL trong seed logic.

---

## 11) Đề xuất cải tiến (roadmap ngắn gọn)

### Ngắn hạn (1–3 ngày)
- Dọn secrets khỏi git, rotate, chuyển sang Secret Manager.
- Chuẩn hoá `VITE_API_BASE_URL` + update `cloudbuild.yaml` + `deploy-gcp.ps1`.
- Fix mismatch `reply` + bỏ/implement `/restaurants/newest`.
- Xoá hoặc đổi mục đích `src/services/temp_test.ts`.

### Trung hạn (1–2 tuần)
- Hoàn thiện migrations bằng Alembic (baseline + migration author_name, nullable user_id, tables mới).
- Refactor API layer frontend (thêm normalize base URL + typed contracts) và quyết định dùng React Query + Zustand hay giữ cách cũ.
- Nối Bookings/Reviews/Chatbot với backend endpoints.

### Dài hạn
- Redis cho cache/rate-limit (nếu scale nhiều instance).
- Observability + monitoring + alerting.
- CI chạy test trước deploy (pytest + vitest).

---

## 12) Tài liệu tham chiếu trong repo

- Tổng quan dự án: `New_Frontend/README.md`
- API backend: `New_Frontend/backend/docs/API.md`
- Phân tích kiến trúc & kế hoạch nâng cấp: `plans/architecture-analysis.md`, `plans/upgrade-plan-10-points.md`
