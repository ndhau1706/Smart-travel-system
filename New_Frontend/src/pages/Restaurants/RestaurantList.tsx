import { useMemo } from "react";
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
import type { Restaurant } from "../../services/api";

interface RestaurantListProps {
  restaurants: Restaurant[];
  onSelectRestaurant: (restaurant: Restaurant) => void;
  isLoading?: boolean;
  searchQuery: string;
  onSearchQueryChange: (value: string) => void;
  selectedPrice: number;
  onPriceChange: (value: number) => void;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalResults: number;
}

const priceFilters = [
  { label: "Tất cả", value: 0 },
  { label: "Bình dân", value: 1 },
  { label: "Trung cấp", value: 2 },
  { label: "Cao cấp", value: 3 },
];

export function RestaurantList({
  restaurants,
  onSelectRestaurant,
  isLoading = false,
  searchQuery,
  onSearchQueryChange,
  selectedPrice,
  onPriceChange,
  currentPage,
  totalPages,
  onPageChange,
  totalResults,
}: RestaurantListProps) {
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

  const hasActiveFilters = selectedPrice !== 0 || searchQuery !== "";

  const clearFilters = () => {
    onPriceChange(0);
    onSearchQueryChange("");
    onPageChange(1);
  };

  const prevDisabled = currentPage <= 1;
  const nextDisabled = currentPage >= totalPages;

  return (
    <div className="min-h-dvh">
      <ScrollArea className="h-dvh">
        <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8">
          {/* Header */}
          <div className="text-center space-y-3 pt-6">
            <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight">Nhà hàng</h1>
            <p className="text-muted-foreground text-base sm:text-lg max-w-3xl mx-auto">
              Trải nghiệm ẩm thực chuẩn "gu" với sự thấu hiểu từ Trí tuệ Nhân tạo và Dữ liệu xác thực.
            </p>
          </div>

          {/* Search and Filters */}
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Tìm kiếm nhà hàng, món ăn..."
                value={searchQuery}
                onChange={(e) => onSearchQueryChange(e.target.value)}
                className="pl-10 rounded-lg"
              />
            </div>

            {/* Filter Section */}
            <div className="rounded-xl border bg-card p-4 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
                <div className="flex items-center gap-2">
                  <Filter className="h-5 w-5 text-muted-foreground" />
                  <span className="font-medium">Lọc theo</span>
                </div>
                {hasActiveFilters && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearFilters}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-4 w-4" />
                    Xóa bộ lọc
                  </Button>
                )}
              </div>

              {/* Price Filters */}
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Mức giá</p>
                <div className="flex flex-wrap gap-2">
                  {priceFilters.map((price) => (
                    <Badge
                      key={price.value}
                      onClick={() => onPriceChange(price.value)}
                      variant={selectedPrice === price.value ? "default" : "secondary"}
                      className="cursor-pointer rounded-full"
                    >
                      {price.label}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Results Count */}
          <div className="text-sm text-muted-foreground">
            {isLoading ? "Đang tải..." : <>Tìm thấy <span className="font-medium text-foreground">{totalResults}</span> nhà hàng</>}
          </div>

          {/* Restaurant Grid */}
          {isLoading && restaurants.length === 0 ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-muted border-t-primary" />
              <p className="text-muted-foreground mt-4">Đang tải danh sách nhà hàng...</p>
            </div>
          ) : restaurants.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-6">
              {restaurants.map((restaurant) => (
                <RestaurantCard
                  key={restaurant.id}
                  {...restaurant}
                  onClick={() => onSelectRestaurant(restaurant)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-lg font-medium">Không tìm thấy nhà hàng phù hợp</p>
              <p className="text-muted-foreground">Thử điều chỉnh bộ lọc của bạn</p>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pb-8">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationLink
                      href="#"
                      aria-disabled={prevDisabled}
                      className={prevDisabled ? "pointer-events-none opacity-50" : ""}
                      onClick={(e) => {
                        e.preventDefault();
                        if (!prevDisabled) onPageChange(currentPage - 1);
                      }}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </PaginationLink>
                  </PaginationItem>

                  {pageItems.map((item, idx) =>
                    item === "ellipsis" ? (
                      <PaginationItem key={`ellipsis-${idx}`}>
                        <PaginationEllipsis />
                      </PaginationItem>
                    ) : (
                      <PaginationItem key={item}>
                        <PaginationLink
                          href="#"
                          size="sm"
                          isActive={item === currentPage}
                          onClick={(e) => {
                            e.preventDefault();
                            onPageChange(item);
                          }}
                        >
                          {item}
                        </PaginationLink>
                      </PaginationItem>
                    ),
                  )}

                  <PaginationItem>
                    <PaginationLink
                      href="#"
                      aria-disabled={nextDisabled}
                      className={nextDisabled ? "pointer-events-none opacity-50" : ""}
                      onClick={(e) => {
                        e.preventDefault();
                        if (!nextDisabled) onPageChange(currentPage + 1);
                      }}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </PaginationLink>
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
