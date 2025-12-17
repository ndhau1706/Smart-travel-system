import { Link, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "./ui/sheet";
import { Home, Store, UtensilsCrossed, MessageCircle, Info, Mail, FileText, Menu, ChevronLeft, ChevronRight, LogIn } from "lucide-react";
import { useSidebar } from "../context/SidebarContext";
import { UserMenu } from "./UserMenu";
import { cn } from "./ui/utils";

const navItems = [
  { path: "/", label: "Trang chủ", icon: Home },
  { path: "/restaurants", label: "Nhà hàng", icon: Store },
  { path: "/menu", label: "Menu", icon: UtensilsCrossed },
  { path: "/chatbot", label: "Gợi ý món", icon: MessageCircle },
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

  const isActive = (path: string) => {
    if (path === "/") return currentPath === "/";
    return currentPath.startsWith(path);
  };

  return (
    <>
      {/* Desktop Sidebar */}
      <div 
        className={`hidden lg:flex fixed top-0 left-0 h-full z-40 flex-col bg-gradient-to-b from-pink-100 via-rose-100 to-pink-50 border-r-2 border-pink-200 shadow-xl transition-all duration-300 ${
          isCollapsed ? "w-20" : "w-64"
        }`}
        style={{ boxShadow: "4px 0 25px rgba(255,182,193,0.3)" }}
      >
        {/* Logo/Brand - Click to go home */}
        <Link to="/" className="p-4 border-b border-pink-200 block hover:bg-pink-50 transition-colors cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-pink-400 to-rose-400 flex items-center justify-center text-white text-xl">
              🍜
            </div>
            {!isCollapsed && (
              <div>
                <h1 className="text-pink-800 text-lg font-bold">Food Assistant</h1>
                <p className="text-pink-600 text-xs">Khám phá ẩm thực</p>
              </div>
            )}
          </div>
        </Link>

        {/* Navigation Items */}
        <nav className="flex-1 p-3 space-y-2 overflow-y-auto">
          {navItems.map((item) => (
            <Link key={item.path} to={item.path}>
              <Button
                variant={isActive(item.path) ? "default" : "ghost"}
                className={`w-full justify-start rounded-xl transition-all duration-200 ${
                  isActive(item.path)
                    ? "bg-gradient-to-r from-pink-400 to-rose-400 text-white shadow-lg"
                    : "text-pink-700 hover:bg-pink-100 hover:text-pink-800"
                } ${isCollapsed ? "px-3" : "px-4"}`}
                size="lg"
              >
                <item.icon className={`h-5 w-5 ${isCollapsed ? "" : "mr-3"}`} />
                {!isCollapsed && <span>{item.label}</span>}
              </Button>
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-pink-200 space-y-2">
          {/* User */}
          {user ? (
            <UserMenu
              userName={user.name}
              userEmail={user.email}
              avatarUrl={user.avatar ?? null}
              onLogout={onLogout}
              compact={isCollapsed}
              dropdownSide="top"
              dropdownAlign={isCollapsed ? "start" : "end"}
              className={cn(
                "w-full",
                isCollapsed ? "justify-center" : "justify-start",
              )}
            />
          ) : (
            <Button
              variant="ghost"
              onClick={onLoginClick}
              className={cn(
                "w-full rounded-xl transition-all duration-200 text-pink-700 hover:bg-pink-100 hover:text-pink-800",
                isCollapsed ? "justify-center px-3" : "justify-start px-4",
              )}
              size="lg"
            >
              <LogIn className={cn("h-5 w-5", isCollapsed ? "" : "mr-3")} />
              {!isCollapsed && <span>Đăng nhập</span>}
            </Button>
          )}

          {/* Collapse Toggle */}
          <Button
            variant="ghost"
            onClick={toggleCollapsed}
            className="w-full justify-center rounded-xl text-pink-600 hover:bg-pink-100"
            size="sm"
          >
            {isCollapsed ? (
              <ChevronRight className="h-5 w-5" />
            ) : (
              <>
                <ChevronLeft className="h-5 w-5 mr-2" />
                <span>Thu gọn</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Mobile Navigation */}
      <div className="lg:hidden fixed top-safe-4 left-safe-4 z-40">
        <Sheet>
          <SheetTrigger asChild>
            <Button
              className="bg-gradient-to-r from-pink-400 to-rose-400 text-white rounded-2xl shadow-xl border-2 border-pink-200"
              style={{ boxShadow: "0 0 25px rgba(255,182,193,0.4)" }}
              size="icon"
            >
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent 
            side="left" 
            className="bg-gradient-to-br from-pink-100 via-rose-100 to-pink-50 border-r-2 border-pink-200 w-72"
          >
            <SheetHeader className="sr-only">
              <SheetTitle>Menu</SheetTitle>
              <SheetDescription>Điều hướng nhanh trong ứng dụng</SheetDescription>
            </SheetHeader>
            <div className="flex flex-col h-full mt-8">
              <Link to="/" className="flex items-center gap-3 mb-6 px-2 hover:bg-pink-50 rounded-xl py-2 transition-colors cursor-pointer">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-pink-400 to-rose-400 flex items-center justify-center text-white text-xl">
                  🍜
                </div>
                <div>
                  <h1 className="text-pink-800 text-lg font-bold">Food Assistant</h1>
                  <p className="text-pink-500 text-xs">Khám phá ẩm thực</p>
                </div>
              </Link>

              <div className="space-y-2">
                {navItems.map((item) => (
                  <Link key={item.path} to={item.path}>
                    <Button
                      variant={isActive(item.path) ? "default" : "ghost"}
                      className={`w-full justify-start rounded-xl ${
                        isActive(item.path)
                          ? "bg-gradient-to-r from-pink-400 to-rose-400 text-white"
                          : "text-pink-700 hover:bg-pink-100"
                      }`}
                      size="lg"
                    >
                      <item.icon className="h-5 w-5 mr-3" />
                      {item.label}
                    </Button>
                  </Link>
                ))}
              </div>

              <div className="mt-auto pt-4 border-t border-pink-200">
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
                    className="w-full justify-start rounded-xl text-pink-700 hover:bg-pink-100"
                    size="lg"
                  >
                    <LogIn className="h-5 w-5 mr-3" />
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
