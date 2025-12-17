import { useState } from "react";

import { Button } from "../../components/ui/button";
import { ScrollArea } from "../../components/ui/scroll-area";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "../../components/ui/sheet";
import { MessageSquare, Trash2, Sparkles, History } from "lucide-react";
import { useSidebar } from "../../context/SidebarContext";

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

export function ChatSidebar({
  chats,
  currentChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
}: ChatSidebarProps) {
  const { isCollapsed } = useSidebar();
  const [mobileOpen, setMobileOpen] = useState(false);

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
      className={`h-full flex flex-col bg-gradient-to-b from-pink-50 via-rose-50 to-pink-100 border-r-2 border-pink-200 transition-all duration-300 ${
        fullWidth ? "w-full" : compact ? "w-16" : "w-64"
      }`}
    >
      {/* Header */}
      <div
        className={`border-b border-pink-200 bg-gradient-to-r from-pink-100 to-rose-100 ${compact ? "p-2" : "p-3"}`}
      >
        <Button
          onClick={compact ? onNewChat : handleNew}
          className={`bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white shadow-lg rounded-xl ${
            compact ? "w-full p-2" : "w-full"
          }`}
          size={compact ? "icon" : "default"}
        >
          <Sparkles className={`h-4 w-4`} />
          {!compact && "NEW CHAT"}
        </Button>
      </div>

      {/* Chat List */}
      <ScrollArea className="flex-1">
        <div className={`space-y-1 ${compact ? "p-1" : "p-2"}`}>
          {chats.length === 0 ? (
            !compact && (
              <div className="text-center py-8 text-pink-600 text-sm">
                Chưa có cuộc trò chuyện nào
              </div>
            )
          ) : (
            chats.map((chat) => (
              <div
                key={chat.id}
                className={`group relative flex items-center rounded-xl cursor-pointer transition-all ${
                  compact ? "p-2 justify-center" : "gap-3 p-3"
                } ${
                  currentChatId === chat.id
                    ? "bg-gradient-to-r from-pink-200 to-rose-200 border border-pink-300 shadow-md"
                    : "hover:bg-pink-100 border border-transparent"
                }`}
                onClick={() => (compact ? onSelectChat(chat.id) : handleSelect(chat.id))}
                title={compact ? chat.title : undefined}
              >
                <MessageSquare
                  className={`h-4 w-4 flex-shrink-0 ${
                    currentChatId === chat.id ? "text-pink-700" : "text-pink-400"
                  }`}
                />
                {!compact && (
                  <>
                    <div className="flex-1 min-w-0">
                      <span
                        className={`text-sm truncate block ${
                          currentChatId === chat.id
                            ? "text-pink-800 font-medium"
                            : "text-pink-700"
                        }`}
                      >
                        {chat.title}
                      </span>
                      <span className="text-xs text-pink-400">
                        {chat.timestamp.toLocaleDateString("vi-VN")}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100"
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation();
                        onDeleteChat(chat.id);
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-pink-700 hover:text-red-500" />
                    </Button>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      {!compact && (
        <div className="p-3 border-t border-pink-200 bg-gradient-to-r from-pink-50 to-rose-50">
          <div className="text-center text-xs text-pink-600">
            🍜 Food Journey Assistant
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Mobile: history in a sheet */}
      <div className="lg:hidden fixed top-safe-4 right-safe-4 z-40">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <Button
              className="bg-gradient-to-r from-pink-400 to-rose-400 text-white rounded-2xl shadow-xl border-2 border-pink-200"
              style={{ boxShadow: "0 0 25px rgba(255,182,193,0.4)" }}
              size="icon"
              aria-label="Lịch sử chat"
            >
              <History className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent
            side="right"
            className="bg-gradient-to-br from-pink-100 via-rose-100 to-pink-50 border-l-2 border-pink-200 w-80 p-0"
          >
            <SheetHeader className="border-b border-pink-200/60">
              <SheetTitle className="text-pink-800 flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-pink-500" />
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
