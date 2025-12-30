import { API_URL, CHATBOT_API_URL } from "./config";
import { getClientId } from "./identity";
import { recommendRestaurantsForChat, type ChatHistoryMessage } from "./api";

export interface ChatbotRestaurant {
  id?: string | number;
  name?: string;
  address?: string | null;
  phone?: string | null;
  website?: string | null;
  rating?: number | null;
  rating_count?: number | null;
  ratingCount?: number | null;
  price_level?: string | number | null;
  food_tags?: string[] | null;
  distance_text?: string | null;
  open_status?: string | null;
  badges?: string[] | null;
  signature_dishes?: string[] | null;
  review_insights?: string | null;
}

export interface ChatbotApiResponse {
  session_id: string;
  message: string;
  restaurants?: ChatbotRestaurant[] | null;
  language?: string;
  explanation?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface ChatbotRecommendation {
  id: string;
  name: string;
  cuisine?: string;
  address?: string;
  rating?: number;
  reviewCount?: number;
  priceLevel?: number;
  image?: string;
  googleMapsUrl?: string;
  website?: string;
  detailId?: string;
}

export interface ChatbotMessageResult {
  reply: string;
  recommendations: ChatbotRecommendation[];
  sessionId?: string | null;
}

export interface SendChatbotMessageOptions {
  message: string;
  sessionId?: string | null;
  userId?: string | null;
  history?: ChatHistoryMessage[];
  limit?: number;
}

const PRICE_LEVEL_MAP: Record<string, number> = {
  PRICE_LEVEL_INEXPENSIVE: 1,
  PRICE_LEVEL_MODERATE: 2,
  PRICE_LEVEL_EXPENSIVE: 3,
  PRICE_LEVEL_VERY_EXPENSIVE: 4,
};

function readAuthUserId(): string | null {
  try {
    const stored = localStorage.getItem("auth");
    if (!stored) return null;
    const parsed = JSON.parse(stored) as { user?: { id?: string; email?: string } };
    return parsed?.user?.id || parsed?.user?.email || null;
  } catch {
    return null;
  }
}

function normalizePriceLevel(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return Math.round(value);
  }
  if (typeof value === "string") {
    const normalized = value.trim().toUpperCase();
    if (!normalized) return undefined;
    if (PRICE_LEVEL_MAP[normalized]) return PRICE_LEVEL_MAP[normalized];
    if (normalized.includes("INEXPENSIVE")) return 1;
    if (normalized.includes("MODERATE")) return 2;
    if (normalized.includes("EXPENSIVE")) return 3;
    if (normalized.includes("VERY")) return 4;
  }
  return undefined;
}

function buildMapsUrl(name?: string | null, address?: string | null): string | undefined {
  const query = [name, address].filter(Boolean).join(" ").trim();
  if (!query) return undefined;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}

function normalizeChatbotRestaurant(item: ChatbotRestaurant): ChatbotRecommendation {
  const name = (item.name || "").trim() || "Nhà hàng";
  const address = item.address ? String(item.address) : undefined;
  const rating = typeof item.rating === "number" ? item.rating : undefined;
  const ratingCount =
    typeof item.rating_count === "number"
      ? item.rating_count
      : typeof item.ratingCount === "number"
        ? item.ratingCount
        : undefined;
  const priceLevel = normalizePriceLevel(item.price_level ?? undefined);
  const website = item.website ? String(item.website) : undefined;
  const googleMapsUrl = buildMapsUrl(name, address);
  const id = item.id !== undefined ? String(item.id) : `${name}-${address || "unknown"}`;

  return {
    id,
    name,
    address,
    rating,
    reviewCount: ratingCount ?? undefined,
    priceLevel,
    googleMapsUrl,
    website,
  };
}

function normalizeLegacyRestaurant(item: {
  id: string;
  name: string;
  cuisine?: string;
  address?: string;
  rating?: number;
  review_count?: number;
  price_level?: number;
  image?: string;
  google_maps_url?: string;
}): ChatbotRecommendation {
  return {
    id: item.id,
    detailId: item.id,
    name: item.name,
    cuisine: item.cuisine,
    address: item.address,
    rating: item.rating,
    reviewCount: item.review_count,
    priceLevel: item.price_level,
    image: item.image,
    googleMapsUrl: item.google_maps_url,
  };
}

async function callChatbotApi(options: SendChatbotMessageOptions): Promise<ChatbotMessageResult> {
  if (!CHATBOT_API_URL) {
    throw new Error("Chatbot API URL is not configured.");
  }

  const userId = options.userId || readAuthUserId() || getClientId();

  const res = await fetch(`${CHATBOT_API_URL}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: options.message,
      session_id: options.sessionId || undefined,
      user_id: userId,
    }),
  });

  let data: ChatbotApiResponse | null = null;
  try {
    data = (await res.json()) as ChatbotApiResponse;
  } catch {
    // ignore parse errors
  }

  if (!res.ok || !data) {
    const message = (data as any)?.message || res.statusText || "Chatbot request failed";
    throw new Error(message);
  }

  const recommendations = Array.isArray(data.restaurants)
    ? data.restaurants.map(normalizeChatbotRestaurant)
    : [];

  return {
    reply: data.message,
    recommendations,
    sessionId: data.session_id,
  };
}

async function callLegacyApi(options: SendChatbotMessageOptions): Promise<ChatbotMessageResult> {
  const limit = typeof options.limit === "number" ? options.limit : 6;
  const legacy = await recommendRestaurantsForChat(options.message, limit, options.history);
  const recommendations = (legacy.restaurants || []).map(normalizeLegacyRestaurant);
  return {
    reply: legacy.reply,
    recommendations,
    sessionId: null,
  };
}

export async function sendChatbotMessage(options: SendChatbotMessageOptions): Promise<ChatbotMessageResult> {
  const preferChatbotApi = Boolean(CHATBOT_API_URL);

  if (preferChatbotApi) {
    try {
      return await callChatbotApi(options);
    } catch (err) {
      if (API_URL) {
        return await callLegacyApi(options);
      }
      throw err;
    }
  }

  return await callLegacyApi(options);
}
