import { useEffect, useMemo, useState } from "react";
import { RestaurantCard } from "./RestaurantCard";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
} from "../../components/ui/pagination";
import { ScrollArea } from "../../components/ui/scroll-area";
import { Search, Filter, X, ChevronLeft, ChevronRight } from "lucide-react";

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
  isLoading?: boolean;
}

const cuisineFilters = [
  { label: "Tất cả", value: "" },
  { label: "Lẩu", value: "lẩu" },
  { label: "Hải sản", value: "hải sản" },
  { label: "Nướng", value: "nướng" },
  { label: "Cơm", value: "cơm" },
  { label: "Buffet", value: "buffet" },
  { label: "Món nước", value: "món nước" },
  { label: "Món chiên", value: "món chiên" },
  { label: "Đồ chay", value: "Đồ chay" },
  { label: "Cafe", value: "cafe" },
];

const priceFilters = [
  { label: "Tất cả", value: 0 },
  { label: "$", value: 1 },
  { label: "$$", value: 2 },
  { label: "$$$", value: 3 },
];

export function RestaurantList({ restaurants, onSelectRestaurant, isLoading = false }: RestaurantListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCuisine, setSelectedCuisine] = useState("");
  const [selectedPrice, setSelectedPrice] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);

  const filteredRestaurants = restaurants.filter((restaurant) => {
    const searchLower = searchQuery.toLowerCase();
    const matchesSearch = searchQuery === "" ||
      restaurant.name.toLowerCase().includes(searchLower) ||
      restaurant.cuisine.toLowerCase().includes(searchLower) ||
      restaurant.specialty.some((s) => s.toLowerCase().includes(searchLower));

    const matchesCuisine = selectedCuisine === "" ||
      restaurant.specialty.some((s) => s.toLowerCase().includes(selectedCuisine.toLowerCase()));

    const matchesPrice = selectedPrice === 0 || restaurant.priceLevel === selectedPrice;

    return matchesSearch && matchesCuisine && matchesPrice;
  });

  const pageSize = 24;
  const totalPages = Math.max(1, Math.ceil(filteredRestaurants.length / pageSize));

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedCuisine, selectedPrice, restaurants.length]);

  useEffect(() => {
    setCurrentPage((p) => Math.min(Math.max(1, p), totalPages));
  }, [totalPages]);

  const pagedRestaurants = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRestaurants.slice(start, start + pageSize);
  }, [filteredRestaurants, currentPage]);

  const pageItems = useMemo(() => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, idx) => idx + 1);
    }

    const siblings = 1;
    const pages: Array<number | "ellipsis"> = [];
    pages.push(1);

    const start = Math.max(2, currentPage - siblings);
    const end = Math.min(totalPages - 1, currentPage + siblings);

    if (start > 2) pages.push("ellipsis");
    for (let p = start; p <= end; p += 1) pages.push(p);
    if (end < totalPages - 1) pages.push("ellipsis");

    pages.push(totalPages);
    return pages;
  }, [currentPage, totalPages]);

  const hasActiveFilters = selectedCuisine !== "" || selectedPrice !== 0 || searchQuery !== "";

  const clearFilters = () => {
    setSelectedCuisine("");
    setSelectedPrice(0);
    setSearchQuery("");
    setCurrentPage(1);
  };

  return (
    <div className="min-h-app relative">
      <ScrollArea className="h-app">
        <div className="max-w-7xl mx-auto p-4 md:p-6 space-y-6">
          {/* Header */}
          <div className="text-center space-y-3">
            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
              🍜 Khám phá Ẩm thực Việt Nam 🥢
            </h1>
            <p className="text-pink-700">
              Tìm kiếm và khám phá các nhà hàng Việt Nam tốt nhất
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
                      key={cuisine.value}
                      onClick={() => setSelectedCuisine(cuisine.value)}
                      className={`cursor-pointer transition-all rounded-full ${
                        selectedCuisine === cuisine.value
                          ? "bg-gradient-to-r from-pink-400 to-rose-400 text-white border-pink-500"
                          : "bg-white/80 text-pink-700 border-pink-300 hover:bg-pink-200/50"
                      }`}
                      style={
                        selectedCuisine === cuisine.value
                          ? { boxShadow: "0 0 15px rgba(255,182,193,0.5)" }
                          : undefined
                      }
                    >
                      {cuisine.label}
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
            {isLoading ? (
              "Đang tải..."
            ) : (
              <>
                Tìm thấy <span>{filteredRestaurants.length}</span> nhà hàng • Trang{" "}
                <span>{currentPage}</span>/<span>{totalPages}</span>
              </>
            )}
          </div>

          {/* Restaurant Grid */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-pink-300 border-t-pink-600"></div>
              <p className="text-pink-600 text-lg mt-4">Đang tải danh sách nhà hàng...</p>
            </div>
          ) : filteredRestaurants.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-6">
                {pagedRestaurants.map((restaurant) => (
                <RestaurantCard
                  key={restaurant.id}
                  {...restaurant}
                  onClick={() => onSelectRestaurant(restaurant)}
                />
              ))}
              </div>

              {totalPages > 1 && (
                <div className="pb-10">
                  <Pagination>
                    <PaginationContent className="bg-white/70 backdrop-blur-md border border-pink-200 rounded-full px-2 py-1 shadow-md">
                      <PaginationItem>
                        <PaginationLink
                          href="#"
                          aria-label="Trang trước"
                          onClick={(e) => {
                            e.preventDefault();
                            setCurrentPage((p) => Math.max(1, p - 1));
                          }}
                          className={currentPage === 1 ? "pointer-events-none opacity-50" : ""}
                        >
                          <ChevronLeft className="h-4 w-4" />
                        </PaginationLink>
                      </PaginationItem>

                      {pageItems.map((item, idx) => (
                        <PaginationItem key={`${item}-${idx}`}>
                          {item === "ellipsis" ? (
                            <PaginationEllipsis className="text-pink-500" />
                          ) : (
                            <PaginationLink
                              href="#"
                              isActive={item === currentPage}
                              onClick={(e) => {
                                e.preventDefault();
                                setCurrentPage(item);
                              }}
                              className={
                                item === currentPage
                                  ? "border-pink-300 text-pink-800"
                                  : "text-pink-700 hover:text-pink-800"
                              }
                            >
                              {item}
                            </PaginationLink>
                          )}
                        </PaginationItem>
                      ))}

                      <PaginationItem>
                        <PaginationLink
                          href="#"
                          aria-label="Trang sau"
                          onClick={(e) => {
                            e.preventDefault();
                            setCurrentPage((p) => Math.min(totalPages, p + 1));
                          }}
                          className={currentPage === totalPages ? "pointer-events-none opacity-50" : ""}
                        >
                          <ChevronRight className="h-4 w-4" />
                        </PaginationLink>
                      </PaginationItem>
                    </PaginationContent>
                  </Pagination>
                </div>
              )}
            </>
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
