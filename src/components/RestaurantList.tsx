import { useState } from "react";
import { RestaurantCard } from "./RestaurantCard";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { Search, Filter, X } from "lucide-react";

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
  menu: any[];
}

interface RestaurantListProps {
  restaurants: Restaurant[];
  onSelectRestaurant: (restaurant: Restaurant) => void;
}

const cuisineFilters = [
  "Tất cả",
  "Phở",
  "Bánh mì",
  "Bún",
  "Cơm",
  "Hải sản",
  "Lẩu",
  "Đồ nướng",
  "Chay",
];

const priceFilters = [
  { label: "Tất cả", value: 0 },
  { label: "$", value: 1 },
  { label: "$$", value: 2 },
  { label: "$$$", value: 3 },
];

export function RestaurantList({ restaurants, onSelectRestaurant }: RestaurantListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCuisine, setSelectedCuisine] = useState("Tất cả");
  const [selectedPrice, setSelectedPrice] = useState(0);

  const filteredRestaurants = restaurants.filter((restaurant) => {
    const matchesSearch =
      restaurant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      restaurant.cuisine.toLowerCase().includes(searchQuery.toLowerCase()) ||
      restaurant.specialty.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesCuisine =
      selectedCuisine === "Tất cả" ||
      restaurant.cuisine.includes(selectedCuisine) ||
      restaurant.specialty.some((s) => s.includes(selectedCuisine));

    const matchesPrice = selectedPrice === 0 || restaurant.priceLevel === selectedPrice;

    return matchesSearch && matchesCuisine && matchesPrice;
  });

  const hasActiveFilters = selectedCuisine !== "Tất cả" || selectedPrice !== 0 || searchQuery !== "";

  const clearFilters = () => {
    setSelectedCuisine("Tất cả");
    setSelectedPrice(0);
    setSearchQuery("");
  };

  return (
    <div className="min-h-screen relative">
      <ScrollArea className="h-screen">
        <div className="max-w-7xl mx-auto p-4 md:p-6 space-y-6">
          {/* Header */}
          <div className="text-center space-y-3">
            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
              🍜 Khám phá Ẩm thực Việt Nam 🥢
            </h1>
            <p className="text-pink-700">
              Tìm kiếm và đặt bàn tại các nhà hàng Việt Nam tốt nhất
            </p>
          </div>

          {/* Search and Filters */}
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-pink-400" />
              <Input
                type="text"
                placeholder="Tìm kiếm nhà hàng, món ăn..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-12 bg-white/90 backdrop-blur-lg border-2 border-pink-200 focus:border-pink-400 rounded-2xl py-6 shadow-lg"
                style={{ boxShadow: "0 0 20px rgba(255,182,193,0.3)" }}
              />
            </div>

            {/* Filter Section */}
            <div
              className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-4 shadow-lg"
              style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Filter className="h-5 w-5 text-pink-600" />
                  <span className="text-pink-800">Lọc theo</span>
                </div>
                {hasActiveFilters && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearFilters}
                    className="text-pink-600 hover:text-pink-700 hover:bg-pink-200/50"
                  >
                    <X className="h-4 w-4 mr-1" />
                    Xóa bộ lọc
                  </Button>
                )}
              </div>

              {/* Cuisine Filters */}
              <div className="space-y-2">
                <p className="text-sm text-pink-700">Loại món ăn</p>
                <div className="flex flex-wrap gap-2">
                  {cuisineFilters.map((cuisine) => (
                    <Badge
                      key={cuisine}
                      onClick={() => setSelectedCuisine(cuisine)}
                      className={`cursor-pointer transition-all rounded-full ${
                        selectedCuisine === cuisine
                          ? "bg-gradient-to-r from-pink-400 to-rose-400 text-white border-pink-500"
                          : "bg-white/80 text-pink-700 border-pink-300 hover:bg-pink-200/50"
                      }`}
                      style={
                        selectedCuisine === cuisine
                          ? { boxShadow: "0 0 15px rgba(255,182,193,0.5)" }
                          : undefined
                      }
                    >
                      {cuisine}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Price Filters */}
              <div className="space-y-2 mt-4">
                <p className="text-sm text-pink-700">Mức giá</p>
                <div className="flex flex-wrap gap-2">
                  {priceFilters.map((price) => (
                    <Badge
                      key={price.value}
                      onClick={() => setSelectedPrice(price.value)}
                      className={`cursor-pointer transition-all rounded-full ${
                        selectedPrice === price.value
                          ? "bg-gradient-to-r from-pink-400 to-rose-400 text-white border-pink-500"
                          : "bg-white/80 text-pink-700 border-pink-300 hover:bg-pink-200/50"
                      }`}
                      style={
                        selectedPrice === price.value
                          ? { boxShadow: "0 0 15px rgba(255,182,193,0.5)" }
                          : undefined
                      }
                    >
                      {price.label}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Results Count */}
          <div className="text-pink-700">
            Tìm thấy <span>{filteredRestaurants.length}</span> nhà hàng
          </div>

          {/* Restaurant Grid */}
          {filteredRestaurants.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-6">
              {filteredRestaurants.map((restaurant) => (
                <RestaurantCard
                  key={restaurant.id}
                  {...restaurant}
                  onClick={() => onSelectRestaurant(restaurant)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-pink-600 text-lg">Không tìm thấy nhà hàng phù hợp</p>
              <p className="text-pink-500 mt-2">Thử điều chỉnh bộ lọc của bạn</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
