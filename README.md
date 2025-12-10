# HCM Restaurants Dataset

Dataset chứa thông tin về **2057 nhà hàng/quán ăn tại TP.HCM**, được thu thập từ Google Maps và xử lý bằng Machine Learning.

---

## 📦 Files Dataset

### 1. `hcm_restaurants_chatbot.json`
**Mục đích:** Training chatbot, RAG, semantic search  
**Số lượng:** 2057 quán  
**Kích thước:** ~15MB

**Nội dung:**
```json
{
  "name": "Tên quán",
  "address": "Địa chỉ đầy đủ",
  "phone": "Số điện thoại",
  "website": "Website URL",
  "category": "Loại hình (Nhà hàng/Quán ăn/Cafe)",
  "rating": 4.5,
  "rating_count": 1000,
  "price_level": "PRICE_LEVEL_MODERATE",
  "opening_hours": {
    "Thứ Hai": "07:00–22:00",
    ...
  },
  "food_tags": ["cơm", "món nước", "món xào"],
  "comments": [
    {
      "author": "Tên người review",
      "rating": 5,
      "text": "Nội dung review",
      "date": "10/12/2025"
    }
  ],
  "coordinates": {
    "lat": 10.7769,
    "lon": 106.7009
  },
  "original_url": "Google Maps URL",
  "location_summary": "District 1 (Premium)",
  "type_summary": "Restaurant + Cafe",
  "contact_summary": "Has website & phone",
  "price_level_source": "original/predicted"
}
```

**Sử dụng:**
- ✅ Training chatbot AI
- ✅ Semantic search
- ✅ Recommendation system
- ✅ Data analysis
- ❌ Không có ảnh

---

### 2. `hcm_restaurants_frontend.json`
**Mục đích:** Hiển thị trên website/mobile app  
**Số lượng:** 968 quán (chỉ quán có ảnh)  
**Kích thước:** ~12MB

**Nội dung:**
```json
{
  "name": "Tên quán",
  "address": "Địa chỉ",
  "phone": "Số điện thoại",
  "website": "Website URL",
  "category": "Loại hình",
  "rating": 4.5,
  "rating_count": 1000,
  "price_level": "PRICE_LEVEL_MODERATE",
  "opening_hours": {...},
  "food_tags": ["cơm", "món nước"],
  "comments": [...],
  "coordinates": {
    "lat": 10.7769,
    "lon": 106.7009
  },
  "hosted_images": [
    "https://habi.software/images/NHÀ_HÀNG_NGON_1.jpg",
    "https://habi.software/images/NHÀ_HÀNG_NGON_2.jpg",
    "https://habi.software/images/NHÀ_HÀNG_NGON_3.jpg"
  ],
  "location_summary": "District 1 (Premium)",
  "type_summary": "Restaurant + Cafe",
  "contact_summary": "Has website & phone"
}
```

**Sử dụng:**
- ✅ Hiển thị danh sách quán
- ✅ Chi tiết quán (có ảnh)
- ✅ Google Maps integration
- ✅ Gallery/slideshow
- ⚠️ Chỉ có quán có ảnh (968/2057)

---

### 3. `hcm_restaurants_backend.json`
**Mục đích:** Backend API, database  
**Số lượng:** 968 quán (chỉ quán có ảnh)  
**Kích thước:** ~15MB

**Nội dung:** Tất cả fields từ Frontend + thêm:
```json
{
  ...tất cả fields của frontend,
  "local_images": [
    "images\\NHÀ_HÀNG_NGON_1.jpg",
    "images\\NHÀ_HÀNG_NGON_2.jpg",
    "images\\NHÀ_HÀNG_NGON_3.jpg"
  ],
  "original_url": "Google Maps URL",
  "engagement_score": 39.26,
  "price_level_source": "original"
}
```

**Sử dụng:**
- ✅ REST API endpoints
- ✅ Database seeding
- ✅ Admin dashboard
- ✅ File management (local_images)
- ✅ Analytics & metrics

---

## 📊 Data Fields Explanation

### Price Levels
- `PRICE_LEVEL_FREE` (0) - Miễn phí
- `PRICE_LEVEL_INEXPENSIVE` (1) - Rẻ (< 100k/người)
- `PRICE_LEVEL_MODERATE` (2) - Trung bình (100-300k/người)
- `PRICE_LEVEL_EXPENSIVE` (3) - Đắt (300-500k/người)
- `PRICE_LEVEL_VERY_EXPENSIVE` (4) - Rất đắt (> 500k/người)

### Location Summary
- `District X (Premium)` - Quận cao cấp (1, 2, 3, 7, Phú Nhuận, Bình Thạnh)
- `District X` - Quận khác
- `Tên quận (Premium)` - Quận có tên và cao cấp

### Price Level Source
- `original` - Dữ liệu từ Google Places API (773 quán)
- `predicted` - Dự đoán bằng ML RandomForest (1284 quán, accuracy 88.39%)

---

## 🔧 ML Model Information

**Model:** RandomForestClassifier
- **Accuracy:** 88.39%
- **Training data:** 773 quán có price_level
- **Predicted:** 1284 quán thiếu price_level
- **Features:** 25 features (rating, location, keywords, engagement...)

**Top Features:**
1. `engagement_score` (19.4%) - rating × log(rating_count) + comments×0.5 + images×0.2
2. `rating_count` (18.1%)
3. `rating` (13.8%)
4. `num_food_tags` (10.5%)
5. `district` (8.7%)

---

## 📁 Images Folder

### Tổng quan
**Location:** `D:\data\images\`  
**Tổng số file:** 10,000+ image files  
**Format:** JPG/JPEG  
**Kích thước folder:** ~2.5GB

### Naming Convention
Images được đặt tên theo pattern:
```
Tên_Quán_1.jpg    # Ảnh đầu tiên
Tên_Quán_2.jpg    # Ảnh thứ hai
Tên_Quán_3.jpg    # Ảnh thứ ba
```

**Quy tắc đặt tên:**
- Tên quán được normalize: bỏ dấu, viết thường, thay khoảng trắng bằng `_`
- Mỗi quán có từ 1-3 ảnh
- Suffix `_1`, `_2`, `_3` để phân biệt ảnh

**Ví dụ:**
```
NHÀ_HÀNG_NGON_1.jpg
NHÀ_HÀNG_NGON_2.jpg
NHÀ_HÀNG_NGON_3.jpg
PHỞ_24_GIA_LAI_1.jpg
PHỞ_24_GIA_LAI_2.jpg
```

### Image Matching Process
**Algorithm:** Fuzzy String Matching (SequenceMatcher)  
**Threshold:** 95% similarity  
**Coverage:** 968/2057 quán (47%)

**Quy trình matching:**
1. Normalize tên quán và tên file (bỏ dấu, lowercase)
2. So sánh similarity score giữa tên quán và tên file
3. Chỉ match nếu similarity >= 95%
4. Tìm tất cả ảnh có suffix `_1`, `_2`, `_3`
5. Tạo 2 paths:
   - `local_images`: `images\\Tên_File.jpg` (cho backend)
   - `hosted_images`: `https://habi.software/images/Tên_File.jpg` (cho frontend)

**Kết quả:**
- ✅ 968 quán matched thành công (chất lượng cao, 95% accuracy)
- ❌ 1089 quán không có ảnh local
- ⚠️ Các quán không match được loại khỏi frontend/backend JSON

### Image Hosting
**Production URL:** `https://habi.software/images/`  
**Local path:** `D:\data\images\`

**Lưu ý:**
- Frontend sử dụng `hosted_images` URLs
- Backend lưu cả `local_images` và `hosted_images`
- Chatbot không cần ảnh

### Statistics
- **Total images:** 10,000+ files
- **Restaurants với ảnh:** 968 (47%)
- **Restaurants không ảnh:** 1089 (53%)
- **Average images/restaurant:** ~3 ảnh

---

## 🚀 Usage Examples

### Load data trong Python
```python
import json

# For chatbot
with open('hcm_restaurants_chatbot.json', 'r', encoding='utf-8') as f:
    chatbot_data = json.load(f)

# For frontend
with open('hcm_restaurants_frontend.json', 'r', encoding='utf-8') as f:
    frontend_data = json.load(f)

# For backend
with open('hcm_restaurants_backend.json', 'r', encoding='utf-8') as f:
    backend_data = json.load(f)
```

### Filter premium restaurants
```python
premium = [r for r in frontend_data if 'Premium' in r['location_summary']]
```

### Get highly rated restaurants
```python
top_rated = [r for r in frontend_data if r['rating'] >= 4.5 and r['rating_count'] > 100]
```

---

## 📝 Notes

1. **Google Places API** đã bị khóa → Không thể lấy thêm dữ liệu mới
2. **Images** từ Google API URLs đã hết hạn → Chỉ dùng `hosted_images`
3. **Price levels** 1284/2057 quán được predict bằng ML (xem `price_level_source`)
4. **Chatbot file** có đầy đủ 2057 quán, không cần ảnh
5. **Frontend/Backend files** chỉ có 968 quán có ảnh

---

## 📧 Contact

Dataset được tạo bởi: Khánh Linh
Date: December 10, 2025  
Version: 1.0
