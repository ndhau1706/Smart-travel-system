import { UtensilsCrossed, User } from "lucide-react";
import { Avatar, AvatarFallback } from "./ui/avatar";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      className={`flex gap-4 p-6 ${
        isUser ? "bg-transparent" : "bg-gradient-to-r from-pink-200/70 via-rose-200/70 to-fuchsia-200/70 backdrop-blur-md border-2 border-pink-300 rounded-3xl my-2 mx-4 shadow-lg"
      }`}
      style={!isUser ? { boxShadow: '0 0 25px rgba(255,182,193,0.3), inset 0 0 20px rgba(255,255,255,0.3)' } : {}}
    >
      <Avatar className="h-10 w-10 flex-shrink-0 shadow-xl border-2 border-pink-300">
        <AvatarFallback 
          className={isUser ? "bg-gradient-to-br from-pink-300 to-rose-400 shadow-lg" : "bg-gradient-to-br from-pink-400 via-rose-400 to-fuchsia-400 shadow-lg"}
          style={{ boxShadow: isUser ? '0 0 18px rgba(255,182,193,0.5)' : '0 0 18px rgba(255,182,193,0.5)' }}
        >
          {isUser ? <User className="h-5 w-5 text-white drop-shadow-[0_0_4px_rgba(255,255,255,0.8)]" /> : <span className="text-xl drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]">🍜</span>}
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 space-y-2 overflow-hidden">
        <div className={`${isUser ? "text-gray-800" : "text-gray-800"} whitespace-pre-wrap break-words`}>
          {content}
        </div>
      </div>
    </div>
  );
}
