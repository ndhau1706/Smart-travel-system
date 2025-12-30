import { useState, useEffect, useRef } from "react";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { ScrollArea } from "../../components/ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { MessageCircle, X, PanelLeftIcon } from "lucide-react";
import { sendChatbotMessage } from "../../services/chatbot";
import type { ChatRecommendationRestaurant } from "./ChatMessage";
import { cn } from "../../components/ui/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  recommendations?: ChatRecommendationRestaurant[];
}

const foodSuggestions = [
  "Món phở ngon nhất ở đâu?",
  "Gợi ý món ăn sáng Việt Nam",
  "Quán bánh mì ngon ở Sài Gòn",
  "Món chay Việt Nam có gì?",
];

const chatbotResponses = [
  "Dựa trên các nhà hàng trong danh sách, tôi gợi ý bạn nên thử phở bò tại Phở Hà Nội hoặc Phở 24. Cả hai đều có đánh giá cao và được du khách yêu thích!",
  "Bánh mì Việt Nam là một lựa chọn tuyệt vời! Tôi khuyên bạn nên thử Bánh Mì Sài Gòn - họ có nhiều loại nhân như thịt nướng, pate, và chả lụa. Giá cả phải chăng và rất ngon!",
  "Nếu bạn thích hải sản, tôi gợi ý bạn ghé Nhà Hàng Hải Sản Biển Xanh. Họ có các món như tôm hấp, cua rang me, và cá chiên giòn rất tươi ngon!",
  "Món bún chả là đặc sản Hà Nội không thể bỏ qua! Bún chả bao gồm thịt nướng thơm phức, bún tươi và nước chấm chua ngọt. Rất ngon và phù hợp cho bữa trưa!",
  "Cơm tấm là món ăn phổ biến ở miền Nam, thường có sườn nướng, bì, chả trứng và nước mắm chua ngọt. Nhà Hàng Cơm Tấm Sài Gòn phục vụ món này rất đặc biệt!",
  "Đối với món chay, tôi gợi ý Nhà Hàng Chay Sen Việt. Họ có nhiều món chay sáng tạo như phở chay, bún chay, và các món xào rau củ quả đa dạng và bổ dưỡng!",
];

function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function FloatingChatbot({ userEmail }: { userEmail: string | null }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const storageKey = userEmail ? `floating_chat_messages:${userEmail}` : "floating_chat_messages:guest";

  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) {
        setMessages([]);
        setSessionId(null);
        return;
      }

      const parsed = JSON.parse(raw) as { messages?: Message[]; sessionId?: string | null } | Message[] | null;
      if (Array.isArray(parsed)) {
        setMessages(parsed);
        setSessionId(null);
        return;
      }

      if (!parsed || !Array.isArray(parsed.messages)) {
        setMessages([]);
        setSessionId(null);
        return;
      }

      setMessages(parsed.messages);
      setSessionId(typeof parsed.sessionId === "string" ? parsed.sessionId : null);
    } catch {
      setMessages([]);
      setSessionId(null);
    }
  }, [storageKey]);

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify({ sessionId, messages }));
    } catch {
      // ignore
    }
  }, [messages, sessionId, storageKey]);

  useEffect(() => {
    const handler = () => {
      setIsOpen(true);
      setIsMinimized(false);
    };

    window.addEventListener("chatbot:open", handler);
    return () => window.removeEventListener("chatbot:open", handler);
  }, []);

  useEffect(() => {
    if (scrollAreaRef.current && isOpen) {
      const viewport = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]");
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [messages, isOpen]);

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

    return next;
  };

  const buildMessageWithMemory = (content: string): string => {
    const trimmed = content.trim();
    if (!trimmed) return content;

    const normalized = stripDiacritics(trimmed);
    const isGreeting = /^(hi|hello|xin chao|chao|hey)\b/.test(normalized);
    if (isGreeting) return content;

    let prefs: ChatPrefs = {};
    for (const msg of messages) {
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
    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsGenerating(true);
    try {
      const modelMessage = buildMessageWithMemory(content);
      const historyForApi = messages.slice(-12).map((m) => ({ role: m.role, content: m.content }));
      const data = await sendChatbotMessage({
        message: modelMessage,
        sessionId,
        history: historyForApi,
        limit: 6,
      });
      const recommendations: ChatRecommendationRestaurant[] = data.recommendations;
      setSessionId(data.sessionId ?? sessionId ?? null);

      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: data.reply,
        recommendations,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content:
          err?.message ||
          chatbotResponses[Math.floor(Math.random() * chatbotResponses.length)],
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMessage(suggestion);
  };

  if (!isOpen) {
    return (
      <Button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full shadow-lg p-0"
        aria-label="Mở chatbot"
      >
        <MessageCircle className="h-6 w-6" />
      </Button>
    );
  }

  return (
    <Card
      className={cn(
        "fixed bottom-4 right-4 z-50 overflow-hidden border bg-card shadow-lg transition-all duration-300",
        isMinimized ? "h-16" : "h-[520px] sm:h-[560px]",
        "w-[calc(100vw-1.5rem)] sm:w-[360px] md:w-[420px] rounded-xl",
      )}
    >
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 border-b bg-primary text-primary-foreground px-4 py-3">
          <div className="h-2.5 w-2.5 rounded-full bg-green-400 animate-pulse" />
          <div className="min-w-0 flex-1 text-left">
            <div className="text-sm font-medium truncate">Trợ lý ẩm thực AI</div>
            {!isMinimized && (
              <div className="text-xs text-primary-foreground/80 truncate">
                Gợi ý nhà hàng từ dữ liệu của bạn
              </div>
            )}
          </div>
          <div className="flex gap-1">
            <Button
              size="icon"
              variant="ghost"
              onClick={() => setIsMinimized(!isMinimized)}
              className="h-8 w-8 text-primary-foreground hover:bg-white/15"
              aria-label={isMinimized ? "Mở rộng" : "Thu gọn"}
            >
              <PanelLeftIcon className="h-4 w-4" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              onClick={() => setIsOpen(false)}
              className="h-8 w-8 text-primary-foreground hover:bg-white/15"
              aria-label="Đóng chatbot"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {!isMinimized && (
          <>
            <ScrollArea className="flex-1 p-3 sm:p-4" ref={scrollAreaRef}>
              {messages.length === 0 ? (
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Xin chào! Bạn muốn ăn món gì, ở khu vực nào và mức giá ra sao?
                  </p>
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">Gợi ý nhanh</p>
                    {foodSuggestions.map((suggestion, idx) => (
                      <Button
                        key={idx}
                        variant="outline"
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="w-full justify-start text-left rounded-lg text-sm"
                      >
                        {suggestion}
                      </Button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <ChatMessage
                      key={message.id}
                      role={message.role}
                      content={message.content}
                      recommendations={message.recommendations}
                    />
                  ))}
                  {isGenerating && (
                    <div className="flex items-center gap-2 rounded-lg border bg-muted/40 p-3 text-sm text-muted-foreground">
                      <span className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce" />
                      <span
                        className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce"
                        style={{ animationDelay: "0.15s" }}
                      />
                      <span
                        className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce"
                        style={{ animationDelay: "0.3s" }}
                      />
                      <span className="ml-1">Đang tạo gợi ý…</span>
                    </div>
                  )}
                </div>
              )}
            </ScrollArea>

            <ChatInput onSendMessage={handleSendMessage} disabled={isGenerating} />
          </>
        )}
      </div>
    </Card>
  );
}
