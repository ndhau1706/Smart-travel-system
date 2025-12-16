import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { User, LogOut, Settings, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { cn } from "./ui/utils";

interface UserMenuProps {
  userName: string;
  userEmail: string;
  onLogout: () => void;
  avatarUrl?: string | null;
  className?: string;
  compact?: boolean;
  dropdownSide?: "top" | "bottom" | "left" | "right";
  dropdownAlign?: "start" | "center" | "end";
}

export function UserMenu({
  userName,
  userEmail,
  onLogout,
  avatarUrl,
  className,
  compact = false,
  dropdownSide = "bottom",
  dropdownAlign = "end",
}: UserMenuProps) {
  const navigate = useNavigate();
  const safeUserName = (userName || "").trim();
  const initials = safeUserName
    ? safeUserName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className={cn(
            "min-w-0 flex items-center gap-2 bg-gradient-to-br from-pink-200/90 to-purple-200/90 backdrop-blur-lg border-2 border-pink-300 shadow-xl hover:from-pink-200 hover:to-purple-200 rounded-2xl px-3 py-2",
            className,
          )}
          style={{ boxShadow: '0 0 20px rgba(255,182,193,0.5)' }}
        >
          <Avatar className="h-8 w-8 border-2 border-pink-300">
            {avatarUrl ? (
              <AvatarImage src={avatarUrl} alt={safeUserName || "Avatar"} />
            ) : null}
            <AvatarFallback className="bg-gradient-to-br from-pink-400 to-rose-400 text-white shadow-lg">
              {initials}
            </AvatarFallback>
          </Avatar>
          {!compact && (
            <span className="min-w-0 flex-1 text-left text-sm text-gray-800 truncate">
              {safeUserName || userName}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align={dropdownAlign}
        side={dropdownSide}
        className="w-56 bg-gradient-to-br from-pink-50 to-purple-50 border-2 border-pink-300 shadow-2xl rounded-2xl mt-2"
        style={{ boxShadow: '0 0 30px rgba(255,182,193,0.4)' }}
      >
        <DropdownMenuLabel className="text-pink-700">
          <div className="flex flex-col space-y-1">
            <p className="leading-none">{userName}</p>
            <p className="text-xs text-pink-500 leading-none">{userEmail}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-pink-300" />
        <DropdownMenuItem
          onSelect={() => navigate("/account/profile")}
          className="text-gray-700 focus:bg-pink-200/50 focus:text-gray-900 cursor-pointer"
        >
          <User className="mr-2 h-4 w-4" />
          <span>Hồ sơ</span>
        </DropdownMenuItem>
        <DropdownMenuItem
          onSelect={() => navigate("/account/settings")}
          className="text-gray-700 focus:bg-pink-200/50 focus:text-gray-900 cursor-pointer"
        >
          <Settings className="mr-2 h-4 w-4" />
          <span>Cài đặt</span>
        </DropdownMenuItem>
        <DropdownMenuItem
          onSelect={() => navigate("/account/premium")}
          className="text-gray-700 focus:bg-pink-200/50 focus:text-gray-900 cursor-pointer"
        >
          <Sparkles className="mr-2 h-4 w-4" />
          <span>Gói Premium</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator className="bg-pink-300" />
        <DropdownMenuItem
          onSelect={onLogout}
          className="text-red-600 focus:bg-pink-200/50 focus:text-red-700 cursor-pointer"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Đăng xuất</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
