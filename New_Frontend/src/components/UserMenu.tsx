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
            "min-w-0 flex items-center gap-2 rounded-lg px-3 py-2 text-sidebar-foreground/90 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            compact ? "justify-center px-2" : "justify-start",
            className,
          )}
        >
          <Avatar className="h-8 w-8 border border-sidebar-border">
            {avatarUrl ? (
              <AvatarImage src={avatarUrl} alt={safeUserName || "Avatar"} />
            ) : null}
            <AvatarFallback className="bg-primary text-primary-foreground">
              {initials}
            </AvatarFallback>
          </Avatar>
          {!compact && (
            <span className="min-w-0 flex-1 text-left text-sm truncate">
              {safeUserName || userName}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align={dropdownAlign}
        side={dropdownSide}
        className="w-56"
      >
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="leading-none font-medium">{userName}</p>
            <p className="text-xs text-muted-foreground leading-none">{userEmail}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onSelect={() => navigate("/account/profile")}
          className="cursor-pointer"
        >
          <User className="mr-2 h-4 w-4" />
          <span>Hồ sơ</span>
        </DropdownMenuItem>
        <DropdownMenuItem
          onSelect={() => navigate("/account/settings")}
          className="cursor-pointer"
        >
          <Settings className="mr-2 h-4 w-4" />
          <span>Cài đặt</span>
        </DropdownMenuItem>
        <DropdownMenuItem
          onSelect={() => navigate("/account/premium")}
          className="cursor-pointer"
        >
          <Sparkles className="mr-2 h-4 w-4" />
          <span>Gói Premium</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onSelect={onLogout}
          className="cursor-pointer text-destructive focus:text-destructive"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Đăng xuất</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
