import { useState, useRef, useEffect } from "react";
import { Button } from "../../components/ui/button";
import { Textarea } from "../../components/ui/textarea";
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
    <div className="sticky bottom-0 z-40 border-t border-border/60 bg-background/75 backdrop-blur shadow-[0_-8px_24px_rgba(0,0,0,0.06)]">
      <div className="mx-auto w-full max-w-3xl px-4 pt-3 pb-[calc(env(safe-area-inset-bottom)+1.5rem)]">
        <form onSubmit={handleSubmit} className="w-full">
          <div className="relative w-full rounded-full border border-border bg-card/70 shadow-sm ring-0 transition-shadow focus-within:ring-2 focus-within:ring-primary/25">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Hỏi về ẩm thực Việt Nam..."
              disabled={disabled}
              className="min-h-[52px] max-h-[200px] w-full rounded-full border-0 bg-transparent px-5 py-3 pr-14 shadow-none focus-visible:ring-0 focus-visible:border-transparent"
              rows={1}
            />
            <Button
              type="submit"
              size="icon"
              disabled={!message.trim() || disabled}
              className="absolute right-2 top-1/2 h-10 w-10 -translate-y-1/2 rounded-full shadow-sm"
              aria-label="Gửi"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
