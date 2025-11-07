import { useState, useEffect, useRef } from "react";
import { ChatSidebar } from "./components/ChatSidebar";
import { ChatMessage } from "./components/ChatMessage";
import { ChatInput } from "./components/ChatInput";
import { PromptSuggestions } from "./components/PromptSuggestions";
import { AuthDialog } from "./components/AuthDialog";
import { UserMenu } from "./components/UserMenu";
import { Navigation } from "./components/Navigation";
import { HomePage } from "./components/HomePage";
import { RestaurantList } from "./components/RestaurantList";
import { RestaurantDetail } from "./components/RestaurantDetail";
import { BookingsPage } from "./components/BookingsPage";
import { MenuPage } from "./components/MenuPage";
import { AboutPage } from "./components/AboutPage";
import { ContactPage } from "./components/ContactPage";
import { ReviewsPage } from "./components/ReviewsPage";
import { PolicyPage } from "./components/PolicyPage";
import { ThankYouPage } from "./components/ThankYouPage";
import { FloatingChatbot } from "./components/FloatingChatbot";
import { ScrollArea } from "./components/ui/scroll-area";
import { Button } from "./components/ui/button";
import { Toaster } from "./components/ui/sonner";
import { UtensilsCrossed, LogIn } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface Chat {
  id: string;
  title: string;
  timestamp: Date;
  messages: Message[];
}

interface User {
  email: string;
  name: string;
}

interface MenuItem {
  id: string;
  name: string;
  description: string;
  price: number;
  image: string;
  category: string;
}

interface Restaurant {
  id: string;
  name: string;
  image: string;
  cuisine: string;
  rating: number;
  reviewCount: number;
  priceLevel: number;
  distance: string;
  openTime: string;
  specialty: string[];
  description: string;
  address: string;
  phone: string;
  menu: MenuItem[];
}

type View = "home" | "restaurants" | "chatbot" | "restaurant-detail" | "bookings" | "menu" | "about" | "contact" | "reviews" | "policy" | "thank-you";

// Mock restaurants data
const mockRestaurants: Restaurant[] = [
  {
    id: "1",
    name: "Phở Hà Nội",
    image: "https://images.unsplash.com/photo-1701480253822-1842236c9a97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcGhvJTIwbm9vZGxlJTIwc291cHxlbnwxfHx8fDE3NjI0MDY1OTB8MA&ixlib=rb-4.1.0&q=80&w=1080",
    cuisine: "Phở & Bún",
    rating: 4.8,
    reviewCount: 234,
    priceLevel: 2,
    distance: "1.2 km",
    openTime: "7:00 - 22:00",
    specialty: ["Phở Bò", "Phở Gà", "Bún Chả"],
    description: "Nhà hàng phở truyền thống với công thức nấu nước dùng hơn 50 năm. Phở Hà Nội mang đến hương vị phở đậm đà, nguyên bản từ Hà Thành.",
    address: "123 Nguyễn Huệ, Quận 1, TP.HCM",
    phone: "028 3823 4567",
    menu: [
      {
        id: "m1",
        name: "Phở Bò Tái",
        description: "Phở bò tái mềm với nước dùng đậm đà",
        price: 65000,
        image: "https://images.unsplash.com/photo-1701480253822-1842236c9a97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcGhvJTIwbm9vZGxlJTIwc291cHxlbnwxfHx8fDE3NjI0MDY1OTB8MA&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Phở",
      },
      {
        id: "m2",
        name: "Phở Bò Chín",
        description: "Phở bò chín với thịt bò mềm",
        price: 70000,
        image: "https://images.unsplash.com/photo-1701480253822-1842236c9a97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcGhvJTIwbm9vZGxlJTIwc291cHxlbnwxfHx8fDE3NjI0MDY1OTB8MA&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Phở",
      },
      {
        id: "m3",
        name: "Phở Gà",
        description: "Phở gà thanh ngọt với thịt gà thơm ngon",
        price: 60000,
        image: "https://images.unsplash.com/photo-1701480253822-1842236c9a97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcGhvJTIwbm9vZGxlJTIwc291cHxlbnwxfHx8fDE3NjI0MDY1OTB8MA&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Phở",
      },
      {
        id: "m4",
        name: "Bún Chả Hà Nội",
        description: "Bún chả với thịt nướng thơm phức",
        price: 75000,
        image: "https://images.unsplash.com/photo-1602227479007-d98c5757238e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwYnVuJTIwY2hhfGVufDF8fHx8MTc2MjMzMjg4NHww&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Bún",
      },
    ],
  },
  {
    id: "2",
    name: "Bánh Mì Sài Gòn",
    image: "https://images.unsplash.com/photo-1599719455360-ff0be7c4dd06?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwYmFuaCUyMG1pJTIwc2FuZHdpY2h8ZW58MXx8fHwxNzYyNDA2NTkwfDA&ixlib=rb-4.1.0&q=80&w=1080",
    cuisine: "Bánh mì & Đồ ăn sáng",
    rating: 4.6,
    reviewCount: 189,
    priceLevel: 1,
    distance: "0.8 km",
    openTime: "6:00 - 14:00",
    specialty: ["Bánh Mì Thịt", "Bánh Mì Chả", "Bánh Mì Pate"],
    description: "Bánh mì Sài Gòn giòn tan với nhiều loại nhân đa dạng. Sử dụng bánh mì nướng tươi mỗi ngày và nguyên liệu tươi ngon.",
    address: "45 Pasteur, Quận 1, TP.HCM",
    phone: "028 3829 1234",
    menu: [
      {
        id: "m5",
        name: "Bánh Mì Thịt Nướng",
        description: "Bánh mì với thịt nướng thơm lừng",
        price: 25000,
        image: "https://images.unsplash.com/photo-1599719455360-ff0be7c4dd06?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwYmFuaCUyMG1pJTIwc2FuZHdpY2h8ZW58MXx8fHwxNzYyNDA2NTkwfDA&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Bánh mì",
      },
      {
        id: "m6",
        name: "Bánh Mì Pate",
        description: "Bánh mì pate truyền thống",
        price: 20000,
        image: "https://images.unsplash.com/photo-1599719455360-ff0be7c4dd06?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwYmFuaCUyMG1pJTIwc2FuZHdpY2h8ZW58MXx8fHwxNzYyNDA2NTkwfDA&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Bánh mì",
      },
      {
        id: "m7",
        name: "Bánh Mì Xíu Mại",
        description: "Bánh mì với xíu mại sốt cà",
        price: 30000,
        image: "https://images.unsplash.com/photo-1599719455360-ff0be7c4dd06?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwYmFuaCUyMG1pJTIwc2FuZHdpY2h8ZW58MXx8fHwxNzYyNDA2NTkwfDA&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Bánh mì",
      },
    ],
  },
  {
    id: "3",
    name: "Nhà Hàng Hải Sản Biển Xanh",
    image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
    cuisine: "Hải sản",
    rating: 4.7,
    reviewCount: 156,
    priceLevel: 3,
    distance: "2.5 km",
    openTime: "10:00 - 22:00",
    specialty: ["Tôm Hấp", "Cua Rang Me", "Cá Chiên"],
    description: "Nhà hàng hải sản tươi sống với không gian rộng rãi, thoáng mát. Chuyên các món hải sản chế biến theo phong cách Việt Nam.",
    address: "789 Võ Văn Tần, Quận 3, TP.HCM",
    phone: "028 3930 5678",
    menu: [
      {
        id: "m8",
        name: "Tôm Hấp Bia",
        description: "Tôm tươi hấp bia thơm ngon",
        price: 280000,
        image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Hải sản",
      },
      {
        id: "m9",
        name: "Cua Rang Me",
        description: "Cua rang me chua ngọt đậm đà",
        price: 450000,
        image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Hải sản",
      },
      {
        id: "m10",
        name: "Cá Chiên Giòn",
        description: "Cá chiên giòn với nước mắm",
        price: 320000,
        image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Hải sản",
      },
    ],
  },
  {
    id: "4",
    name: "Gỏi Cuốn Sài Gòn",
    image: "https://images.unsplash.com/photo-1693494869603-09f1981f28e0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwc3ByaW5nJTIwcm9sbHN8ZW58MXx8fHwxNzYyMzMyNjA2fDA&ixlib=rb-4.1.0&q=80&w=1080",
    cuisine: "Gỏi & Salad",
    rating: 4.5,
    reviewCount: 98,
    priceLevel: 2,
    distance: "1.5 km",
    openTime: "9:00 - 21:00",
    specialty: ["Gỏi Cuốn", "Gỏi Ngó Sen", "Salad Tôm"],
    description: "Chuyên các món gỏi cuốn tươi ngon với rau sống và nước chấm đặc biệt. Không gian sạch sẽ, thoáng mát.",
    address: "234 Lê Thánh Tôn, Quận 1, TP.HCM",
    phone: "028 3824 7890",
    menu: [
      {
        id: "m11",
        name: "Gỏi Cuốn Tôm Thịt",
        description: "Gỏi cuốn với tôm và thịt heo",
        price: 50000,
        image: "https://images.unsplash.com/photo-1693494869603-09f1981f28e0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwc3ByaW5nJTIwcm9sbHN8ZW58MXx8fHwxNzYyMzMyNjA2fDA&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Gỏi cuốn",
      },
      {
        id: "m12",
        name: "Gỏi Ngó Sen",
        description: "Gỏi ngó sen giòn ngọt",
        price: 65000,
        image: "https://images.unsplash.com/photo-1693494869603-09f1981f28e0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwc3ByaW5nJTIwcm9sbHN8ZW58MXx8fHwxNzYyMzMyNjA2fDA&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Gỏi",
      },
      {
        id: "m13",
        name: "Gỏi Cuốn Chay",
        description: "Gỏi cuốn chay với đậu hũ",
        price: 45000,
        image: "https://images.unsplash.com/photo-1693494869603-09f1981f28e0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwc3ByaW5nJTIwcm9sbHN8ZW58MXx8fHwxNzYyMzMyNjA2fDA&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Gỏi cuốn",
      },
    ],
  },
  {
    id: "5",
    name: "Cơm Tấm Sài Gòn",
    image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
    cuisine: "Cơm",
    rating: 4.6,
    reviewCount: 176,
    priceLevel: 1,
    distance: "1.8 km",
    openTime: "6:00 - 23:00",
    specialty: ["Cơm Tấm Sườn", "Cơm Tấm Bì", "Cơm Gà"],
    description: "Cơm tấm truyền thống Sài Gòn với sườn nướng thơm ngon, bì giòn và chả trứng đặc biệt.",
    address: "567 Cách Mạng Tháng 8, Quận 3, TP.HCM",
    phone: "028 3932 4567",
    menu: [
      {
        id: "m14",
        name: "Cơm Tấm Sườn Bì Chả",
        description: "Cơm tấm đầy đủ với sườn, bì, chả",
        price: 55000,
        image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Cơm",
      },
      {
        id: "m15",
        name: "Cơm Gà Xối Mỡ",
        description: "Cơm gà xối mỡ hành thơm lừng",
        price: 50000,
        image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Cơm",
      },
    ],
  },
  {
    id: "6",
    name: "Nhà Hàng Chay Sen Việt",
    image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
    cuisine: "Chay",
    rating: 4.8,
    reviewCount: 142,
    priceLevel: 2,
    distance: "3.0 km",
    openTime: "8:00 - 21:00",
    specialty: ["Phở Chay", "Bún Chay", "Cơm Chay"],
    description: "Nhà hàng chay với không gian yên tĩnh, thanh tịnh. Các món ăn chay đa dạng, bổ dưỡng và ngon miệng.",
    address: "890 Trần Hưng Đạo, Quận 5, TP.HCM",
    phone: "028 3855 6789",
    menu: [
      {
        id: "m16",
        name: "Phở Chay",
        description: "Phở chay với nước dùng thanh ngọt",
        price: 55000,
        image: "https://images.unsplash.com/photo-1701480253822-1842236c9a97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcGhvJTIwbm9vZGxlJTIwc291cHxlbnwxfHx8fDE3NjI0MDY1OTB8MA&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Món chính",
      },
      {
        id: "m17",
        name: "Bún Chay",
        description: "Bún chay với rau củ tươi ngon",
        price: 50000,
        image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Món chính",
      },
      {
        id: "m18",
        name: "Cơm Chiên Chay",
        description: "Cơm chiên chay với rau củ và đậu",
        price: 45000,
        image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
        category: "Món chính",
      },
    ],
  },
];

// Mock travel food AI responses
const travelFoodResponses = [
  "Dựa trên vị trí của bạn, tôi gợi ý thử phở tại Phở Hà Nội - một trong những quán phở truyền thống tốt nhất với nước dùng nguyên bản!",
  "Bánh mì Sài Gòn gần đây là lựa chọn tuyệt vời cho bữa sáng! Họ mở cửa từ 6:00 sáng với bánh mì giòn tan và nhiều loại nhân đa dạng.",
  "Nếu bạn thích hải sản, Nhà Hàng Hải Sản Biển Xanh là nơi hoàn hảo với tôm hấp và cua rang me tuyệt ngon!",
  "Món bún chả tại Phở Hà Nội rất đáng thử! Thịt nướng thơm phức với nước chấm đặc biệt là điểm nhấn của món này.",
  "Cơm tấm Sài Gòn là lựa chọn tốt cho bữa trưa với giá phải chăng chỉ từ 50-55k. Sườn nướng và bì rất ngon!",
  "Nếu bạn ăn chay, Nhà Hàng Chay Sen Việt có nhiều món chay sáng tạo và ngon miệng. Phở chay của họ rất được yêu thích!",
];

function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export default function App() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [authDialogOpen, setAuthDialogOpen] = useState(false);
  const [currentView, setCurrentView] = useState<View>("home");
  const [selectedRestaurant, setSelectedRestaurant] = useState<Restaurant | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const currentChat = chats.find((chat) => chat.id === currentChatId);

  const handleLogin = (email: string, name: string) => {
    setUser({ email, name });
  };

  const handleLogout = () => {
    setUser(null);
  };

  useEffect(() => {
    if (currentView === "chatbot" && chats.length === 0) {
      handleNewChat();
    }
  }, [currentView]);

  useEffect(() => {
    if (scrollAreaRef.current && currentView === "chatbot") {
      const viewport = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]");
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [currentChat?.messages, currentView]);

  const handleNewChat = () => {
    const newChat: Chat = {
      id: generateId(),
      title: "New Chat",
      timestamp: new Date(),
      messages: [],
    };
    setChats((prev) => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    setSidebarOpen(false);
  };

  const handleSelectChat = (id: string) => {
    setCurrentChatId(id);
    setSidebarOpen(false);
  };

  const handleDeleteChat = (id: string) => {
    setChats((prev) => prev.filter((chat) => chat.id !== id));
    if (currentChatId === id) {
      const remainingChats = chats.filter((chat) => chat.id !== id);
      setCurrentChatId(remainingChats[0]?.id || null);
      if (remainingChats.length === 0) {
        handleNewChat();
      }
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!currentChatId) return;

    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content,
    };

    setChats((prev) =>
      prev.map((chat) => {
        if (chat.id === currentChatId) {
          const updatedMessages = [...chat.messages, userMessage];
          const title =
            chat.messages.length === 0
              ? content.slice(0, 30) + (content.length > 30 ? "..." : "")
              : chat.title;
          return { ...chat, messages: updatedMessages, title };
        }
        return chat;
      })
    );

    setIsGenerating(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const assistantMessage: Message = {
      id: generateId(),
      role: "assistant",
      content: travelFoodResponses[Math.floor(Math.random() * travelFoodResponses.length)],
    };

    setChats((prev) =>
      prev.map((chat) =>
        chat.id === currentChatId
          ? { ...chat, messages: [...chat.messages, assistantMessage] }
          : chat
      )
    );
    setIsGenerating(false);
  };

  const handleSelectRestaurant = (restaurant: Restaurant) => {
    setSelectedRestaurant(restaurant);
    setCurrentView("restaurant-detail");
  };

  const handleBackToRestaurants = () => {
    setSelectedRestaurant(null);
    setCurrentView("restaurants");
  };

  return (
    <div className="h-screen flex bg-gradient-to-br from-pink-100 via-purple-100 to-fuchsia-100 text-gray-800 relative overflow-hidden">
      <Toaster position="top-center" />
      
      {/* Auth Dialog */}
      <AuthDialog open={authDialogOpen} onOpenChange={setAuthDialogOpen} onLogin={handleLogin} />

      {/* User Menu or Login Button */}
      {user ? (
        <UserMenu userName={user.name} userEmail={user.email} onLogout={handleLogout} />
      ) : (
        <Button
          onClick={() => setAuthDialogOpen(true)}
          className="fixed top-4 right-4 z-50 flex items-center gap-2 bg-gradient-to-br from-pink-400 to-rose-400 backdrop-blur-lg border-2 border-pink-200 shadow-xl hover:from-pink-300 hover:to-rose-300 rounded-2xl text-white"
          style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
        >
          <LogIn className="h-4 w-4" />
          <span className="hidden sm:inline">Đăng nhập</span>
        </Button>
      )}

      {/* Navigation Bar */}
      <Navigation
        currentView={currentView}
        onNavigate={(view) => setCurrentView(view)}
      />

      {/* Pastel Pink Galaxy/Nebula Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-pink-200/60 via-purple-200/50 to-fuchsia-200/60" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-pink-300/40 via-transparent to-transparent" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-fuchsia-300/40 via-transparent to-transparent" />

      {/* Twinkling Pink Stars */}
      {[...Array(50)].map((_, i) => (
        <div
          key={`star-${i}`}
          className="star"
          style={{
            width: Math.random() * 4 + 2 + "px",
            height: Math.random() * 4 + 2 + "px",
            left: Math.random() * 100 + "%",
            top: Math.random() * 100 + "%",
            animationDelay: Math.random() * 3 + "s",
            animationDuration: Math.random() * 2 + 2 + "s",
            background:
              "radial-gradient(circle, rgba(255,182,193,1) 0%, rgba(255,105,180,0.9) 50%, transparent 100%)",
          }}
        />
      ))}

      {/* Floating Food Emojis */}
      <div className="food-emoji-float absolute top-10 left-20 text-6xl" style={{ animationDuration: "4s" }}>🍜</div>
      <div className="food-emoji-float absolute top-40 right-32 text-5xl" style={{ animationDuration: "5s", animationDelay: "0.5s" }}>🥖</div>
      <div className="food-emoji-float absolute bottom-20 left-40 text-5xl" style={{ animationDuration: "4.5s", animationDelay: "1s" }}>🌶️</div>
      <div className="food-emoji-float absolute bottom-32 right-20 text-6xl" style={{ animationDuration: "5.5s", animationDelay: "1.5s" }}>🥢</div>
      <div className="food-emoji-float absolute top-1/2 right-10 text-4xl" style={{ animationDuration: "4s", animationDelay: "2s" }}>🍲</div>
      <div className="food-emoji-float absolute top-1/3 left-1/4 text-5xl" style={{ animationDuration: "4.8s", animationDelay: "0.8s" }}>☕</div>
      <div className="food-emoji-float absolute bottom-1/4 right-1/3 text-4xl" style={{ animationDuration: "5.2s", animationDelay: "1.2s" }}>🥘</div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative z-10">
        {currentView === "home" && (
          <HomePage onNavigateToRestaurants={() => setCurrentView("restaurants")} />
        )}

        {currentView === "restaurants" && (
          <RestaurantList restaurants={mockRestaurants} onSelectRestaurant={handleSelectRestaurant} />
        )}

        {currentView === "restaurant-detail" && selectedRestaurant && (
          <RestaurantDetail restaurant={selectedRestaurant} onBack={handleBackToRestaurants} />
        )}

        {currentView === "chatbot" && (
          <>
            <ChatSidebar
              chats={chats}
              currentChatId={currentChatId}
              onSelectChat={handleSelectChat}
              onNewChat={handleNewChat}
              onDeleteChat={handleDeleteChat}
              isOpen={sidebarOpen}
              onToggle={() => setSidebarOpen(!sidebarOpen)}
            />

            <div className="flex-1 flex flex-col">
              {currentChat ? (
                <>
                  <ScrollArea className="flex-1" ref={scrollAreaRef}>
                    <div className="max-w-3xl mx-auto pt-20">
                      {currentChat.messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full min-h-[500px] p-6">
                          <div className="flex items-center gap-3 mb-6">
                            <div
                              className="p-5 rounded-full bg-gradient-to-br from-pink-400 via-rose-400 to-fuchsia-400 shadow-2xl shadow-pink-400/60 animate-pulse border-4 border-pink-200"
                              style={{
                                animationDuration: "2s",
                                boxShadow: "0 0 40px rgba(255,182,193,0.6), inset 0 0 20px rgba(255,255,255,0.5)",
                              }}
                            >
                              <UtensilsCrossed className="h-12 w-12 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]" />
                            </div>
                          </div>
                          <div className="text-center space-y-3 mb-8">
                            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
                              🍜 Trợ Lý Ẩm Thực AI 🥢
                            </h1>
                            <p className="text-pink-700 drop-shadow-[0_1px_4px_rgba(255,182,193,0.3)]">
                              ✨ Hỏi tôi về món ăn Việt Nam và nhận gợi ý nhà hàng tuyệt vời! ✨
                            </p>
                          </div>
                          <PromptSuggestions onSelectPrompt={handleSendMessage} />
                        </div>
                      ) : (
                        <div>
                          {currentChat.messages.map((message) => (
                            <ChatMessage key={message.id} role={message.role} content={message.content} />
                          ))}
                          {isGenerating && (
                            <div
                              className="flex gap-4 p-6 bg-gradient-to-r from-pink-200/80 via-rose-200/80 to-fuchsia-200/80 backdrop-blur-md border-2 border-pink-300 rounded-3xl my-2 mx-4 shadow-lg"
                              style={{
                                boxShadow: "0 0 25px rgba(255,182,193,0.4), inset 0 0 20px rgba(255,255,255,0.3)",
                              }}
                            >
                              <div className="flex gap-2">
                                <div
                                  className="w-4 h-4 bg-gradient-to-r from-pink-400 to-rose-400 rounded-full animate-bounce shadow-lg"
                                  style={{ boxShadow: "0 0 12px rgba(255,182,193,0.6)" }}
                                />
                                <div
                                  className="w-4 h-4 bg-gradient-to-r from-rose-400 to-fuchsia-400 rounded-full animate-bounce shadow-lg"
                                  style={{ animationDelay: "0.2s", boxShadow: "0 0 12px rgba(255,182,193,0.6)" }}
                                />
                                <div
                                  className="w-4 h-4 bg-gradient-to-r from-fuchsia-400 to-pink-400 rounded-full animate-bounce shadow-lg"
                                  style={{ animationDelay: "0.4s", boxShadow: "0 0 12px rgba(255,182,193,0.6)" }}
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </ScrollArea>

                  <ChatInput onSendMessage={handleSendMessage} disabled={isGenerating} />
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <p className="text-pink-600">Chọn chat hoặc tạo chat mới</p>
                </div>
              )}
            </div>
          </>
        )}

        {currentView === "bookings" && (
          <BookingsPage />
        )}

        {currentView === "menu" && (
          <MenuPage />
        )}

        {currentView === "about" && (
          <AboutPage />
        )}

        {currentView === "contact" && (
          <ContactPage />
        )}

        {currentView === "reviews" && (
          <ReviewsPage />
        )}

        {currentView === "policy" && (
          <PolicyPage />
        )}

        {currentView === "thank-you" && (
          <ThankYouPage
            onNavigateHome={() => setCurrentView("home")}
            onNavigateBookings={() => setCurrentView("bookings")}
            onNavigateChatbot={() => setCurrentView("chatbot")}
          />
        )}
      </div>

      {/* Floating Chatbot - only show on non-chatbot views */}
      {currentView !== "chatbot" && <FloatingChatbot />}
    </div>
  );
}