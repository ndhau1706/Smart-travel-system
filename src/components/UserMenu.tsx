import { Avatar, AvatarFallback } from "./ui/avatar";
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

interface UserMenuProps {
  userName: string;
  userEmail: string;
  onLogout: () => void;
}

export function UserMenu({ userName, userEmail, onLogout }: UserMenuProps) {
  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="fixed top-4 right-4 z-50 flex items-center gap-2 bg-gradient-to-br from-pink-200/90 to-purple-200/90 backdrop-blur-lg border-2 border-pink-300 shadow-xl hover:from-pink-200 hover:to-purple-200 rounded-2xl px-3 py-2"
          style={{ boxShadow: '0 0 20px rgba(255,182,193,0.5)' }}
        >
          <Avatar className="h-8 w-8 border-2 border-pink-300">
            <AvatarFallback className="bg-gradient-to-br from-pink-400 to-rose-400 text-white shadow-lg">
              {initials}
            </AvatarFallback>
          </Avatar>
          <span className="text-sm text-gray-800 hidden sm:inline">{userName}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
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
        <DropdownMenuItem className="text-gray-700 focus:bg-pink-200/50 focus:text-gray-900 cursor-pointer">
          <User className="mr-2 h-4 w-4" />
          <span>Hồ sơ</span>
        </DropdownMenuItem>
        <DropdownMenuItem className="text-gray-700 focus:bg-pink-200/50 focus:text-gray-900 cursor-pointer">
          <Settings className="mr-2 h-4 w-4" />
          <span>Cài đặt</span>
        </DropdownMenuItem>
        <DropdownMenuItem className="text-gray-700 focus:bg-pink-200/50 focus:text-gray-900 cursor-pointer">
          <Sparkles className="mr-2 h-4 w-4" />
          <span>Gói Premium</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator className="bg-pink-300" />
        <DropdownMenuItem
          onClick={onLogout}
          className="text-red-600 focus:bg-pink-200/50 focus:text-red-700 cursor-pointer"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Đăng xuất</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
