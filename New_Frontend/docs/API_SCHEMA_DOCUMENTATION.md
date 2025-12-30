# 📚 Smart Travel System - API Schema Documentation

> **Ngày tạo:** 09/12/2024  
> **Phiên bản:** 1.0.0  
> **Tác giả:** GitHub Copilot  

---

## 📋 Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Cấu trúc file đã tạo](#2-cấu-trúc-file-đã-tạo)
3. [Chi tiết các thay đổi](#3-chi-tiết-các-thay-đổi)
4. [Standard API Response Format](#4-standard-api-response-format)
5. [API Endpoints & Schemas](#5-api-endpoints--schemas)
6. [Error Handling](#6-error-handling)
7. [Thuật toán & Phương thức sử dụng](#7-thuật-toán--phương-thức-sử-dụng)
8. [Điểm mạnh & Lợi ích](#8-điểm-mạnh--lợi-ích)
9. [Hướng dẫn sử dụng](#9-hướng-dẫn-sử-dụng)

---

## 1. Tổng quan

### 🎯 Mục đích
Tạo một **Standard API Schema** thống nhất cho dự án Smart Travel System, giúp:
- Frontend và Backend dễ dàng giao tiếp với nhau
- Đảm bảo tính nhất quán trong cấu trúc dữ liệu
- Giảm thiểu lỗi do không đồng bộ giữa các team
- Tăng tốc độ phát triển

### 🔧 Công nghệ sử dụng
| Công nghệ | Phiên bản | Mục đích |
|-----------|-----------|----------|
| TypeScript | 5.x | Type safety, IntelliSense |
| React | 18.3.1 | Frontend framework |
| Vite | 6.3.5 | Build tool |

---

## 2. Cấu trúc file đã tạo

```
src/
├── types/                          # 📁 Type definitions
│   ├── index.ts                    # ✅ Export tất cả types
│   ├── api.types.ts                # ✅ Định nghĩa interfaces & types
│   └── api.examples.ts             # ✅ Mẫu JSON request/response
│
├── services/                       # 📁 API services
│   ├── index.ts                    # ✅ Export tất cả services
│   └── api.service.ts              # ✅ HTTP client & API methods
│
└── docs/                           # 📁 Documentation
    └── API_SCHEMA_DOCUMENTATION.md # ✅ File này
```

### 📄 Chi tiết từng file

| File | Dòng code | Mô tả |
|------|-----------|-------|
| `api.types.ts` | ~620 | Định nghĩa tất cả interfaces, types, error codes |
| `api.service.ts` | ~620 | HTTP client, token management, API methods |
| `api.examples.ts` | ~450 | JSON samples cho backend reference |
| `index.ts` (types) | ~10 | Re-export types |
| `index.ts` (services) | ~8 | Re-export services |

---

## 3. Chi tiết các thay đổi

### 3.1 File đã chỉnh sửa

#### 📝 `package.json`
| Thay đổi | Trước | Sau | Lý do |
|----------|-------|-----|-------|
| `date-fns` version | `"^4"` | `"^3.6.0"` | Xung đột dependency với `react-day-picker@8.10.1` (yêu cầu `date-fns@^2.28.0 \|\| ^3.0.0`) |

**Lỗi gặp phải:**
```
npm error ERESOLVE unable to resolve dependency tree
npm error peer date-fns@"^2.28.0 || ^3.0.0" from react-day-picker@8.10.1
```

### 3.2 Files đã tạo mới

| File | Mục đích |
|------|----------|
| `src/types/api.types.ts` | Định nghĩa TypeScript interfaces cho tất cả API |
| `src/types/api.examples.ts` | Mẫu JSON để backend team tham khảo |
| `src/types/index.ts` | Barrel export cho types |
| `src/services/api.service.ts` | HTTP client và API helper functions |
| `src/services/index.ts` | Barrel export cho services |

---

## 4. Standard API Response Format

### 4.1 Generic Response Wrapper

```typescript
interface ApiResponse<T = unknown> {
  success: boolean;        // Trạng thái request
  data: T | null;          // Dữ liệu trả về
  message: string;         // Thông báo cho user
  error?: ApiError | null; // Chi tiết lỗi (nếu có)
  meta?: ApiMeta;          // Metadata (pagination, timestamp...)
}
```

### 4.2 Ví dụ Response

#### ✅ Success Response
```json
{
  "success": true,
  "data": {
    "id": "rst_001",
    "name": "Phở Hà Nội",
    "rating": 4.8
  },
  "message": "Lấy thông tin nhà hàng thành công",
  "error": null,
  "meta": {
    "timestamp": "2024-12-09T09:00:00Z",
    "requestId": "req_xyz789"
  }
}
```

#### ❌ Error Response
```json
{
  "success": false,
  "data": null,
  "message": "Email hoặc mật khẩu không đúng",
  "error": {
    "code": "E1001",
    "message": "Invalid credentials",
    "details": {
      "email": ["Email không hợp lệ"]
    }
  },
  "meta": {
    "timestamp": "2024-12-09T09:00:00Z"
  }
}
```

### 4.3 Pagination Format

```typescript
interface PaginationMeta {
  page: number;       // Trang hiện tại
  limit: number;      // Số item mỗi trang
  total: number;      // Tổng số items
  totalPages: number; // Tổng số trang
  hasNext: boolean;   // Có trang tiếp theo?
  hasPrev: boolean;   // Có trang trước?
}
```

---

## 5. API Endpoints & Schemas

### 5.1 Authentication APIs

| Method | Endpoint | Request Type | Response Type |
|--------|----------|--------------|---------------|
| POST | `/api/auth/login` | `LoginRequest` | `LoginResponse` |
| POST | `/api/auth/register/start` | `RegisterStartRequest` | `{ email: string }` |
| POST | `/api/auth/register/verify` | `RegisterVerifyRequest` | `LoginResponse` |
| POST | `/api/auth/refresh` | `RefreshTokenRequest` | `RefreshTokenResponse` |
| POST | `/api/auth/logout` | `LogoutRequest` | `void` |
| POST | `/api/auth/forgot-password` | `{ email: string }` | `{ message: string }` |
| POST | `/api/auth/reset-password` | `{ email: string; otp: string; new_password: string; confirm_password: string }` | `{ message: string }` |

### 5.2 Restaurant APIs

| Method | Endpoint | Request Type | Response Type |
|--------|----------|--------------|---------------|
| GET | `/api/restaurants` | `GetRestaurantsRequest` | `Restaurant[]` |
| GET | `/api/restaurants/:id` | - | `Restaurant` |
| GET | `/api/restaurants/:id/menu` | `GetMenuItemsRequest` | `MenuItem[]` |
| GET | `/api/restaurants/:id/reviews` | `GetReviewsRequest` | `Review[]` |
| GET | `/api/restaurants/search` | `{ q: string }` | `Restaurant[]` |

### 5.3 Booking APIs

| Method | Endpoint | Request Type | Response Type |
|--------|----------|--------------|---------------|
| GET | `/api/bookings` | `GetBookingsRequest` | `Booking[]` |
| GET | `/api/bookings/:id` | - | `Booking` |
| POST | `/api/bookings` | `CreateBookingRequest` | `Booking` |
| PUT | `/api/bookings/:id` | `UpdateBookingRequest` | `Booking` |
| DELETE | `/api/bookings/:id` | `CancelBookingRequest` | `Booking` |

### 5.4 Review APIs

| Method | Endpoint | Request Type | Response Type |
|--------|----------|--------------|---------------|
| GET | `/api/reviews/me` | - | `Review[]` |
| POST | `/api/reviews` | `CreateReviewRequest` | `Review` |
| PUT | `/api/reviews/:id` | `Partial<CreateReviewRequest>` | `Review` |
| DELETE | `/api/reviews/:id` | - | `void` |
| POST | `/api/reviews/:id/like` | - | `{ likes: number }` |

### 5.5 Chat APIs

| Method | Endpoint | Request Type | Response Type |
|--------|----------|--------------|---------------|
| POST | `/api/chat/message` | `SendMessageRequest` | `SendMessageResponse` |
| GET | `/api/chat/history` | - | `ChatSession[]` |
| GET | `/api/chat/:id` | - | `ChatSession` |
| DELETE | `/api/chat/:id` | - | `void` |

### 5.6 Other APIs

| Method | Endpoint | Request Type | Response Type |
|--------|----------|--------------|---------------|
| POST | `/api/contact` | `ContactFormRequest` | `ContactFormResponse` |
| GET | `/api/search` | `SearchRequest` | `SearchResponse` |

---

## 6. Error Handling

### 6.1 Error Codes

```typescript
const API_ERROR_CODES = {
  // 🔐 Authentication Errors (1xxx)
  AUTH_INVALID_CREDENTIALS: 'E1001',  // Sai email/password
  AUTH_TOKEN_EXPIRED: 'E1002',         // Token hết hạn
  AUTH_TOKEN_INVALID: 'E1003',         // Token không hợp lệ
  AUTH_UNAUTHORIZED: 'E1004',          // Chưa đăng nhập
  AUTH_EMAIL_EXISTS: 'E1005',          // Email đã tồn tại
  AUTH_EMAIL_NOT_VERIFIED: 'E1007',    // Email chưa xác thực
  
  // ✅ Validation Errors (2xxx)
  VALIDATION_ERROR: 'E2001',           // Lỗi validation chung
  INVALID_INPUT: 'E2002',              // Input không hợp lệ
  MISSING_REQUIRED_FIELD: 'E2003',     // Thiếu field bắt buộc
  
  // 🔍 Resource Errors (3xxx)
  RESOURCE_NOT_FOUND: 'E3001',         // Resource không tìm thấy
  RESTAURANT_NOT_FOUND: 'E3002',       // Nhà hàng không tồn tại
  BOOKING_NOT_FOUND: 'E3003',          // Booking không tồn tại
  USER_NOT_FOUND: 'E3004',             // User không tồn tại
  REVIEW_NOT_FOUND: 'E3005',           // Review không tồn tại
  
  // 💼 Business Logic Errors (4xxx)
  BOOKING_SLOT_UNAVAILABLE: 'E4001',   // Slot đặt bàn đã hết
  BOOKING_CANNOT_CANCEL: 'E4002',      // Không thể hủy booking
  RESTAURANT_CLOSED: 'E4003',          // Nhà hàng đã đóng cửa
  MAX_GUESTS_EXCEEDED: 'E4004',        // Vượt quá số khách tối đa
  REVIEW_ALREADY_EXISTS: 'E4005',      // Đã đánh giá rồi
  
  // 🔥 Server Errors (5xxx)
  INTERNAL_SERVER_ERROR: 'E5001',      // Lỗi server
  DATABASE_ERROR: 'E5002',             // Lỗi database
  EXTERNAL_SERVICE_ERROR: 'E5003',     // Lỗi service bên ngoài
};
```

### 6.2 HTTP Status Codes

| Code | Constant | Ý nghĩa |
|------|----------|---------|
| 200 | `OK` | Thành công |
| 201 | `CREATED` | Tạo mới thành công |
| 204 | `NO_CONTENT` | Thành công, không có data |
| 400 | `BAD_REQUEST` | Request không hợp lệ |
| 401 | `UNAUTHORIZED` | Chưa xác thực |
| 403 | `FORBIDDEN` | Không có quyền |
| 404 | `NOT_FOUND` | Không tìm thấy |
| 409 | `CONFLICT` | Xung đột dữ liệu |
| 422 | `UNPROCESSABLE_ENTITY` | Validation error |
| 429 | `TOO_MANY_REQUESTS` | Rate limit |
| 500 | `INTERNAL_SERVER_ERROR` | Lỗi server |

---

## 7. Thuật toán & Phương thức sử dụng

### 7.1 Token Management

**Thuật toán:** JWT (JSON Web Token) với Refresh Token rotation

```
┌─────────────────────────────────────────────────────────────┐
│                    TOKEN FLOW                                │
├─────────────────────────────────────────────────────────────┤
│  1. User login → Nhận accessToken + refreshToken            │
│  2. accessToken lưu trong memory (biến JS)                  │
│  3. refreshToken lưu trong localStorage                     │
│  4. Mỗi request gửi accessToken trong Authorization header  │
│  5. Nếu accessToken hết hạn (401) → Auto refresh            │
│  6. Nếu refresh thành công → Retry request ban đầu          │
│  7. Nếu refresh thất bại → Logout user                      │
└─────────────────────────────────────────────────────────────┘
```

**Code implementation:**
```typescript
// Token storage
let accessToken: string | null = null;
let refreshToken: string | null = null;

// Auto refresh mechanism
if (response.status === 401 && !skipAuth) {
  const refreshed = await refreshAccessToken();
  if (refreshed) {
    return apiRequest<T>(endpoint, options); // Retry
  }
  clearTokens(); // Logout
}
```

### 7.2 HTTP Client với Timeout

**Phương thức:** AbortController pattern

```typescript
async function fetchWithTimeout(url: string, options: RequestOptions = {}): Promise<Response> {
  const { timeout = 30000, ...fetchOptions } = options;
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}
```

**Lợi ích:**
- Tránh request treo vô hạn
- User experience tốt hơn
- Resource management hiệu quả

### 7.3 Generic Type Pattern

**Phương thức:** TypeScript Generics

```typescript
// Generic API Response
interface ApiResponse<T = unknown> {
  success: boolean;
  data: T | null;
  message: string;
}

// Sử dụng
type GetRestaurantsResponse = ApiResponse<Restaurant[]>;
type GetUserResponse = ApiResponse<User>;
```

**Lợi ích:**
- Type safety tại compile time
- IntelliSense support
- Giảm code duplication

### 7.4 Barrel Export Pattern

**Phương thức:** Re-export từ index.ts

```typescript
// src/types/index.ts
export * from './api.types';
export { API_EXAMPLES } from './api.examples';

// src/services/index.ts  
export { default as api } from './api.service';
export * from './api.service';
```

**Lợi ích:**
- Import gọn gàng: `import { User, api } from '@/types'`
- Encapsulation tốt hơn
- Dễ refactor

### 7.5 Query String Builder

**Phương thức:** URLSearchParams API

```typescript
const queryString = params
  ? '?' + new URLSearchParams(params as unknown as Record<string, string>).toString()
  : '';
```

**Lợi ích:**
- URL encoding tự động
- Handle special characters
- Cross-browser compatible

---

## 8. Điểm mạnh & Lợi ích

### 8.1 Điểm mạnh

| # | Điểm mạnh | Mô tả |
|---|-----------|-------|
| 1 | **Type Safety** | TypeScript interfaces đảm bảo đúng kiểu dữ liệu tại compile time |
| 2 | **Consistency** | Tất cả API responses đều theo cùng 1 format |
| 3 | **Documentation** | Code tự document với JSDoc comments |
| 4 | **Error Handling** | Hệ thống error codes rõ ràng, dễ debug |
| 5 | **Auto Refresh** | Token tự động refresh, user không bị logout đột ngột |
| 6 | **Timeout Protection** | Request không bị treo vô hạn |
| 7 | **Modular Design** | Dễ mở rộng, thêm API mới dễ dàng |
| 8 | **Backend Reference** | File examples giúp backend team hiểu rõ format |

### 8.2 Lợi ích cho từng team

#### 🎨 Frontend Team
- IntelliSense support đầy đủ
- Giảm bugs do sai kiểu dữ liệu
- Không cần đọc docs, chỉ cần hover để xem type
- Auto-complete khi coding

#### ⚙️ Backend Team
- Biết chính xác format cần trả về
- Error codes chuẩn hóa
- JSON examples để tham khảo
- Contract rõ ràng với frontend

#### 🔄 Communication
- Single source of truth cho API contracts
- Giảm miscommunication
- Dễ review changes

### 8.3 So sánh trước/sau

| Aspect | Trước | Sau |
|--------|-------|-----|
| **Type checking** | Runtime errors | Compile-time errors |
| **API format** | Không nhất quán | Chuẩn hóa hoàn toàn |
| **Error handling** | Ad-hoc | Systematic với error codes |
| **Token refresh** | Manual | Automatic |
| **Documentation** | Riêng lẻ | Integrated trong code |
| **Import statements** | Dài dòng | Gọn gàng với barrel exports |

---

## 9. Hướng dẫn sử dụng

### 9.1 Import types

```typescript
// Import specific types
import type { 
  User, 
  Restaurant, 
  Booking,
  ApiResponse,
  LoginRequest 
} from '@/types';

// Import all
import * as Types from '@/types';
```

### 9.2 Sử dụng API service

```typescript
import { api } from '@/services';

// Authentication
const loginResult = await api.auth.login({
  email: 'user@example.com',
  password: 'password123'
});

if (loginResult.success) {
  const user = loginResult.data.user;
  api.setTokens(loginResult.data.accessToken, loginResult.data.refreshToken);
}

// Get restaurants
const restaurants = await api.restaurant.getRestaurants({
  cuisine: 'pho',
  rating: 4,
  sortBy: 'rating'
});

// Create booking
const booking = await api.booking.createBooking({
  restaurantId: 'rst_001',
  date: '2024-12-15',
  time: '19:00',
  guests: 4,
  customerName: 'Nguyễn Văn A',
  customerPhone: '0912345678'
});
```

### 9.3 Error handling

```typescript
import { API_ERROR_CODES } from '@/types';

const result = await api.auth.login(credentials);

if (!result.success) {
  switch (result.error?.code) {
    case API_ERROR_CODES.AUTH_INVALID_CREDENTIALS:
      toast.error('Email hoặc mật khẩu không đúng');
      break;
    case API_ERROR_CODES.AUTH_EMAIL_NOT_VERIFIED:
      toast.warning('Vui lòng xác thực email');
      break;
    default:
      toast.error(result.message);
  }
}
```

### 9.4 Custom hooks (gợi ý)

```typescript
// hooks/useAuth.ts
import { useState } from 'react';
import { api } from '@/services';
import type { User, LoginRequest } from '@/types';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);

  const login = async (credentials: LoginRequest) => {
    setLoading(true);
    const result = await api.auth.login(credentials);
    setLoading(false);
    
    if (result.success && result.data) {
      setUser(result.data.user);
      api.setTokens(result.data.accessToken, result.data.refreshToken);
      return true;
    }
    return false;
  };

  const logout = async () => {
    await api.auth.logout();
    api.clearTokens();
    setUser(null);
  };

  return { user, loading, login, logout };
}
```

---

## 📝 Ghi chú thêm

### Environment Variables

Tạo file `.env` tại root:
```env
# Can be backend root or backend /api prefix (both supported)
VITE_API_BASE_URL=http://localhost:8000
# VITE_API_BASE_URL=http://localhost:8000/api
```

### Cần cài thêm (optional)

```bash
# Nếu muốn validation với Zod
npm install zod @hookform/resolvers

# Nếu muốn state management
npm install zustand

# Nếu muốn data fetching với caching
npm install @tanstack/react-query
```

---

> **📌 Lưu ý:** File này nên được cập nhật khi có thay đổi về API schema.

---
