import { useEffect, useState } from "react";

import { Button } from "../../components/ui/button";
import { ScrollArea } from "../../components/ui/scroll-area";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "../../components/ui/sheet";
import { MessageSquare, Trash2, Sparkles, History, PanelLeftIcon } from "lucide-react";
import { cn } from "../../components/ui/utils";

interface Chat {
  id: string;
  title: string;
  timestamp: Date;
}

interface ChatSidebarProps {
  chats: Chat[];
  currentChatId: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string) => void;
}

function truncateText(text: string, maxChars: number): string {
  const normalized = (text ?? "").trim();
  if (!normalized) return "";
  const chars = Array.from(normalized);
  if (chars.length <= maxChars) return normalized;
  return `${chars.slice(0, maxChars).join("")}...`;
}

export function ChatSidebar({
  chats,
  currentChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
}: ChatSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("chat_history_sidebar_collapsed");
      setIsCollapsed(raw === "1");
    } catch {
      // ignore
    }
  }, []);

  const toggleCollapsed = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("chat_history_sidebar_collapsed", next ? "1" : "0");
      } catch {
        // ignore
      }
      return next;
    });
  };

  const handleSelect = (id: string) => {
    onSelectChat(id);
    setMobileOpen(false);
  };

  const handleNew = () => {
    onNewChat();
    setMobileOpen(false);
  };

  const SidebarContent = ({ compact, fullWidth = false }: { compact: boolean; fullWidth?: boolean }) => (
    <div
      className={cn(
        "h-full flex flex-col bg-card border-l border-border transition-all duration-300",
        fullWidth ? "w-full" : compact ? "w-16" : "w-64",
      )}
    >
      {/* Header */}
      <div className={cn("border-b border-border", compact ? "p-2" : "p-3")}>
        <Button
          onClick={compact ? onNewChat : handleNew}
          className={cn("w-full rounded-lg", compact ? "p-2" : "")}
          size={compact ? "icon" : "default"}
        >
          <Sparkles className="h-4 w-4" />
          {!compact && "New chat"}
        </Button>
      </div>

      {/* Chat List */}
      <ScrollArea className="flex-1">
        <div className={`space-y-1 ${compact ? "p-1" : "p-2"}`}>
          {chats.length === 0 ? (
            !compact && (
              <div className="text-center py-8 text-muted-foreground text-sm">
                Chưa có cuộc trò chuyện nào
              </div>
            )
          ) : (
            chats.map((chat) => (
              <div
                key={chat.id}
                className={cn(
                  "group relative flex items-center min-w-0 overflow-hidden rounded-lg cursor-pointer transition-colors",
                  compact ? "p-2 justify-center" : "gap-3 p-3",
                  currentChatId === chat.id
                     ? "bg-accent border border-border"
                     : "border border-transparent hover:bg-accent/60",
                )}
                onClick={() => (compact ? onSelectChat(chat.id) : handleSelect(chat.id))}
                title={chat.title}
              >
                <MessageSquare
                  className={cn(
                    "h-4 w-4 flex-shrink-0",
                    currentChatId === chat.id ? "text-primary" : "text-muted-foreground",
                  )}
                />
                {!compact && (
                  <>
                    <div className="flex-1 min-w-0 overflow-hidden">
                      <span
                        className={cn(
                          "block w-full truncate text-sm",
                          currentChatId === chat.id ? "text-foreground font-medium" : "text-foreground/80",
                        )}
                      >
                        {truncateText(chat.title, 10)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {chat.timestamp.toLocaleDateString("vi-VN")}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive/10"
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation();
                        onDeleteChat(chat.id);
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-muted-foreground group-hover:text-destructive" />
                    </Button>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className={cn("border-t border-border", compact ? "p-2 space-y-0" : "p-3 space-y-2")}>
        {!compact && (
          <div className="text-center text-xs text-muted-foreground">
            Lịch sử chat
          </div>
        )}
        <Button
          variant="ghost"
          onClick={toggleCollapsed}
          className="w-full justify-center rounded-lg text-muted-foreground hover:text-foreground"
          size="sm"
        >
          {compact ? (
            <PanelLeftIcon className="h-5 w-5" />
          ) : (
            <>
              <PanelLeftIcon className="h-5 w-5 mr-2" />
              <span>Thu gọn</span>
            </>
          )}
        </Button>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile: history in a sheet */}
      <div className="lg:hidden fixed z-40 top-[calc(env(safe-area-inset-top)+1rem)] right-[calc(env(safe-area-inset-right)+1rem)]">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <Button
              className="bg-primary text-primary-foreground rounded-xl shadow-sm"
              size="icon"
              aria-label="Lịch sử chat"
            >
              <History className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent
            side="right"
            className="bg-background border-l border-border w-80 p-0"
          >
            <SheetHeader className="border-b border-border px-4 py-4">
              <SheetTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-muted-foreground" />
                Lịch sử chat
              </SheetTitle>
              <SheetDescription className="sr-only">
                Danh sách các cuộc trò chuyện trước đây
              </SheetDescription>
            </SheetHeader>
            <div className="h-full">
              <SidebarContent compact={false} fullWidth />
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop */}
      <div className="hidden lg:flex h-full">
        <SidebarContent compact={isCollapsed} />
      </div>
    </>
  );
}
