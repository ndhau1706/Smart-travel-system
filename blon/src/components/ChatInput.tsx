import { useState, useRef, useEffect } from "react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div 
      className="border-t-2 border-pink-300 bg-gradient-to-r from-pink-100/90 via-purple-100/90 to-fuchsia-100/90 backdrop-blur-xl p-4 shadow-2xl"
      style={{ boxShadow: '0 -10px 30px rgba(255,182,193,0.3)' }}
    >
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-2">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Vietnamese food... 🍜🥢✨"
            disabled={disabled}
            className="min-h-[52px] max-h-[200px] resize-none bg-white/80 border-2 border-pink-300 text-gray-800 placeholder:text-pink-400/70 pr-12 focus:border-pink-400 focus:ring-2 focus:ring-pink-300 backdrop-blur-sm rounded-3xl shadow-xl"
            style={{ boxShadow: '0 0 20px rgba(255,182,193,0.3), inset 0 0 15px rgba(255,255,255,0.5)' }}
            rows={1}
          />
          <Button
            type="submit"
            size="icon"
            disabled={!message.trim() || disabled}
            className="absolute right-2 bottom-2 h-10 w-10 bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 hover:from-pink-300 hover:via-rose-300 hover:to-fuchsia-300 disabled:from-gray-400 disabled:to-gray-500 shadow-xl rounded-2xl border-2 border-pink-200 transform hover:scale-110 transition-transform"
            style={{ boxShadow: '0 0 20px rgba(255,182,193,0.5)' }}
          >
            <Send className="h-4 w-4 text-white drop-shadow-[0_0_4px_rgba(255,255,255,0.8)]" />
          </Button>
        </div>
      </form>
    </div>
  );
}
