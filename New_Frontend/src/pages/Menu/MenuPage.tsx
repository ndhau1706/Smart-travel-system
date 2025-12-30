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
    <div className="min-h-dvh">
      <ScrollArea className="h-dvh">
        <div className="max-w-7xl mx-auto p-4 md:p-8 pb-24 space-y-10">
          {/* Header */}
          <div className="text-center space-y-6 pt-10">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <ChefHat className="h-7 w-7" />
            </div>
            <div className="space-y-3">
              <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight">
                Bản đồ vị giác
              </h1>
              <p className="text-muted-foreground text-base sm:text-lg max-w-3xl mx-auto">
                Mỗi món ăn là một điểm đến thú vị.
                <br />
                Khám phá ẩm thực Việt Nam theo sở thích của bạn.
              </p>
            </div>
          </div>

          {/* Search */}
          <div className="relative max-w-2xl mx-auto w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Tìm kiếm món ăn..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-11 pl-10 rounded-lg bg-background shadow-sm"
            />
          </div>

          {/* Category Tabs */}
          <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="w-full">
            <TabsList className="mb-4 h-auto w-full flex-wrap justify-start">
              {categories.map((category) => (
                <TabsTrigger
                  key={category}
                  value={category}
                  className="data-[state=active]:text-primary"
                >
                  {category}
                </TabsTrigger>
              ))}
            </TabsList>

            {categories.map((category) => (
              <TabsContent key={category} value={category}>
                <div className="mb-4 text-sm text-muted-foreground">
                  Tìm thấy{" "}
                  <span className="font-medium text-foreground">
                    {filteredItems.length}
                  </span>{" "}
                  món ăn
                </div>

                {filteredItems.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredItems.map((item) => (
                      <Card
                        key={item.id}
                        className="group overflow-hidden rounded-xl bg-card shadow-sm hover:shadow-md transition-shadow"
                      >
                        <div className="relative h-48 overflow-hidden">
                          <ImageWithFallback
                            src={item.image}
                            alt={item.name}
                            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                          />
                          <div className="absolute top-3 right-3 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground shadow-sm">
                            {item.price.toLocaleString("vi-VN")}đ
                          </div>
                        </div>

                        <div className="p-5 space-y-3">
                          <div>
                            <h3 className="font-semibold leading-tight">{item.name}</h3>
                            <p className="text-sm text-muted-foreground">{item.restaurant}</p>
                          </div>

                          <p className="text-sm text-muted-foreground line-clamp-2">{item.description}</p>

                          <div className="flex flex-wrap gap-2">
                            {item.tags.map((tag, idx) => (
                              <Badge
                                key={idx}
                                variant="secondary"
                                className="text-xs"
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
                    <p className="text-muted-foreground text-lg">Không tìm thấy món ăn phù hợp</p>
                    <p className="text-muted-foreground mt-2">Thử tìm kiếm với từ khóa khác</p>
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
