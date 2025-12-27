# 📖 API Documentation for Frontend Integration

**Version:** 2.0  
**Base URL:** `http://localhost:8000` (development) | Configure for production  
**Last Updated:** December 2025

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Authentication](#-authentication)
3. [Chat API](#-chat-api)
4. [Sessions API](#-sessions-api)
5. [Feedback API](#-feedback-api)
6. [Health Check](#-health-check)
7. [Error Handling](#-error-handling)
8. [Rate Limiting](#-rate-limiting)
9. [CORS Configuration](#-cors-configuration)
10. [WebSocket (Streaming)](#-websocket-streaming)
11. [Examples](#-examples)

---

## 🚀 Quick Start

### 1. Check if backend is running
```bash
curl http://localhost:8000/health
```

### 2. Register a new user
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "SecurePass123!"}'
```

### 3. Login and get token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "SecurePass123!"}'
```

### 4. Send a chat message
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"message": "Tìm quán phở ngon ở Quận 1"}'
```

---

## 🔐 Authentication

### Authentication Flow

```
┌─────────┐      ┌──────────┐      ┌─────────┐
│ Frontend│      │  Backend │      │   JWT   │
└────┬────┘      └────┬─────┘      └────┬────┘
     │                │                  │
     │ POST /auth/login                  │
     │───────────────>│                  │
     │                │  Generate Token  │
     │                │─────────────────>│
     │                │                  │
     │  access_token + refresh_token     │
     │<───────────────│                  │
     │                │                  │
     │ Request with Bearer token         │
     │───────────────>│                  │
     │                │  Validate Token  │
     │                │─────────────────>│
     │                │                  │
     │   Response     │                  │
     │<───────────────│                  │
```

### Endpoints

#### `POST /auth/register` - Register New User
```typescript
// Request
{
  "username": string,      // 3-50 characters, alphanumeric + underscore
  "email": string,         // Valid email format
  "password": string       // Min 8 chars, must include uppercase, lowercase, number
}

// Response (201 Created)
{
  "message": "User registered successfully",
  "user_id": "uuid-string"
}

// Errors
// 400: Username already exists
// 400: Email already registered
// 422: Validation error
```

#### `POST /auth/login` - User Login
```typescript
// Request
{
  "username": string,
  "password": string
}

// Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,           // 15 minutes
  "user": {
    "id": "uuid",
    "username": "testuser",
    "email": "test@example.com",
    "role": "user"
  }
}

// Errors
// 401: Invalid credentials
// 422: Validation error
```

#### `POST /auth/refresh` - Refresh Access Token
```typescript
// Request
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}

// Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}

// Errors
// 401: Invalid or expired refresh token
```

#### `POST /auth/logout` - Logout (Invalidate Token)
```typescript
// Headers
Authorization: Bearer <access_token>

// Response (200 OK)
{
  "message": "Successfully logged out"
}
```

#### `GET /auth/me` - Get Current User Info
```typescript
// Headers
Authorization: Bearer <access_token>

// Response (200 OK)
{
  "id": "uuid",
  "username": "testuser",
  "email": "test@example.com",
  "role": "user",
  "created_at": "2025-01-15T10:30:00Z"
}

// Errors
// 401: Not authenticated
```

#### `POST /auth/guest` - Guest Authentication
```typescript
// Request (no body required)

// Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,    // 1 hour for guests
  "user": {
    "id": "guest-uuid",
    "username": "guest_abc123",
    "role": "guest"
  }
}
```

### Token Storage Recommendations

```javascript
// ✅ Recommended: HttpOnly cookies (if using SSR)
// For SPA apps:

// Store in memory (most secure)
let accessToken = null;

// Or use sessionStorage (cleared on tab close)
sessionStorage.setItem('access_token', token);

// ❌ Avoid: localStorage (vulnerable to XSS)
```

### Auto Refresh Token Logic

```typescript
// axios interceptor example
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000'
});

// Request interceptor - add token
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = getRefreshToken();
        const response = await axios.post('/auth/refresh', { refresh_token: refreshToken });
        
        const { access_token } = response.data;
        setAccessToken(access_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        logout();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);
```

---

## 💬 Chat API

### `POST /api/chat` - Send Chat Message

The main endpoint for AI-powered restaurant recommendations.

```typescript
// Request
{
  "message": string,           // Required: User's query (1-1000 chars)
  "session_id"?: string,       // Optional: Continue existing conversation
  "user_id"?: string,          // Optional: For anonymous users
  "user_location"?: {          // Optional: User's location for distance calc
    "lat": number,
    "lng": number
  }
}

// Response
{
  "message": string,           // AI's response text
  "session_id": string,        // Session ID for follow-up messages
  "restaurants": [             // List of recommended restaurants
    {
      "id": string,
      "name": string,
      "address": string,
      "district": string,
      "rating": number,        // 1-5
      "price_range": string,   // "$", "$$", "$$$", "$$$$"
      "cuisine_types": string[],
      "phone"?: string,
      "opening_hours"?: string,
      "image_url"?: string,
      "distance_km"?: number   // If user_location provided
    }
  ],
  "language": "vi" | "en",     // Detected language
  "confidence": number,        // AI confidence score (0-1)
  "follow_up_questions"?: string[]  // Suggested follow-up questions
}

// Headers
Authorization: Bearer <token>  // Optional for authenticated users
```

### Example Queries

```javascript
// Vietnamese queries (auto-detected)
"Tìm quán phở ngon ở Quận 1"
"Nhà hàng Nhật Bản giá rẻ"
"Quán cà phê có view đẹp gần đây"
"Món Hàn Quốc cho nhóm 10 người"

// English queries
"Best pizza restaurant in District 7"
"Vegetarian restaurants near me"
"Romantic dinner place for anniversary"

// Follow-up queries (with session_id)
"Có quán nào mở cửa sau 10 giờ tối không?"
"Quán này có giao hàng không?"
```

### Response Example

```json
{
  "message": "Dựa trên yêu cầu của bạn, tôi gợi ý 3 quán phở ngon nhất ở Quận 1:\n\n1. **Phở Hòa Pasteur** - Phở bò truyền thống, nước dùng đậm đà\n2. **Phở Lệ** - Phở gà thanh nhẹ, không bột ngọt\n3. **Phở 2000** - Nổi tiếng từ 1990, được Bill Clinton ghé thăm",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "restaurants": [
    {
      "id": "rest_001",
      "name": "Phở Hòa Pasteur",
      "address": "260C Pasteur, Quận 3, TP.HCM",
      "district": "Quận 3",
      "rating": 4.5,
      "price_range": "$$",
      "cuisine_types": ["Vietnamese", "Pho"],
      "phone": "028 3829 7943",
      "opening_hours": "06:00-22:00"
    }
  ],
  "language": "vi",
  "confidence": 0.92,
  "follow_up_questions": [
    "Bạn muốn tìm quán mở cửa sớm hay muộn?",
    "Có cần quán có chỗ đậu xe không?"
  ]
}
```

---

## 📁 Sessions API

### `GET /api/sessions` - List User's Sessions

```typescript
// Headers
Authorization: Bearer <token>  // Required

// Query Parameters
?limit=20                      // Max sessions to return (default: 20)
&offset=0                      // Pagination offset

// Response
{
  "sessions": [
    {
      "id": "uuid",
      "title": "Tìm quán phở...",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:45:00Z",
      "message_count": 5
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

### `GET /api/sessions/{session_id}` - Get Session Details

```typescript
// Headers
Authorization: Bearer <token>  // Required

// Response
{
  "id": "uuid",
  "title": "Tìm quán phở ngon",
  "user_id": "user-uuid",
  "language": "vi",
  "created_at": "2025-01-15T10:30:00Z",
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user",
      "content": "Tìm quán phở ngon ở Quận 1",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "Dựa trên yêu cầu của bạn...",
      "timestamp": "2025-01-15T10:30:05Z",
      "metadata": {
        "restaurants": ["rest_001", "rest_002"]
      }
    }
  ]
}

// Errors
// 403: Access denied (not your session)
// 404: Session not found
```

### `DELETE /api/sessions/{session_id}` - Delete Session

```typescript
// Headers
Authorization: Bearer <token>  // Required

// Response (200 OK)
{
  "message": "Session deleted successfully"
}

// Errors
// 403: Access denied
// 404: Session not found
```

---

## 👍 Feedback API

### `POST /api/feedback` - Submit Feedback

```typescript
// Headers
Authorization: Bearer <token>  // Required

// Request
{
  "session_id": string,        // Required: Session to rate
  "rating": number,            // Required: 1-5 stars
  "message_id"?: string,       // Optional: Specific message to rate
  "restaurant_id"?: string,    // Optional: Rate specific restaurant
  "comment"?: string,          // Optional: User comment (max 1000 chars)
  "feedback_type": "helpful" | "not_helpful" | "wrong_info" | "other"
}

// Response (201 Created)
{
  "id": "feedback-uuid",
  "message": "Feedback submitted successfully"
}
```

### `GET /api/feedback` - Get User's Feedback History

```typescript
// Headers
Authorization: Bearer <token>  // Required

// Response
{
  "feedback": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "rating": 5,
      "comment": "Great recommendations!",
      "created_at": "2025-01-15T10:45:00Z"
    }
  ]
}
```

---

## 🏥 Health Check

### `GET /health` - Basic Health Check

```typescript
// Response (200 OK)
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z"
}

// Response (503 Service Unavailable)
{
  "status": "unhealthy",
  "error": "Database connection failed"
}
```

### `GET /ready` - Comprehensive Readiness

```typescript
// Response (200 OK)
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "faiss_index": "ok",
    "bm25_index": "ok",
    "groq_api": "ok"
  },
  "version": "2.0.0"
}
```

---

## ❌ Error Handling

### Error Response Format

```typescript
{
  "detail": string | {
    "message": string,
    "code": string,
    "field"?: string
  }
}
```

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Success |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Invalid request body |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal error |
| 503 | Service Unavailable | Maintenance mode |

### Handling Errors (React Example)

```typescript
const handleApiError = (error: AxiosError) => {
  const status = error.response?.status;
  const detail = error.response?.data?.detail;
  
  switch (status) {
    case 401:
      // Token expired - try refresh
      return refreshTokenAndRetry(error);
    case 403:
      toast.error('You do not have permission');
      break;
    case 404:
      toast.error('Resource not found');
      break;
    case 422:
      // Validation error
      if (typeof detail === 'object') {
        toast.error(`${detail.field}: ${detail.message}`);
      }
      break;
    case 429:
      toast.warning('Too many requests. Please wait.');
      break;
    default:
      toast.error('An error occurred. Please try again.');
  }
};
```

---

## 🚦 Rate Limiting

### Default Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| All endpoints | 100 requests | 1 minute |
| `/api/chat` | 30 requests | 1 minute |
| `/auth/login` | 5 requests | 1 minute |
| `/auth/register` | 3 requests | 1 minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
```

### Handling Rate Limits

```typescript
if (error.response?.status === 429) {
  const retryAfter = error.response.headers['retry-after'] || 60;
  console.log(`Rate limited. Retry after ${retryAfter}s`);
  
  setTimeout(() => {
    retryRequest();
  }, retryAfter * 1000);
}
```

---

## 🌐 CORS Configuration

### Allowed Origins (Development)

- `http://localhost:3000` (React default)
- `http://localhost:5173` (Vite default)
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

### Production Setup

Add your domain to `.env.production`:
```
CORS_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
```

### CORS Headers Sent

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-CSRF-Token
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 3600
```

---

## 🔌 WebSocket (Streaming)

For real-time streaming responses:

### `WS /ws/chat` - Streaming Chat

```typescript
// Connect
const ws = new WebSocket('ws://localhost:8000/ws/chat');

// Authenticate first
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_access_token'
  }));
};

// Send message
ws.send(JSON.stringify({
  type: 'message',
  content: 'Tìm quán ăn ngon',
  session_id: 'optional-session-id'
}));

// Receive streaming response
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'chunk') {
    // Append to response
    setResponse(prev => prev + data.content);
  } else if (data.type === 'done') {
    // Response complete
    setRestaurants(data.restaurants);
  } else if (data.type === 'error') {
    console.error(data.message);
  }
};
```

---

## 💻 Examples

### React + Axios Complete Example

```typescript
// api/client.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Add auth interceptor
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// api/chat.ts
export interface ChatMessage {
  message: string;
  session_id?: string;
  user_location?: { lat: number; lng: number };
}

export interface ChatResponse {
  message: string;
  session_id: string;
  restaurants: Restaurant[];
  language: string;
}

export const sendMessage = async (data: ChatMessage): Promise<ChatResponse> => {
  const response = await api.post('/api/chat', data);
  return response.data;
};

// components/Chat.tsx
import React, { useState } from 'react';
import { sendMessage } from '../api/chat';

export const Chat: React.FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    
    try {
      const response = await sendMessage({
        message: input,
        session_id: sessionId || undefined,
      });
      
      setSessionId(response.session_id);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.message,
        restaurants: response.restaurants 
      }]);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
            {msg.restaurants && (
              <RestaurantList restaurants={msg.restaurants} />
            )}
          </div>
        ))}
      </div>
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Nhập câu hỏi về nhà hàng..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading}>
          {loading ? 'Đang xử lý...' : 'Gửi'}
        </button>
      </div>
    </div>
  );
};
```

### Vue 3 + Composition API Example

```typescript
// composables/useChat.ts
import { ref } from 'vue';
import { api } from '../api/client';

export function useChat() {
  const messages = ref<Message[]>([]);
  const sessionId = ref<string | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function sendMessage(content: string) {
    loading.value = true;
    error.value = null;
    
    messages.value.push({ role: 'user', content });
    
    try {
      const { data } = await api.post('/api/chat', {
        message: content,
        session_id: sessionId.value,
      });
      
      sessionId.value = data.session_id;
      messages.value.push({
        role: 'assistant',
        content: data.message,
        restaurants: data.restaurants,
      });
    } catch (err) {
      error.value = 'Failed to send message';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return { messages, sessionId, loading, error, sendMessage };
}
```

---

## 📞 Support & Contact

- **API Issues**: Check `/health` and `/ready` endpoints
- **Authentication**: See error messages in 401/403 responses
- **Rate Limiting**: Check `X-RateLimit-*` headers
- **Swagger Docs**: Visit `http://localhost:8000/docs`
- **ReDoc**: Visit `http://localhost:8000/redoc`

---

*Generated for Frontend Team - December 2025*
