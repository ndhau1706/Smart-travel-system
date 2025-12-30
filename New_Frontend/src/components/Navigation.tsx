import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "./ui/sheet";
import { Home, Store, UtensilsCrossed, MessageCircle, Info, Mail, FileText, PanelLeftIcon, LogIn, Palette, Gamepad2, PenSquare, Wallet } from "lucide-react";
import { useSidebar } from "../context/SidebarContext";
import { UserMenu } from "./UserMenu";
import { cn } from "./ui/utils";

const THEME_STORAGE_KEY = "theme";
type ThemeMode = "tech" | "pink";

const navItems = [
  { path: "/", label: "Trang chủ", icon: Home },
  { path: "/restaurants", label: "Nhà hàng", icon: Store },
  { path: "/menu", label: "Menu", icon: UtensilsCrossed },
  { path: "/blogs", label: "Blogs", icon: PenSquare },
  { path: "/vouchers", label: "Ví voucher", icon: Wallet },
  { path: "/chatbot", label: "Gợi ý món", icon: MessageCircle },
  { path: "/games", label: "Trò chơi", icon: Gamepad2 },
  { path: "/about", label: "Giới thiệu", icon: Info },
  { path: "/contact", label: "Liên hệ", icon: Mail },
  { path: "/policy", label: "Chính sách", icon: FileText },
];

interface NavigationProps {
  user: { name: string; email: string; avatar?: string | null } | null;
  onLoginClick: () => void;
  onLogout: () => void;
}

export function Navigation({ user, onLoginClick, onLogout }: NavigationProps) {
  const location = useLocation();
  const currentPath = location.pathname;
  const { isCollapsed, toggleCollapsed } = useSidebar();
  const [theme, setTheme] = useState<ThemeMode>(() => {
    try {
      return localStorage.getItem(THEME_STORAGE_KEY) === "pink" ? "pink" : "tech";
    } catch {
      return "tech";
    }
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "pink") {
      root.setAttribute("data-theme", "pink");
    } else {
      root.removeAttribute("data-theme");
    }

    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // ignore
    }
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === "pink" ? "tech" : "pink"));

  const isActive = (path: string) => {
    if (path === "/") return currentPath === "/";
    return currentPath.startsWith(path);
  };

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden lg:flex fixed inset-y-0 left-0 z-40 flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border shadow-sm transition-[width] duration-300",
          isCollapsed ? "w-20 items-center" : "w-64",
        )}
      >
        {/* Brand */}
        <div
          className={cn(
            "relative flex w-full items-center border-b border-sidebar-border py-4",
            isCollapsed ? "justify-center px-0" : "gap-3 px-4",
          )}
        >
          <Link
            to="/"
            className={cn(
              "flex items-center gap-3",
              isCollapsed ? "w-full justify-center px-0" : "min-w-0",
            )}
            onClick={(event) => {
              // When collapsed, clicking the logo expands the sidebar (no navigation).
              if (isCollapsed) {
                event.preventDefault();
                toggleCollapsed();
              }
            }}
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sidebar-accent text-sidebar-accent-foreground ring-1 ring-sidebar-border">
              <UtensilsCrossed className="h-5 w-5 text-highlight" />
            </div>
            {!isCollapsed && (
              <div className="min-w-0">
                <div className="truncate font-semibold leading-none">Smart Travel</div>
                <div className="mt-1 truncate text-xs text-sidebar-foreground/70">Khám phá ẩm thực</div>
              </div>
            )}
          </Link>

          {/* Desktop toggle button (top-right of sidebar header) */}
          {!isCollapsed && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Thu gọn sidebar"
              className="ml-auto h-9 w-9 rounded-lg text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              onClick={(event) => {
                event.stopPropagation();
                toggleCollapsed();
              }}
            >
              <PanelLeftIcon className="h-5 w-5" />
            </Button>
          )}
        </div>

        {/* Navigation Items */}
        <nav
          className={cn(
            "w-full flex-1 overflow-y-auto py-4 space-y-1",
            isCollapsed ? "px-0 flex flex-col items-center" : "px-3",
          )}
        >
          {navItems.map((item) => (
            <Button
              key={item.path}
              asChild
              variant="ghost"
              size={isCollapsed ? "icon" : "default"}
              className={cn(
                "transition-colors",
                isActive(item.path)
                  ? "bg-sidebar-primary text-sidebar-primary-foreground hover:bg-sidebar-primary/90"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                isCollapsed
                  ? "h-11 w-11 rounded-xl p-0 gap-0"
                  : "w-full justify-start gap-3 rounded-lg px-3 py-2 text-sm font-medium",
              )}
            >
              <Link to={item.path} title={item.label}>
                <item.icon className={cn("shrink-0", isCollapsed ? "h-6 w-6" : "h-5 w-5")} />
                {!isCollapsed && <span className="truncate">{item.label}</span>}
              </Link>
            </Button>
          ))}
        </nav>

        {/* Footer */}
        <div
          className={cn(
            "w-full border-t border-sidebar-border flex flex-col gap-2",
            isCollapsed ? "items-center p-2" : "p-3",
          )}
        >
          <Button
            variant="ghost"
            onClick={toggleTheme}
            aria-label="Đổi giao diện"
            className={cn(
              "rounded-lg transition-colors text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              theme === "pink" ? "bg-sidebar-accent text-sidebar-accent-foreground" : "",
              isCollapsed ? "h-11 w-11 rounded-xl p-0 gap-0" : "w-full justify-start px-3",
            )}
            size={isCollapsed ? "icon" : "lg"}
          >
            <Palette className={cn("h-5 w-5", isCollapsed ? "" : "mr-3")} />
            {!isCollapsed && <span>Giao diện: {theme === "pink" ? "Hồng" : "Tech"}</span>}
          </Button>

          {/* User */}
          {user ? (
            <UserMenu
              userName={user.name}
              userEmail={user.email}
              avatarUrl={user.avatar ?? null}
              onLogout={onLogout}
              compact={isCollapsed}
              dropdownSide="right"
              dropdownAlign={isCollapsed ? "start" : "end"}
              className={cn(
                isCollapsed ? "h-11 w-11 p-0 justify-center rounded-xl" : "w-full justify-start",
              )}
            />
          ) : (
            <Button
              variant="ghost"
              onClick={onLoginClick}
              className={cn(
                "rounded-lg transition-colors text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                isCollapsed ? "h-11 w-11 rounded-xl p-0 gap-0" : "w-full justify-start px-3",
              )}
              size={isCollapsed ? "icon" : "lg"}
            >
              <LogIn className={cn("h-5 w-5", isCollapsed ? "" : "mr-3")} />
              {!isCollapsed && <span>Đăng nhập</span>}
            </Button>
          )}
        </div>
      </aside>

      {/* Mobile Navigation */}
      <div className="lg:hidden fixed z-40 top-[calc(env(safe-area-inset-top)+1rem)] left-[calc(env(safe-area-inset-left)+1rem)]">
        <Sheet>
          <SheetTrigger asChild>
            <Button
              className="bg-primary text-primary-foreground rounded-xl shadow-sm"
              size="icon"
            >
              <PanelLeftIcon className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent 
            side="left" 
            className="bg-sidebar text-sidebar-foreground border-r border-sidebar-border w-72 p-0"
          >
            <SheetHeader className="sr-only">
              <SheetTitle>Menu</SheetTitle>
              <SheetDescription>Điều hướng nhanh trong ứng dụng</SheetDescription>
            </SheetHeader>
            <div className="flex flex-col h-full">
              <div className="flex items-center gap-3 border-b border-sidebar-border px-4 py-4">
                <Link to="/" className="flex min-w-0 items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sidebar-accent text-sidebar-accent-foreground ring-1 ring-sidebar-border">
                    <UtensilsCrossed className="h-5 w-5 text-highlight" />
                  </div>
                  <div className="min-w-0">
                    <div className="truncate font-semibold leading-none">Smart Travel</div>
                    <div className="mt-1 truncate text-xs text-sidebar-foreground/70">Khám phá ẩm thực</div>
                  </div>
                </Link>
              </div>

              <div className="space-y-1 px-3 py-4">
                {navItems.map((item) => (
                  <Link key={item.path} to={item.path}>
                    <Button
                      variant="ghost"
                      className={cn(
                        "w-full justify-start gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                        isActive(item.path)
                          ? "bg-sidebar-primary text-sidebar-primary-foreground hover:bg-sidebar-primary/90"
                          : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                      )}
                    >
                      <item.icon className="h-5 w-5 shrink-0" />
                      {item.label}
                    </Button>
                  </Link>
                ))}
              </div>

              <div className="mt-auto p-3 border-t border-sidebar-border space-y-2">
                <Button
                  variant="ghost"
                  onClick={toggleTheme}
                  aria-label="Đổi giao diện"
                  className={cn(
                    "w-full justify-start gap-3 rounded-lg transition-colors text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    theme === "pink" ? "bg-sidebar-accent text-sidebar-accent-foreground" : "",
                  )}
                >
                  <Palette className="h-5 w-5 shrink-0" />
                  Giao diện: {theme === "pink" ? "Hồng" : "Tech"}
                </Button>

                {user ? (
                  <UserMenu
                    userName={user.name}
                    userEmail={user.email}
                    avatarUrl={user.avatar ?? null}
                    onLogout={onLogout}
                    dropdownSide="top"
                    dropdownAlign="start"
                    className="w-full justify-start"
                  />
                ) : (
                  <Button
                    variant="ghost"
                    onClick={onLoginClick}
                    className="w-full justify-start gap-3 rounded-lg text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  >
                    <LogIn className="h-5 w-5 shrink-0" />
                    Đăng nhập
                  </Button>
                )}
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
}
