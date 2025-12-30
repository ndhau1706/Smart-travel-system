import { Button } from "./ui/button";
import { Sheet, SheetContent, SheetTrigger } from "./ui/sheet";
import { Home, Store, Calendar, UtensilsCrossed, MessageCircle, Info, Mail, Star, FileText, Menu } from "lucide-react";

type ViewType = "home" | "restaurants" | "bookings" | "menu" | "chatbot" | "about" | "contact" | "reviews" | "policy";

interface NavigationProps {
  currentView: ViewType;
  onNavigate: (view: ViewType) => void;
}

const navItems = [
  { id: "home" as ViewType, label: "Trang chủ", icon: Home },
  { id: "restaurants" as ViewType, label: "Nhà hàng", icon: Store },
  { id: "bookings" as ViewType, label: "Đặt chỗ", icon: Calendar },
  { id: "menu" as ViewType, label: "Menu", icon: UtensilsCrossed },
  { id: "chatbot" as ViewType, label: "Gợi ý món", icon: MessageCircle },
  { id: "reviews" as ViewType, label: "Đánh giá", icon: Star },
  { id: "about" as ViewType, label: "Giới thiệu", icon: Info },
  { id: "contact" as ViewType, label: "Liên hệ", icon: Mail },
  { id: "policy" as ViewType, label: "Chính sách", icon: FileText },
];

export function Navigation({ currentView, onNavigate }: NavigationProps) {
  return (
    <>
      {/* Desktop Navigation */}
      <div className="hidden lg:flex fixed top-4 left-1/2 -translate-x-1/2 z-40 gap-2 bg-white/90 backdrop-blur-xl border-2 border-pink-200 rounded-2xl p-2 shadow-xl max-w-5xl" style={{ boxShadow: "0 0 25px rgba(255,182,193,0.4)" }}>
        {navItems.map((item) => (
          <Button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            variant={currentView === item.id || (currentView === "restaurant-detail" && item.id === "restaurants") ? "default" : "ghost"}
            className={`rounded-xl whitespace-nowrap ${
              currentView === item.id || (currentView === "restaurant-detail" && item.id === "restaurants")
                ? "bg-gradient-to-r from-pink-400 to-rose-400 text-white"
                : "text-pink-700 hover:bg-pink-100"
            }`}
            size="sm"
          >
            <item.icon className="h-4 w-4 mr-2" />
            <span className="text-sm">{item.label}</span>
          </Button>
        ))}
      </div>

      {/* Mobile Navigation */}
      <div className="lg:hidden fixed top-4 left-1/2 -translate-x-1/2 z-40">
        <Sheet>
          <SheetTrigger asChild>
            <Button
              className="bg-gradient-to-r from-pink-400 to-rose-400 text-white rounded-2xl shadow-xl border-2 border-pink-200"
              style={{ boxShadow: "0 0 25px rgba(255,182,193,0.4)" }}
            >
              <Menu className="h-5 w-5 mr-2" />
              Menu
            </Button>
          </SheetTrigger>
          <SheetContent 
            side="left" 
            className="bg-gradient-to-br from-pink-50/98 via-rose-50/98 to-fuchsia-50/98 backdrop-blur-2xl border-r-2 border-pink-200"
          >
            <div className="space-y-4 mt-8">
              <h2 className="text-pink-800 mb-6">🍜 Menu điều hướng</h2>
              {navItems.map((item) => (
                <Button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  variant={currentView === item.id ? "default" : "ghost"}
                  className={`w-full justify-start rounded-xl ${
                    currentView === item.id
                      ? "bg-gradient-to-r from-pink-400 to-rose-400 text-white"
                      : "text-pink-700 hover:bg-pink-100"
                  }`}
                >
                  <item.icon className="h-5 w-5 mr-3" />
                  {item.label}
                </Button>
              ))}
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
}
