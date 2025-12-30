import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Separator } from "../../components/ui/separator";
import { ScrollArea } from "../../components/ui/scroll-area";
import { ImageWithFallback } from "../../components/figma/ImageWithFallback";
import { RestaurantCard } from "../Restaurants/RestaurantCard";
import { fetchRestaurantsPage, type Restaurant } from "../../services/api";
import { ArrowRight, BadgeCheck, MapPin, Sparkles, Star, UtensilsCrossed } from "lucide-react";

interface HomePageProps {
  onNavigateToRestaurants: () => void;
  onNavigateToChatbot: () => void;
}

const highlightTags = ["Ẩm thực địa phương", "Trải nghiệm doanh nghiệp", "Dữ liệu tin cậy", "Tư vấn AI"];

const featureHighlights = [
  {
    title: "Danh sách nhà hàng chọn lọc",
    description: "Xếp hạng dựa trên dữ liệu thực tế, cập nhật liên tục theo đánh giá cộng đồng.",
    icon: BadgeCheck,
  },
  {
    title: "Gợi ý đúng nhu cầu",
    description: "Bộ lọc chuyên sâu theo khu vực, ngân sách và phong cách ẩm thực.",
    icon: Sparkles,
  },
  {
    title: "Bản đồ & vị trí rõ ràng",
    description: "Theo dõi địa điểm, thời gian mở cửa và các điểm nổi bật nhanh chóng.",
    icon: MapPin,
  },
];

export function HomePage({ onNavigateToRestaurants, onNavigateToChatbot }: HomePageProps) {
  const [topRestaurants, setTopRestaurants] = useState<Restaurant[]>([]);
  const [totalRestaurants, setTotalRestaurants] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    fetchRestaurantsPage({ page: 1, limit: 6, sort_by: "rating", sort_order: "desc" })
      .then((result) => {
        if (!active) return;
        setTopRestaurants(result.restaurants);
        setTotalRestaurants(result.pagination?.total ?? result.restaurants.length);
      })
      .catch(() => {
        if (!active) return;
        setTopRestaurants([]);
        setTotalRestaurants(0);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const averageRating = useMemo(() => {
    if (!topRestaurants.length) return "4.8";
    const total = topRestaurants.reduce((sum, item) => sum + (item.rating || 0), 0);
    return (total / topRestaurants.length).toFixed(1);
  }, [topRestaurants]);

  return (
    <div className="min-h-dvh">
      <ScrollArea className="h-dvh">
        <div className="max-w-7xl mx-auto p-4 md:p-8 pb-24 space-y-10">
          <section className="relative overflow-hidden rounded-3xl border bg-card p-6 md:p-10 shadow-sm">
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute -top-24 right-0 h-56 w-56 rounded-full bg-primary/15 blur-3xl" />
              <div className="absolute -bottom-24 left-0 h-56 w-56 rounded-full bg-highlight/15 blur-3xl" />
            </div>
            <div className="relative grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
              <div className="space-y-6">
                <div className="inline-flex items-center gap-2 rounded-full border bg-muted/60 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  <UtensilsCrossed className="h-4 w-4" />
                  Smart Travel System
                </div>
                <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight">
                  Khám phá ẩm thực Việt Nam theo chuẩn doanh nghiệp
                </h1>
                <p className="text-muted-foreground text-base sm:text-lg max-w-xl">
                  Tổng hợp dữ liệu nhà hàng, đánh giá chuyên sâu và công cụ tư vấn thông minh để
                  bạn chọn điểm đến phù hợp nhất trong mọi hành trình.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button onClick={onNavigateToRestaurants} className="h-11 px-6 rounded-lg">
                    Khám phá nhà hàng
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" onClick={onNavigateToChatbot} className="h-11 px-6 rounded-lg">
                    Hỏi AI ngay
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {highlightTags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="rounded-full">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-3">
                  <ImageWithFallback
                    src="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80"
                    alt="Không gian nhà hàng"
                    className="h-44 w-full rounded-2xl object-cover"
                    loading="lazy"
                    decoding="async"
                  />
                  <ImageWithFallback
                    src="https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80"
                    alt="Món ăn Việt Nam"
                    className="h-44 w-full rounded-2xl object-cover"
                    loading="lazy"
                    decoding="async"
                  />
                </div>
                <ImageWithFallback
                  src="https://images.unsplash.com/photo-1526318896980-cf78c088247c?auto=format&fit=crop&w=800&q=80"
                  alt="Trải nghiệm ẩm thực"
                  className="h-full min-h-[290px] w-full rounded-2xl object-cover"
                  loading="lazy"
                  decoding="async"
                />
              </div>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-3">
            <Card className="rounded-2xl border bg-card p-5 shadow-sm">
              <div className="text-xs uppercase text-muted-foreground">Nhà hàng</div>
              <div className="mt-2 text-2xl font-semibold">{totalRestaurants}</div>
              <div className="mt-1 text-sm text-muted-foreground">Địa điểm đã được tổng hợp</div>
            </Card>
            <Card className="rounded-2xl border bg-card p-5 shadow-sm">
              <div className="text-xs uppercase text-muted-foreground">Đánh giá trung bình</div>
              <div className="mt-2 flex items-center gap-2 text-2xl font-semibold">
                <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                {averageRating}
              </div>
              <div className="mt-1 text-sm text-muted-foreground">Từ nhóm nhà hàng nổi bật</div>
            </Card>
            <Card className="rounded-2xl border bg-card p-5 shadow-sm">
              <div className="text-xs uppercase text-muted-foreground">Tư vấn</div>
              <div className="mt-2 text-2xl font-semibold">24/7</div>
              <div className="mt-1 text-sm text-muted-foreground">AI hỗ trợ ngay lập tức</div>
            </Card>
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            {featureHighlights.map((feature) => (
              <Card key={feature.title} className="rounded-2xl border bg-card p-5 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <feature.icon className="h-5 w-5" />
                  </div>
                  <div className="text-base font-semibold">{feature.title}</div>
                </div>
                <p className="mt-3 text-sm text-muted-foreground">{feature.description}</p>
              </Card>
            ))}
          </section>

          <section className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-2xl font-semibold tracking-tight">Nhà hàng nổi bật</h2>
                <p className="text-sm text-muted-foreground">
                  Tuyển chọn từ những địa điểm được đánh giá cao nhất.
                </p>
              </div>
              <Button variant="outline" onClick={onNavigateToRestaurants} className="rounded-lg">
                Xem tất cả
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
            <Separator />

            {isLoading ? (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 6 }).map((_, idx) => (
                  <Card key={idx} className="h-64 rounded-2xl border bg-muted/20 animate-pulse" />
                ))}
              </div>
            ) : topRestaurants.length === 0 ? (
              <Card className="rounded-2xl border border-dashed bg-muted/10 p-6 text-sm text-muted-foreground">
                Chưa tải được danh sách nhà hàng nổi bật. Vui lòng thử lại sau.
              </Card>
            ) : (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {topRestaurants.map((restaurant) => (
                  <RestaurantCard
                    key={restaurant.id}
                    id={restaurant.id}
                    name={restaurant.name}
                    image={restaurant.image}
                    cuisine={restaurant.cuisine}
                    rating={restaurant.rating}
                    reviewCount={restaurant.reviewCount}
                    priceLevel={restaurant.priceLevel}
                    distance={restaurant.distance}
                    openTime={restaurant.openTime}
                    specialty={restaurant.specialty}
                    googleMapsUrl={restaurant.googleMapsUrl}
                    onClick={() => onNavigateToRestaurants()}
                  />
                ))}
              </div>
            )}
          </section>

          <section className="rounded-3xl border bg-muted/20 p-6 md:p-10">
            <div className="grid gap-6 md:grid-cols-[1.2fr_0.8fr] md:items-center">
              <div className="space-y-4">
                <h3 className="text-2xl font-semibold tracking-tight">Sẵn sàng lên lịch khám phá?</h3>
                <p className="text-sm text-muted-foreground">
                  Tận dụng Smart Travel để lên kế hoạch ẩm thực nhanh, chính xác và phù hợp với ngân sách của bạn.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button onClick={onNavigateToRestaurants} className="rounded-lg">
                    Bắt đầu ngay
                  </Button>
                  <Button variant="outline" onClick={onNavigateToChatbot} className="rounded-lg">
                    Nhờ AI gợi ý
                  </Button>
                </div>
              </div>
              <div className="rounded-2xl border bg-background p-5">
                <div className="text-xs uppercase text-muted-foreground">Khuyến nghị</div>
                <div className="mt-2 text-base font-semibold">Đề xuất theo vị trí & sở thích</div>
                <p className="mt-2 text-sm text-muted-foreground">
                  Nhập khu vực, mức giá và phong cách món ăn để nhận danh sách phù hợp nhất.
                </p>
              </div>
            </div>
          </section>
        </div>
      </ScrollArea>
    </div>
  );
}
