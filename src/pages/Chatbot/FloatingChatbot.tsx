import { useState, useEffect, useRef } from "react";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { ScrollArea } from "../../components/ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { MessageCircle, X, Minimize2 } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
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

export function FloatingChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current && isOpen) {
      const viewport = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]");
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsGenerating(true);

    await new Promise((resolve) => setTimeout(resolve, 1000));

    const assistantMessage: Message = {
      id: generateId(),
      role: "assistant",
      content: chatbotResponses[Math.floor(Math.random() * chatbotResponses.length)],
    };

    setMessages((prev) => [...prev, assistantMessage]);
    setIsGenerating(false);
  };

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMessage(suggestion);
  };

  if (!isOpen) {
    return (
      <Button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 h-16 w-16 rounded-full bg-gradient-to-br from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 shadow-2xl text-white p-0"
        style={{
          boxShadow: "0 0 30px rgba(255,182,193,0.6), 0 10px 40px rgba(0,0,0,0.2)",
        }}
      >
        <MessageCircle className="h-8 w-8" />
      </Button>
    );
  }

  return (
    <Card
      className={`fixed bottom-3 right-3 z-50 bg-gradient-to-br from-pink-50 via-rose-50 to-fuchsia-50 border-2 border-pink-200 shadow-2xl overflow-hidden transition-all duration-300 text-center ${
        isMinimized ? "h-16" : "h-[500px] sm:h-[550px] md:h-[600px]"
      } w-[calc(100vw-1.5rem)] sm:w-[360px] md:w-[400px] rounded-2xl sm:rounded-3xl`}
      style={{
        boxShadow: "0 0 40px rgba(255,182,193,0.5), 0 20px 60px rgba(0,0,0,0.15)",
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-pink-400 to-rose-400 border-b-2 border-pink-300">
        <div className="h-3 w-3 bg-green-400 rounded-full animate-pulse" />
        <div className="flex-1 text-center">
          <span className="text-white font-medium">🤖 TRỢ LÝ ẨM THỰC AI 🤖</span>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIsMinimized(!isMinimized)}
            className="h-8 w-8 p-0 text-white hover:bg-white/20"
          >
            <Minimize2 className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIsOpen(false)}
            className="h-8 w-8 p-0 text-white hover:bg-white/20"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Chat Area */}
      {!isMinimized && (
        <div className="flex flex-col h-[calc(500px-64px)] sm:h-[calc(550px-64px)] md:h-[calc(600px-64px)]">
          <ScrollArea className="flex-1 p-3 sm:p-4" ref={scrollAreaRef}>
            {messages.length === 0 ? (
              <div className="space-y-4">
                <div className="text-center">
                  <p className="text-pink-600">
                    Xin chào! Tôi là trợ lý AI chuyên về ẩm thực Việt Nam. Tôi có thể giúp bạn tìm món ăn phù hợp!
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-pink-600">Câu hỏi gợi ý:</p>
                  {foodSuggestions.map((suggestion, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="w-full justify-start text-left bg-white/80 border-pink-200 hover:bg-pink-100 hover:border-pink-300 rounded-xl text-sm"
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <ChatMessage key={message.id} role={message.role} content={message.content} />
                ))}
                {isGenerating && (
                  <div className="flex gap-2 p-3 bg-gradient-to-r from-pink-200/80 via-rose-200/80 to-fuchsia-200/80 backdrop-blur-md border-2 border-pink-300 rounded-2xl">
                    <div className="w-3 h-3 bg-gradient-to-r from-pink-400 to-rose-400 rounded-full animate-bounce" />
                    <div
                      className="w-3 h-3 bg-gradient-to-r from-rose-400 to-fuchsia-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                    <div
                      className="w-3 h-3 bg-gradient-to-r from-fuchsia-400 to-pink-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.4s" }}
                    />
                  </div>
                )}
              </div>
            )}
          </ScrollArea>

          <div className="border-t-2 border-pink-200 p-3 bg-white/50">
            <ChatInput onSendMessage={handleSendMessage} disabled={isGenerating} />
          </div>
        </div>
      )}
    </Card>
  );
}
