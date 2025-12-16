import { useState } from "react";
import { Card } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Input } from "../../components/ui/input";
import { ScrollArea } from "../../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Search, ChefHat } from "lucide-react";
import { ImageWithFallback } from "../../components/figma/ImageWithFallback";

interface MenuItem {
  id: string;
  name: string;
  description: string;
  price: number;
  image: string;
  category: string;
  restaurant: string;
  tags: string[];
}

const allMenuItems: MenuItem[] = [
  {
    id: "1",
    name: "Phở Bò Tái",
    description: "Phở bò tái mềm với nước dùng đậm đà, hành lá và ngò gai thơm lừng",
    price: 65000,
    image: "https://images.unsplash.com/photo-1701480253822-1842236c9a97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcGhvJTIwbm9vZGxlJTIwc291cHxlbnwxfHx8fDE3NjI0MDY1OTB8MA&ixlib=rb-4.1.0&q=80&w=1080",
    category: "Phở & Bún",
    restaurant: "Phở Hà Nội",
    tags: ["Bò", "Nóng", "Truyền thống"],
  },
  {
    id: "2",
    name: "Bún Chả Hà Nội",
    description: "Bún chả với thịt nướng thơm phức, chả viên và nước chấm chua ngọt",
    price: 75000,
    image: "https://images.unsplash.com/photo-1602227479007-d98c5757238e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwYnVuJTIwY2hhfGVufDF8fHx8MTc2MjMzMjg4NHww&ixlib=rb-4.1.0&q=80&w=1080",
    category: "Phở & Bún",
    restaurant: "Phở Hà Nội",
    tags: ["Thịt nướng", "Đặc sản Hà Nội"],
  },
  {
    id: "3",
    name: "Bánh Mì Thịt Nướng",
    description: "Bánh mì giòn tan với thịt nướng thơm lừng, rau sống và gia vị đặc biệt",
    price: 25000,
    image: "https://images.unsplash.com/photo-1599719455360-ff0be7c4dd06?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwYmFuaCUyMG1pJTIwc2FuZHdpY2h8ZW58MXx8fHwxNzYyNDA2NTkwfDA&ixlib=rb-4.1.0&q=80&w=1080",
    category: "Bánh mì",
    restaurant: "Bánh Mì Sài Gòn",
    tags: ["Ăn sáng", "Giá rẻ", "Nhanh"],
  },
  {
    id: "4",
    name: "Gỏi Cuốn Tôm Thịt",
    description: "Gỏi cuốn tươi mát với tôm, thịt heo, rau sống và bún tươi",
    price: 50000,
    image: "https://images.unsplash.com/photo-1693494869603-09f1981f28e0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwc3ByaW5nJTIwcm9sbHN8ZW58MXx8fHwxNzYyMzMyNjA2fDA&ixlib=rb-4.1.0&q=80&w=1080",
    category: "Khai vị",
    restaurant: "Gỏi Cuốn Sài Gòn",
    tags: ["Tươi mát", "Healthy", "Nhẹ nhàng"],
  },
  {
    id: "5",
    name: "Tôm Hấp Bia",
    description: "Tôm tươi hấp bia thơm ngon, giữ trọn vị ngọt tự nhiên",
    price: 280000,
    image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
    category: "Hải sản",
    restaurant: "Nhà Hàng Hải Sản Biển Xanh",
    tags: ["Hải sản", "Cao cấp", "Tươi sống"],
  },
  {
    id: "6",
    name: "Cơm Tấm Sườn Bì Chả",
    description: "Cơm tấm đầy đủ với sườn nướng, bì giòn và chả trứng",
    price: 55000,
    image: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
    category: "Cơm",
    restaurant: "Cơm Tấm Sài Gòn",
    tags: ["Đặc sản Sài Gòn", "Sườn nướng"],
  },
  {
    id: "7",
    name: "Phở Chay",
    description: "Phở chay với nước dùng thanh ngọt từ rau củ và nấm thơm ngon",
    price: 55000,
    image: "https://images.unsplash.com/photo-1701480253822-1842236c9a97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcGhvJTIwbm9vZGxlJTIwc291cHxlbnwxfHx8fDE3NjI0MDY1OTB8MA&ixlib=rb-4.1.0&q=80&w=1080",
    category: "Món chay",
    restaurant: "Nhà Hàng Chay Sen Việt",
    tags: ["Chay", "Healthy", "Bổ dưỡng"],
  },
  {
    id: "8",
    name: "Cà Phê Sữa Đá",
    description: "Cà phê phin truyền thống kết hợp với sữa đặc ngọt ngào",
    price: 25000,
    image: "https://images.unsplash.com/photo-1664515725366-e8328e9dc834?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwY29mZmVlfGVufDF8fHx8MTc2MjM4MjU0OXww&ixlib=rb-4.1.0&q=80&w=1080",
    category: "Đồ uống",
    restaurant: "Nhiều nhà hàng",
    tags: ["Cà phê", "Truyền thống", "Mát lạnh"],
  },
];

const categories = ["Tất cả", "Phở & Bún", "Bánh mì", "Khai vị", "Hải sản", "Cơm", "Món chay", "Đồ uống"];

export function MenuPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("Tất cả");

  const filteredItems = allMenuItems.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesCategory = selectedCategory === "Tất cả" || item.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-app relative">
      <ScrollArea className="h-app">
        <div className="max-w-7xl mx-auto p-4 md:p-6 pt-20 space-y-6">
          {/* Header */}
          <div className="text-center space-y-3">
            <div className="flex justify-center mb-4">
              <div
                className="p-6 rounded-full bg-gradient-to-br from-pink-400 via-rose-400 to-fuchsia-400 shadow-2xl animate-pulse border-4 border-pink-200"
                style={{
                  animationDuration: "2s",
                  boxShadow: "0 0 50px rgba(255,182,193,0.8), inset 0 0 25px rgba(255,255,255,0.5)",
                }}
              >
                <ChefHat className="h-16 w-16 text-white drop-shadow-[0_0_12px_rgba(255,255,255,0.9)]" />
              </div>
            </div>
            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
              🍽️ Thực đơn tổng hợp
            </h1>
            <p className="text-pink-700">Khám phá tất cả các món ăn từ các nhà hàng của chúng tôi</p>
          </div>

          {/* Search */}
          <div className="relative max-w-2xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-pink-400" />
            <Input
              type="text"
              placeholder="Tìm kiếm món ăn..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 bg-white/90 backdrop-blur-lg border-2 border-pink-200 focus:border-pink-400 rounded-2xl py-6 shadow-lg"
              style={{ boxShadow: "0 0 20px rgba(255,182,193,0.3)" }}
            />
          </div>

          {/* Category Tabs */}
          <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="w-full">
            <TabsList className="bg-pink-200/50 backdrop-blur-md rounded-2xl p-1 mb-6 flex-wrap h-auto justify-start">
              {categories.map((category) => (
                <TabsTrigger
                  key={category}
                  value={category}
                  className="data-[state=active]:bg-white data-[state=active]:text-pink-700 rounded-xl"
                >
                  {category}
                </TabsTrigger>
              ))}
            </TabsList>

            {categories.map((category) => (
              <TabsContent key={category} value={category}>
                <div className="mb-4 text-pink-700">
                  Tìm thấy <span>{filteredItems.length}</span> món ăn
                </div>

                {filteredItems.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredItems.map((item) => (
                      <Card
                        key={item.id}
                        className="group overflow-hidden bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 hover:border-pink-300 rounded-3xl shadow-lg hover:shadow-2xl transition-all"
                        style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
                      >
                        <div className="relative h-48 overflow-hidden">
                          <ImageWithFallback
                            src={item.image}
                            alt={item.name}
                            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                          />
                          <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-sm px-3 py-1 rounded-full shadow-lg border border-pink-200">
                            <span className="text-pink-600">{item.price.toLocaleString("vi-VN")}đ</span>
                          </div>
                        </div>

                        <div className="p-5 space-y-3">
                          <div>
                            <h3 className="text-gray-900 mb-1">{item.name}</h3>
                            <p className="text-sm text-pink-600">{item.restaurant}</p>
                          </div>

                          <p className="text-sm text-gray-600 line-clamp-2">{item.description}</p>

                          <div className="flex flex-wrap gap-2">
                            {item.tags.map((tag, idx) => (
                              <Badge
                                key={idx}
                                variant="secondary"
                                className="bg-gradient-to-r from-pink-200 to-rose-200 text-pink-700 border-pink-300 rounded-full text-xs"
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-pink-600 text-lg">Không tìm thấy món ăn phù hợp</p>
                    <p className="text-pink-500 mt-2">Thử tìm kiếm với từ khóa khác</p>
                  </div>
                )}
              </TabsContent>
            ))}
          </Tabs>
        </div>
      </ScrollArea>
    </div>
  );
}
