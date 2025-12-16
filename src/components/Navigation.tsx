import { Link, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import { Sheet, SheetContent, SheetTrigger } from "./ui/sheet";
import { Home, Store, Calendar, UtensilsCrossed, MessageCircle, Info, Mail, Star, FileText, Menu, ChevronLeft, ChevronRight } from "lucide-react";
import { useSidebar } from "../context/SidebarContext";

const navItems = [
  { path: "/", label: "Trang chủ", icon: Home },
  { path: "/restaurants", label: "Nhà hàng", icon: Store },
  { path: "/bookings", label: "Đặt chỗ", icon: Calendar },
  { path: "/menu", label: "Menu", icon: UtensilsCrossed },
  { path: "/chatbot", label: "Gợi ý món", icon: MessageCircle },
  { path: "/reviews", label: "Đánh giá", icon: Star },
  { path: "/about", label: "Giới thiệu", icon: Info },
  { path: "/contact", label: "Liên hệ", icon: Mail },
  { path: "/policy", label: "Chính sách", icon: FileText },
];

export function Navigation() {
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
                <p className="text-pink-500 text-xs">Khám phá ẩm thực</p>
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

        {/* Collapse Toggle */}
        <div className="p-3 border-t border-pink-200">
          <Button
            variant="ghost"
            onClick={toggleCollapsed}
            className="w-full justify-center rounded-xl text-pink-600 hover:bg-pink-100 font-bold"
            size="sm"
          >
            {isCollapsed ? (
              <ChevronRight className="h-5 w-5" />
            ) : (
              <>
                <ChevronLeft className="h-5 w-5" />
                <span>Thu gọn</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Mobile Navigation */}
      <div className="lg:hidden fixed top-4 left-4 z-40">
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
            <div className="space-y-2 mt-8">
              <Link to="/" className="flex items-center gap-3 mb-6 px-2 hover:bg-pink-50 rounded-xl py-2 transition-colors cursor-pointer">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-pink-400 to-rose-400 flex items-center justify-center text-white text-xl">
                  🍜
                </div>
                <div>
                  <h1 className="text-pink-800 text-lg font-bold">Food Assistant</h1>
                  <p className="text-pink-600 text-xs">Khám phá ẩm thực</p>
                </div>
              </Link>
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
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
}
