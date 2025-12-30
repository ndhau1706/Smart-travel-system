import { useState, useEffect, useRef } from "react";
import { Routes, Route, useNavigate, useLocation, useParams } from "react-router-dom";

// Pages imports
import {
  HomePage,
  BlogsPage,
  RestaurantList,
  RestaurantDetail,
  MenuPage,
  GamesPage,
  VouchersPage,
  AboutPage,
  ContactPage,
  PolicyPage,
  ProfilePage,
  SettingsPage,
  PremiumPage,
  ChatSidebar,
  ChatMessage,
  ChatInput,
  PromptSuggestions,
  FloatingChatbot
} from "./pages";

// Common components
import { AuthDialog } from "./components/AuthDialog";
import { UserMenu } from "./components/UserMenu";
import { Navigation } from "./components/Navigation";

// UI components
import { ScrollArea } from "./components/ui/scroll-area";
import { Button } from "./components/ui/button";
import { Toaster } from "./components/ui/sonner";
import { UtensilsCrossed } from "lucide-react";

// Services & Context
import { fetchRestaurantById, fetchRestaurantsPage, Restaurant as ApiRestaurant } from "./services/api";
import { loginWithFirebase, type LoginResponse } from "./services/auth";
import { sendChatbotMessage } from "./services/chatbot";
import { SidebarProvider, useSidebar } from "./context/SidebarContext";
import { firebaseEnabled, firebaseHandleRedirectResult, firebaseSignOut } from "./services/firebase";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  recommendations?: ChatRecommendationRestaurant[];
}

interface Chat {
  id: string;
  title: string;
  timestamp: Date;
  sessionId?: string | null;
  messages: Message[];
}

interface ChatRecommendationRestaurant {
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

interface User {
  email: string;
  name: string;
  avatar?: string | null;
}

const AUTH_STORAGE_KEY = "auth";

// Use Restaurant type from API service
type Restaurant = ApiRestaurant;

// Mock travel food AI responses
const travelFoodResponses = [
  "Dựa trên vị trí của bạn, tôi gợi ý thử phở tại Phở Hà Nội - một trong những quán phở truyền thống tốt nhất với nước dùng nguyên bản!",
  "Bánh mì Sài Gòn gần đây là lựa chọn tuyệt vời cho bữa sáng! Họ mở cửa từ 6:00 sáng với bánh mì giòn tan và nhiều loại nhân đa dạng.",
  "Nếu bạn thích hải sản, Nhà Hàng Hải Sản Biển Xanh là nơi hoàn hảo với tôm hấp và cua rang me tuyệt ngon!",
  "Món bún chả tại Phở Hà Nội rất đáng thử! Thịt nướng thơm phức với nước chấm đặc biệt là điểm nhấn của món này.",
  "Cơm tấm Sài Gòn là lựa chọn tốt cho bữa trưa với giá phải chăng chỉ từ 50-55k. Sườn nướng và bì rất ngon!",
  "Nếu bạn ăn chay, Nhà Hàng Chay Sen Việt có nhiều món chay sáng tạo và ngon miệng. Phở chay của họ rất được yêu thích!",
];

function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Restaurant Detail Page Wrapper
function RestaurantDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadRestaurant = async () => {
      if (id) {
        setLoading(true);
        const data = await fetchRestaurantById(id);
        setRestaurant(data);
        setLoading(false);
      }
    };
    loadRestaurant();
  }, [id]);
  
  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center p-6">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-muted border-t-primary" />
      </div>
    );
  }
  
  if (!restaurant) {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center">
        <p className="text-muted-foreground">Không tìm thấy nhà hàng.</p>
        <Button onClick={() => navigate('/restaurants')}>Quay lại danh sách</Button>
      </div>
    );
  }
  
  return <RestaurantDetail restaurant={restaurant} onBack={() => navigate('/restaurants')} />;
}

// Restaurant List Page Wrapper
function RestaurantListPage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPrice, setSelectedPrice] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const cacheRef = useRef(
    new Map<
      string,
      { restaurants: Restaurant[]; pagination: { total_pages?: number; total?: number } | null; totalResults: number }
    >(),
  );
  const prefetchTimersRef = useRef<number[]>([]);

  useEffect(() => {
    let cancelled = false;
    const searchValue = searchQuery.trim();
    const cacheKey = `${currentPage}|${searchValue}|${selectedPrice}`;
    const cached = cacheRef.current.get(cacheKey);

    if (cached) {
      setRestaurants(cached.restaurants);
      setTotalPages(cached.pagination?.total_pages ?? 1);
      setTotalResults(cached.totalResults);
      setIsLoading(false);
    } else {
      setIsLoading(true);
    }

    const prefetchPage = async (page: number) => {
      const key = `${page}|${searchValue}|${selectedPrice}`;
      if (cacheRef.current.has(key)) return;
      try {
        const { restaurants: data, pagination } = await fetchRestaurantsPage({
          limit: 24,
          page,
          search: searchValue || undefined,
          price_level: selectedPrice || undefined,
          sort_by: "rating",
          sort_order: "desc",
        });
        if (cancelled) return;
        const total = pagination?.total ?? data.length;
        cacheRef.current.set(key, { restaurants: data, pagination, totalResults: total });
      } catch {
        // ignore background prefetch failures
      }
    };

    const schedulePrefetch = (pageTotal: number) => {
      prefetchTimersRef.current.forEach((timer) => window.clearTimeout(timer));
      prefetchTimersRef.current = [];

      const pagesToPrefetch = [currentPage + 1, currentPage + 2].filter((p) => p <= pageTotal);
      pagesToPrefetch.forEach((page, idx) => {
        const timer = window.setTimeout(() => {
          prefetchPage(page);
        }, 600 + idx * 800);
        prefetchTimersRef.current.push(timer);
      });
    };

    const loadRestaurants = async () => {
      if (cached) {
        schedulePrefetch(cached.pagination?.total_pages ?? 1);
        return;
      }

      try {
        const { restaurants: data, pagination } = await fetchRestaurantsPage({
          limit: 24,
          page: currentPage,
          search: searchValue || undefined,
          price_level: selectedPrice || undefined,
          sort_by: "rating",
          sort_order: "desc",
        });

        if (cancelled) return;
        const total = pagination?.total ?? data.length;
        cacheRef.current.set(cacheKey, { restaurants: data, pagination, totalResults: total });
        setRestaurants(data);
        setTotalPages(pagination?.total_pages ?? 1);
        setTotalResults(total);
        schedulePrefetch(pagination?.total_pages ?? 1);
      } catch (error) {
        if (cancelled) return;
        console.error("Failed to fetch restaurants:", error);
        setRestaurants([]);
        setTotalPages(1);
        setTotalResults(0);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    loadRestaurants();

    return () => {
      cancelled = true;
      prefetchTimersRef.current.forEach((timer) => window.clearTimeout(timer));
      prefetchTimersRef.current = [];
    };
  }, [currentPage, searchQuery, selectedPrice]);

  useEffect(() => {
    setCurrentPage((p) => Math.min(Math.max(1, p), totalPages));
  }, [totalPages]);
  
  const handleSelectRestaurant = (restaurant: Restaurant) => {
    navigate(`/restaurants/${restaurant.id}`);
  };
  
  const handleSearchQueryChange = (value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
  };

  const handlePriceChange = (value: number) => {
    setSelectedPrice(value);
    setCurrentPage(1);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(Math.min(Math.max(1, page), totalPages));
  };

  return (
      <RestaurantList
        restaurants={restaurants}
        onSelectRestaurant={handleSelectRestaurant}
        isLoading={isLoading}
        searchQuery={searchQuery}
        onSearchQueryChange={handleSearchQueryChange}
        selectedPrice={selectedPrice}
        onPriceChange={handlePriceChange}
        currentPage={currentPage}
      totalPages={totalPages}
      onPageChange={handlePageChange}
      totalResults={totalResults}
    />
  );
}

// Home Page Wrapper
function HomePageWrapper() {
  const navigate = useNavigate();
  return (
    <HomePage
      onNavigateToRestaurants={() => navigate("/restaurants")}
      onNavigateToChatbot={() => window.dispatchEvent(new Event("chatbot:open"))}
    />
  );
}

// Chatbot Page Component
function ChatbotPage({ userEmail }: { userEmail: string | null }) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const currentChat = chats.find((chat) => chat.id === currentChatId);

  const chatStorageKey = userEmail ? `chat_history:${userEmail}` : "chat_history:guest";

  useEffect(() => {
    setIsHydrated(false);

    try {
      const raw = localStorage.getItem(chatStorageKey);
      if (!raw) {
        setChats([]);
        setCurrentChatId(null);
        setIsHydrated(true);
        return;
      }

      const parsed = JSON.parse(raw) as
        | {
            currentChatId?: string | null;
            chats?: Array<Omit<Chat, "timestamp"> & { timestamp: string }>;
          }
        | null;

      const loadedChats = Array.isArray(parsed?.chats)
        ? parsed!.chats!.map((c) => ({
            ...c,
            timestamp: new Date(c.timestamp),
          }))
        : [];

      setChats(loadedChats);

      const desired = parsed?.currentChatId || loadedChats[0]?.id || null;
      setCurrentChatId(desired);
      setIsHydrated(true);
    } catch {
      setChats([]);
      setCurrentChatId(null);
      setIsHydrated(true);
    }
  }, [chatStorageKey]);

  useEffect(() => {
    if (!isHydrated) return;
    try {
      const payload = {
        currentChatId,
        chats: chats.map((c) => ({
          ...c,
          timestamp: c.timestamp.toISOString(),
        })),
      };
      localStorage.setItem(chatStorageKey, JSON.stringify(payload));
    } catch {
      // ignore
    }
  }, [chatStorageKey, chats, currentChatId, isHydrated]);

  useEffect(() => {
    if (isHydrated && chats.length === 0) {
      handleNewChat();
    }
  }, [isHydrated, chats.length]);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]");
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [currentChat?.messages]);

  const handleNewChat = () => {
    const newChat: Chat = {
      id: generateId(),
      title: "New Chat",
      timestamp: new Date(),
      sessionId: null,
      messages: [],
    };
    setChats((prev) => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
  };

  const handleSelectChat = (id: string) => {
    setCurrentChatId(id);
  };

  const handleDeleteChat = (id: string) => {
    setChats((prev) => prev.filter((chat) => chat.id !== id));
    if (currentChatId === id) {
      const remainingChats = chats.filter((chat) => chat.id !== id);
      setCurrentChatId(remainingChats[0]?.id || null);
      if (remainingChats.length === 0) {
        handleNewChat();
      }
    }
  };

  const stripDiacritics = (value: string) =>
    value
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "")
      .toLowerCase();

  type ChatPrefs = { cuisine?: string; location?: string; priceLabel?: string };

  const extractPrefs = (text: string, prev: ChatPrefs): ChatPrefs => {
    const normalized = stripDiacritics(text);
    const next: ChatPrefs = { ...prev };

    if (normalized.includes("binh dan") || normalized.includes("$") || /\bre\b/.test(normalized)) {
      next.priceLabel = "Bình dân";
    }
    if (normalized.includes("trung cap") || normalized.includes("$$")) {
      next.priceLabel = "Trung cấp";
    }
    if (normalized.includes("cao cap") || normalized.includes("$$$") || /\bdat\b/.test(normalized)) {
      next.priceLabel = "Cao cấp";
    }

    const cuisineMap: Array<{ key: string; label: string }> = [
      { key: "lau", label: "lẩu" },
      { key: "hai san", label: "hải sản" },
      { key: "nuong", label: "nướng" },
      { key: "com", label: "cơm" },
      { key: "buffet", label: "buffet" },
      { key: "mon nuoc", label: "món nước" },
      { key: "mon chien", label: "món chiên" },
      { key: "do chay", label: "đồ chay" },
      { key: "chay", label: "đồ chay" },
      { key: "cafe", label: "cafe" },
      { key: "ca phe", label: "cafe" },
    ];

    for (const item of cuisineMap) {
      if (normalized.includes(item.key)) {
        next.cuisine = item.label;
        break;
      }
    }

    const quanMatch = normalized.match(/\b(?:quan|q)\s*(\d{1,2})\b/);
    if (quanMatch?.[1]) next.location = `Quận ${quanMatch[1]}`;

    const locationMap: Array<{ key: string; label: string }> = [
      { key: "thu duc", label: "Thủ Đức" },
      { key: "hoc mon", label: "Hóc Môn" },
      { key: "go vap", label: "Gò Vấp" },
      { key: "tan binh", label: "Tân Bình" },
      { key: "tan phu", label: "Tân Phú" },
      { key: "binh thanh", label: "Bình Thạnh" },
      { key: "phu nhuan", label: "Phú Nhuận" },
      { key: "quan 1", label: "Quận 1" },
      { key: "quan 3", label: "Quận 3" },
      { key: "quan 5", label: "Quận 5" },
      { key: "quan 7", label: "Quận 7" },
    ];

    for (const item of locationMap) {
      if (normalized.includes(item.key)) {
        next.location = item.label;
        break;
      }
    }

    return next;
  };

  const buildMessageWithMemory = (chat: Chat, content: string): string => {
    const trimmed = content.trim();
    if (!trimmed) return content;

    const normalized = stripDiacritics(trimmed);
    const isGreeting = /^(hi|hello|xin chao|chao|hey)\b/.test(normalized);
    if (isGreeting) return content;

    let prefs: ChatPrefs = {};
    for (const msg of chat.messages) {
      if (msg.role !== "user") continue;
      prefs = extractPrefs(msg.content, prefs);
    }
    prefs = extractPrefs(content, prefs);

    const parts: string[] = [];
    if (prefs.cuisine) parts.push(`món ${prefs.cuisine}`);
    if (prefs.location) parts.push(prefs.location);
    if (prefs.priceLabel) parts.push(`giá ${prefs.priceLabel}`);

    if (parts.length === 0) return content;
    return `${content}\n\n(Ưu tiên: ${parts.join(", ")})`;
  };

  const handleSendMessage = async (content: string) => {
    if (!currentChatId) return;

    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content,
    };

    setChats((prev) =>
      prev.map((chat) => {
        if (chat.id === currentChatId) {
          const updatedMessages = [...chat.messages, userMessage];
          const title =
            chat.messages.length === 0
              ? content.slice(0, 30) + (content.length > 30 ? "..." : "")
              : chat.title;
          return { ...chat, messages: updatedMessages, title };
        }
        return chat;
      })
    );

    setIsGenerating(true);
    try {
      const chat = chats.find((c) => c.id === currentChatId);
      const modelMessage = chat ? buildMessageWithMemory(chat, content) : content;
      const historyForApi = (chat?.messages || []).slice(-12).map((m) => ({
        role: m.role,
        content: m.content,
      }));
      const data = await sendChatbotMessage({
        message: modelMessage,
        sessionId: chat?.sessionId ?? null,
        history: historyForApi,
        limit: 6,
      });
      const recommendations: ChatRecommendationRestaurant[] = data.recommendations;

      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: data.reply,
        recommendations,
      };

      setChats((prev) =>
        prev.map((chat) =>
          chat.id === currentChatId
            ? {
                ...chat,
                sessionId: chat.sessionId ?? data.sessionId ?? null,
                messages: [...chat.messages, assistantMessage],
              }
            : chat,
        ),
      );
    } catch (err: any) {
      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content:
          err?.message ||
          "Xin lỗi, mình đang gặp lỗi khi gợi ý nhà hàng. Bạn thử lại giúp mình nhé.",
      };
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, assistantMessage] }
            : chat,
        ),
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex h-dvh w-full">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 relative h-dvh">
        {currentChat ? (
          <>
            <ScrollArea className="flex-1" ref={scrollAreaRef}>
              <div className="max-w-3xl mx-auto pt-8 px-4">
                {currentChat.messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center min-h-[50vh] p-6">
                    <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
                      <UtensilsCrossed className="h-6 w-6" />
                    </div>
                    <div className="text-center space-y-2">
                      <h1 className="text-2xl font-semibold tracking-tight">Trợ lý ẩm thực AI</h1>
                      <p className="text-muted-foreground max-w-md">
                        Hỏi mình về món ăn Việt Nam, khu vực và mức giá để nhận gợi ý nhà hàng phù hợp.
                      </p>
                    </div>
                    <div className="mt-8 w-full">
                      <PromptSuggestions onSelectPrompt={handleSendMessage} />
                    </div>
                  </div>
                ) : (
                  <div>
                    {currentChat.messages.map((message) => (
                      <ChatMessage
                        key={message.id}
                        role={message.role}
                        content={message.content}
                        recommendations={message.recommendations}
                      />
                    ))}
                    {isGenerating && (
                      <div className="my-2 mx-4 flex items-center gap-3 rounded-xl border bg-card p-4 shadow-sm">
                        <div className="flex gap-1">
                          <span className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce" />
                          <span
                            className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce"
                            style={{ animationDelay: "0.15s" }}
                          />
                          <span
                            className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce"
                            style={{ animationDelay: "0.3s" }}
                          />
                        </div>
                        <span className="text-sm text-muted-foreground">Đang tạo gợi ý…</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </ScrollArea>

            <ChatInput onSendMessage={handleSendMessage} disabled={isGenerating} />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-muted-foreground">Chọn chat hoặc tạo chat mới</p>
          </div>
        )}
      </div>

      {/* Chat History Sidebar (right) */}
      <ChatSidebar
        chats={chats}
        currentChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />
    </div>
  );
}

export default function App() {
  return (
    <SidebarProvider>
      <AppContent />
    </SidebarProvider>
  );
}

function AppContent() {
  const [user, setUser] = useState<User | null>(null);
  const [authDialogOpen, setAuthDialogOpen] = useState(false);
  const location = useLocation();
  const { isCollapsed } = useSidebar();

  useEffect(() => {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!stored) return;
    try {
      const parsed = JSON.parse(stored) as { user?: { email?: string; name?: string; avatar?: string | null } } | null;
      const email = parsed?.user?.email;
      const name = parsed?.user?.name;
      if (email && name) {
        setUser({ email, name, avatar: parsed?.user?.avatar ?? null });
      }
    } catch {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail as { user?: { email?: string; name?: string; avatar?: string | null } } | undefined;
      const email = detail?.user?.email;
      const name = detail?.user?.name;
      if (email && name) {
        setUser({ email, name, avatar: detail?.user?.avatar ?? null });
      }
    };

    window.addEventListener("auth:updated", handler as EventListener);
    return () => window.removeEventListener("auth:updated", handler as EventListener);
  }, []);

  useEffect(() => {
    const handler = () => setAuthDialogOpen(true);
    window.addEventListener("auth:open", handler);
    return () => window.removeEventListener("auth:open", handler);
  }, []);

  useEffect(() => {
    if (!firebaseEnabled) return;

    // Handle Google sign-in redirect result at app level (mobile fallback).
    // This ensures the user is logged in even if the AuthDialog isn't open.
    let cancelled = false;
    const run = async () => {
      try {
        const fbUser = await firebaseHandleRedirectResult();
        if (!fbUser || cancelled) return;
        const idToken = await fbUser.getIdToken();
        const payload = await loginWithFirebase(idToken);
        if (cancelled) return;

        setUser({ email: payload.user.email, name: payload.user.name, avatar: payload.user.avatar ?? null });
        localStorage.setItem(
          AUTH_STORAGE_KEY,
          JSON.stringify({
            user: payload.user,
            accessToken: payload.access_token,
            refreshToken: payload.refresh_token,
            expiresIn: payload.expires_in,
          }),
        );
        window.dispatchEvent(new CustomEvent("auth:updated", { detail: { user: payload.user } }));
      } catch {
        // ignore (not a redirect flow)
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogin = (payload: LoginResponse) => {
    setUser({ email: payload.user.email, name: payload.user.name, avatar: payload.user.avatar ?? null });
    localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({
        user: payload.user,
        accessToken: payload.access_token,
        refreshToken: payload.refresh_token,
        expiresIn: payload.expires_in,
      }),
    );
    window.dispatchEvent(new CustomEvent("auth:updated", { detail: { user: payload.user } }));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem(AUTH_STORAGE_KEY);
    void firebaseSignOut();
    window.dispatchEvent(new CustomEvent("auth:updated", { detail: { user: null } }));
  };

  // Check if current page is chatbot
  const isChatbotPage = location.pathname === '/chatbot';

  return (
    <div className="min-h-dvh w-full bg-background text-foreground relative">
      <Toaster position="top-center" />
      
      {/* Auth Dialog */}
      <AuthDialog open={authDialogOpen} onOpenChange={setAuthDialogOpen} onLogin={handleLogin} />

      {/* Navigation Sidebar */}
      <Navigation
        user={user}
        onLoginClick={() => setAuthDialogOpen(true)}
        onLogout={handleLogout}
      />

      {/* Subtle tech background */}
      <div className="fixed inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/10 via-transparent to-transparent" />
      <div className="fixed inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-highlight/10 via-transparent to-transparent" />

      {/* Main Content - with left margin for sidebar on desktop */}
      <div className={`min-h-dvh flex flex-col relative z-10 transition-all duration-300 ${isCollapsed ? "lg:ml-20" : "lg:ml-64"}`}>
        <Routes>
          <Route path="/" element={<HomePageWrapper />} />
          <Route path="/blogs" element={<BlogsPage />} />
          <Route path="/restaurants" element={<RestaurantListPage />} />
          <Route path="/restaurants/:id" element={<RestaurantDetailPage />} />
          <Route path="/menu" element={<MenuPage />} />
          <Route path="/chatbot" element={<ChatbotPage userEmail={user?.email ?? null} />} />
          <Route path="/games" element={<GamesPage />} />
          <Route path="/vouchers" element={<VouchersPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/policy" element={<PolicyPage />} />
          <Route path="/account/profile" element={<ProfilePage />} />
          <Route path="/account/settings" element={<SettingsPage />} />
          <Route path="/account/premium" element={<PremiumPage />} />
        </Routes>
      </div>

      {/* Floating Chatbot - only show on non-chatbot views */}
      {!isChatbotPage && <FloatingChatbot userEmail={user?.email ?? null} />}
    </div>
  );
}
