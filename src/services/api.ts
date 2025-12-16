import { API_URL } from "./config";
import { getAuthHeaders } from "./auth";

// Types matching backend API response
export interface ApiRestaurant {
  id: string;
  name: string;
  description?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  cuisine?: string;
  price_level?: number;
  rating?: number;
  review_count?: number;
  open_time?: string;
  close_time?: string;
  distance?: number | null;
  image?: string;
  images?: string[];
  is_open?: boolean;
  specialty?: string[];
  menu?: ApiMenuItem[];
}

export interface ApiMenuItem {
  id: string;
  restaurant_id?: string;
  name: string;
  description?: string | null;
  price: number;
  image?: string | null;
  category: string;
}

export interface ApiReview {
  id: string;
  restaurant_id: string;
  user_id?: string | null;
  user_name?: string;
  user_avatar?: string | null;
  author_name?: string;
  rating: number;
  title?: string | null;
  content?: string;
  images?: string[];
  likes?: number;
  sentiment_score?: number | null;
  sentiment_polarity?: number | null;
  sentiment_subjectivity?: number | null;
  is_verified?: boolean;
  visit_date?: string;
  reply?: {
    content: string;
    created_at?: string | null;
    restaurant_name?: string | null;
  } | null;
  created_at?: string;
  updated_at?: string;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string | null;
  meta?: {
    timestamp: string;
    pagination?: PaginationMeta;
  };
}

export interface SitePage {
  slug: string;
  title: string;
  body: string;
  updated_by?: string | null;
  created_at: string;
  updated_at: string;
}

// Frontend types (matching App.tsx interface)
export interface MenuItem {
  id: string;
  name: string;
  description: string;
  price: number;
  image: string;
  category: string;
}

export interface Restaurant {
  id: string;
  name: string;
  image: string;
  images: string[];
  cuisine: string;
  rating: number;
  reviewCount: number;
  priceLevel: number;
  distance: string;
  openTime: string;
  specialty: string[];
  description: string;
  address: string;
  phone: string;
  menu: MenuItem[];
}

// Convert API restaurant to frontend Restaurant format
export function mapApiRestaurantToFrontend(apiRestaurant: ApiRestaurant): Restaurant {
  const mergedImages = Array.from(
    new Set(
      [apiRestaurant.image, ...(apiRestaurant.images || [])].filter(
        (u): u is string => Boolean(u && typeof u === "string"),
      ),
    ),
  );

  const primaryImage = mergedImages[0] || "";

  const menu: MenuItem[] = Array.isArray(apiRestaurant.menu)
    ? apiRestaurant.menu.map((item) => ({
        id: item.id,
        name: item.name,
        description: item.description || "",
        price: typeof item.price === "number" ? item.price : Number(item.price) || 0,
        image: item.image || "",
        category: item.category || "Khác",
      }))
    : [];

  return {
    id: apiRestaurant.id,
    name: apiRestaurant.name,
    image: primaryImage,
    images: mergedImages.length ? mergedImages : [primaryImage],
    cuisine: apiRestaurant.cuisine || 'Ẩm thực Việt Nam',
    rating: apiRestaurant.rating || 4.0,
    reviewCount: apiRestaurant.review_count || 0,
    priceLevel: apiRestaurant.price_level || 2,
    distance:
      apiRestaurant.distance !== null && apiRestaurant.distance !== undefined
        ? `${apiRestaurant.distance} km`
        : "Chưa xác định",
    openTime: formatOpenTime(apiRestaurant.open_time, apiRestaurant.close_time),
    specialty: apiRestaurant.specialty || [],
    description: apiRestaurant.description || '',
    address: apiRestaurant.address || '',
    phone: apiRestaurant.phone || '',
    menu,
  };
}

function formatOpenTime(openTime?: string, closeTime?: string): string {
  if (!openTime) return '7:00 - 22:00';
  const open = openTime?.substring(0, 5) || '07:00';
  const close = closeTime?.substring(0, 5) || '22:00';
  return `${open} - ${close}`;
}

// API Functions
export interface FetchRestaurantsParams {
  limit?: number;
  page?: number;
  search?: string;
  cuisine?: string;
  price_level?: number;
  rating?: number;
  sort_by?: "rating" | "price" | "name";
  sort_order?: "asc" | "desc";
}

export async function fetchRestaurantsPage(
  params: FetchRestaurantsParams = {},
): Promise<{ restaurants: Restaurant[]; pagination: PaginationMeta | null }> {
  const {
    limit = 24,
    page = 1,
    search,
    cuisine,
    price_level,
    rating,
    sort_by,
    sort_order,
  } = params;

  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("page", String(page));

  const trimmedSearch = (search || "").trim();
  if (trimmedSearch) qs.set("search", trimmedSearch);

  const trimmedCuisine = (cuisine || "").trim();
  if (trimmedCuisine) qs.set("cuisine", trimmedCuisine);

  if (typeof price_level === "number" && price_level > 0) qs.set("price_level", String(price_level));
  if (typeof rating === "number") qs.set("rating", String(rating));
  if (sort_by) qs.set("sort_by", sort_by);
  if (sort_order) qs.set("sort_order", sort_order);

  const response = await fetch(`${API_URL}/restaurants?${qs.toString()}`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const result: ApiResponse<ApiRestaurant[]> = await response.json();
  if (result.success && Array.isArray(result.data)) {
    return {
      restaurants: result.data.map(mapApiRestaurantToFrontend),
      pagination: result.meta?.pagination ?? null,
    };
  }

  console.error("API returned unexpected format:", result);
  return { restaurants: [], pagination: result.meta?.pagination ?? null };
}

export async function fetchRestaurants(limit: number = 100, page: number = 1): Promise<Restaurant[]> {
  try {
    const { restaurants } = await fetchRestaurantsPage({ limit, page });
    return restaurants;
  } catch (error) {
    console.error('Error fetching restaurants:', error);
    return [];
  }
}

export async function fetchAllRestaurants(limit: number = 100): Promise<Restaurant[]> {
  const collected: Restaurant[] = [];
  let page = 1;
  for (let i = 0; i < 1000; i += 1) {
    const { restaurants, pagination } = await fetchRestaurantsPage({ limit, page });
    if (!restaurants.length) break;
    collected.push(...restaurants);
    if (!pagination?.has_next) break;
    page += 1;
  }

  const deduped = new Map<string, Restaurant>();
  for (const item of collected) deduped.set(item.id, item);
  return Array.from(deduped.values());
}

export async function fetchRestaurantById(id: string): Promise<Restaurant | null> {
  try {
    const response = await fetch(`${API_URL}/restaurants/${id}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<ApiRestaurant> = await response.json();
    
    if (result.success && result.data) {
      return mapApiRestaurantToFrontend(result.data);
    }
    return null;
  } catch (error) {
    console.error('Error fetching restaurant:', error);
    return null;
  }
}

export async function getNewestRestaurants(): Promise<Restaurant[]> {
  try {
    const response = await fetch(`${API_URL}/restaurants/newest`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<ApiRestaurant[]> = await response.json();
    
    if (result.success && Array.isArray(result.data)) {
      return result.data.map(mapApiRestaurantToFrontend);
    }
    return [];
  } catch (error) {
    console.error('Error fetching newest restaurants:', error);
    return [];
  }
}

export async function fetchRestaurantReviews(restaurantId: string): Promise<ApiReview[]> {
  try {
    const response = await fetch(`${API_URL}/reviews/restaurant/${restaurantId}?limit=100&page=1`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<ApiReview[]> = await response.json();
    
    if (result.success && Array.isArray(result.data)) {
      return result.data;
    }
    return [];
  } catch (error) {
    console.error('Error fetching reviews:', error);
    return [];
  }
}

export interface CreateReviewPayload {
  restaurant_id: string;
  rating: number;
  title?: string;
  content: string;
  images?: string[];
  visit_date?: string;
}

export async function createReview(payload: CreateReviewPayload): Promise<ApiReview> {
  const response = await fetch(`${API_URL}/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });

  let result: ApiResponse<ApiReview> | null = null;
  try {
    result = (await response.json()) as ApiResponse<ApiReview>;
  } catch {
    // ignore
  }

  if (!response.ok) {
    const message = result?.message || result?.error || `HTTP error! status: ${response.status}`;
    throw new Error(message);
  }

  if (!result?.success || !result.data) {
    throw new Error(result?.message || "Gửi đánh giá thất bại");
  }

  return result.data;
}

export interface UpdateReviewPayload {
  rating?: number;
  title?: string | null;
  content?: string;
  images?: string[] | null;
}

export async function updateReview(reviewId: string, payload: UpdateReviewPayload): Promise<ApiReview> {
  const response = await fetch(`${API_URL}/reviews/${encodeURIComponent(reviewId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });

  let result: ApiResponse<ApiReview> | null = null;
  try {
    result = (await response.json()) as ApiResponse<ApiReview>;
  } catch {
    // ignore
  }

  if (!response.ok) {
    const message = result?.message || result?.error || `HTTP error! status: ${response.status}`;
    throw new Error(message);
  }

  if (!result?.success || !result.data) {
    throw new Error(result?.message || "Cập nhật đánh giá thất bại");
  }

  return result.data;
}

export async function deleteReview(reviewId: string): Promise<void> {
  const response = await fetch(`${API_URL}/reviews/${encodeURIComponent(reviewId)}`, {
    method: "DELETE",
    headers: { ...getAuthHeaders() },
  });

  let result: ApiResponse<unknown> | null = null;
  try {
    result = (await response.json()) as ApiResponse<unknown>;
  } catch {
    // ignore
  }

  if (!response.ok) {
    const message = result?.message || result?.error || `HTTP error! status: ${response.status}`;
    throw new Error(message);
  }

  if (!result?.success) {
    throw new Error(result?.message || "Xóa đánh giá thất bại");
  }
}

export async function fetchMyReviewForRestaurant(restaurantId: string): Promise<ApiReview | null> {
  const response = await fetch(`${API_URL}/reviews/restaurant/${encodeURIComponent(restaurantId)}/mine`, {
    headers: { ...getAuthHeaders() },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const result: ApiResponse<ApiReview | null> = await response.json();
  if (!result.success) {
    throw new Error(result.message || "Không lấy được đánh giá của bạn");
  }

  return result.data || null;
}

export async function searchRestaurants(query: string): Promise<Restaurant[]> {
  try {
    const response = await fetch(`${API_URL}/restaurants/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<ApiRestaurant[]> = await response.json();
    
    if (result.success && Array.isArray(result.data)) {
      return result.data.map(mapApiRestaurantToFrontend);
    }
    return [];
  } catch (error) {
    console.error('Error searching restaurants:', error);
    return [];
  }
}

export async function fetchSitePage(slug: string): Promise<SitePage | null> {
  try {
    const response = await fetch(`${API_URL}/pages/${encodeURIComponent(slug)}`);
    if (!response.ok) return null;

    const result: ApiResponse<SitePage> = await response.json();
    if (result.success && result.data) return result.data;
    return null;
  } catch {
    return null;
  }
}
