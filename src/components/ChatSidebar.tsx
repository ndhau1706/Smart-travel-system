import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { PlusCircle, MessageSquare, Trash2, Menu, X } from "lucide-react";

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
  isOpen: boolean;
  onToggle: () => void;
}

export function ChatSidebar({
  chats,
  currentChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  isOpen,
  onToggle,
}: ChatSidebarProps) {
  return (
    <>
      {/* Mobile toggle button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 md:hidden bg-gradient-to-br from-pink-400 to-rose-400 backdrop-blur-lg border-2 border-pink-200 shadow-xl hover:from-pink-300 hover:to-rose-300 rounded-2xl"
        style={{ boxShadow: '0 0 20px rgba(255,182,193,0.5)' }}
        onClick={onToggle}
      >
        {isOpen ? <X className="h-5 w-5 text-white drop-shadow-[0_0_4px_rgba(255,255,255,0.8)]" /> : <Menu className="h-5 w-5 text-white drop-shadow-[0_0_4px_rgba(255,255,255,0.8)]" />}
      </Button>

      {/* Sidebar */}
      <div
        className={`fixed md:static inset-y-0 left-0 z-40 w-64 bg-gradient-to-b from-pink-100/95 via-purple-100/95 to-fuchsia-100/95 backdrop-blur-xl border-r-2 border-pink-300 flex flex-col transition-transform duration-200 shadow-2xl ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
        style={{ boxShadow: '0 0 40px rgba(255,182,193,0.3)' }}
      >
        <div className="p-4 border-b-2 border-pink-300" style={{ boxShadow: '0 4px 15px rgba(255,182,193,0.2)' }}>
          <Button
            onClick={onNewChat}
            className="w-full bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 hover:from-pink-300 hover:via-rose-300 hover:to-fuchsia-300 text-white shadow-xl rounded-2xl border-2 border-pink-200 transform hover:scale-105 transition-transform"
            style={{ boxShadow: '0 0 20px rgba(255,182,193,0.5), inset 0 0 10px rgba(255,255,255,0.3)' }}
          >
            <PlusCircle className="mr-2 h-5 w-5" />
            ✨ New Chat
          </Button>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {chats.map((chat) => (
              <div
                key={chat.id}
                className={`group relative flex items-center gap-2 p-3 rounded-2xl cursor-pointer transition-all duration-200 ${
                  currentChatId === chat.id
                    ? "bg-gradient-to-r from-pink-300/70 to-rose-300/70 shadow-lg border-2 border-pink-400 transform scale-105"
                    : "hover:bg-pink-200/50 border-2 border-transparent hover:border-pink-300"
                }`}
                style={currentChatId === chat.id ? { boxShadow: '0 0 20px rgba(255,182,193,0.5)' } : {}}
                onClick={() => onSelectChat(chat.id)}
              >
                <MessageSquare className="h-4 w-4 text-pink-600 flex-shrink-0 drop-shadow-[0_0_3px_rgba(255,182,193,0.5)]" />
                <span className="flex-1 text-sm text-pink-800 truncate">
                  {chat.title}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteChat(chat.id);
                  }}
                >
                  <Trash2 className="h-3 w-3 text-gray-400 hover:text-red-500" />
                </Button>
              </div>
            ))}
          </div>
        </ScrollArea>

        <div className="p-4 border-t-2 border-pink-300 bg-gradient-to-r from-pink-100 to-purple-100" style={{ boxShadow: '0 -4px 15px rgba(255,182,193,0.2)' }}>
          <div className="flex items-center gap-2 justify-center">
            <div className="text-xs text-pink-700 drop-shadow-[0_1px_3px_rgba(255,182,193,0.3)]">
              🍜 Cosmic Vietnamese Food Guide 🥢
            </div>
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={onToggle}
        />
      )}
    </>
  );
}
