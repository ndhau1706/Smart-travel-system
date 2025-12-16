import { useState, useEffect } from "react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Card } from "../../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { ScrollArea } from "../../components/ui/scroll-area";
import { BookingDialog } from "../../components/BookingDialog";
import { ArrowLeft, Star, MapPin, Clock, Phone, DollarSign, Calendar, User, MessageSquare, ThumbsUp, CheckCircle } from "lucide-react";
import { ImageWithFallback } from "../../components/figma/ImageWithFallback";
import { fetchRestaurantReviews, ApiReview } from "../../services/api";

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
  address: string;
  phone: string;
  openTime: string;
  specialty: string[];
  description: string;
  menu: MenuItem[];
}

interface RestaurantDetailProps {
  restaurant: Restaurant;
  onBack: () => void;
}

export function RestaurantDetail({ restaurant, onBack }: RestaurantDetailProps) {
  const [bookingOpen, setBookingOpen] = useState(false);
  const [reviews, setReviews] = useState<ApiReview[]>([]);
  const [loadingReviews, setLoadingReviews] = useState(true);
  const [activeTab, setActiveTab] = useState("info");

  const categories = Array.from(new Set(restaurant.menu.map((item) => item.category)));

  // Fetch reviews when component mounts
  useEffect(() => {
    const loadReviews = async () => {
      setLoadingReviews(true);
      const fetchedReviews = await fetchRestaurantReviews(restaurant.id);
      setReviews(fetchedReviews);
      setLoadingReviews(false);
    };
    loadReviews();
  }, [restaurant.id]);

  // Render star rating
  const renderStars = (rating: number) => {
    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-4 w-4 ${
              star <= rating
                ? "fill-yellow-400 text-yellow-400"
                : "fill-gray-200 text-gray-200"
            }`}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen relative">
      <ScrollArea className="h-screen">
        <div className="max-w-5xl mx-auto p-4 md:p-6 space-y-6">
          {/* Back Button */}
          <Button
            onClick={onBack}
            variant="outline"
            className="bg-white/80 backdrop-blur-lg border-2 border-pink-200 hover:border-pink-300 rounded-2xl shadow-lg font-bold"
            style={{ boxShadow: "0 0 15px rgba(255,182,193,0.3)" }}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Quay lại
          </Button>

          {/* Restaurant Header */}
          <Card
            className="overflow-hidden bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="relative h-64 md:h-80 overflow-hidden">
              <ImageWithFallback
                src={restaurant.image}
                alt={restaurant.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
              <div className="absolute bottom-6 left-6 right-6 text-white">
                <h1 className="text-white mb-2">{restaurant.name}</h1>
                <div className="flex items-center gap-4 flex-wrap">
                  <div className="flex items-center gap-1 bg-white/20 backdrop-blur-md px-3 py-1 rounded-full">
                    <Star className="h-6 w-6 fill-yellow-400 text-yellow-400" />
                    <span>{restaurant.rating}</span>
                    <span className="text-sm">({restaurant.reviewCount} đánh giá)</span>
                  </div>
                  <span className="text-sm">{restaurant.cuisine}</span>
                </div>
              </div>
            </div>

            <div className="p-4 space-y-4">
              <p className="text-gray-700">{restaurant.description}</p>

              <div className="flex flex-wrap gap-2">
                {restaurant.specialty.map((item, idx) => (
                  <Badge
                    key={idx}
                    variant="secondary"
                    className="bg-gradient-to-r from-pink-200 to-rose-200 text-pink-700 border-pink-300 rounded-full"
                  >
                    {item}
                  </Badge>
                ))}
              </div>

              <div className="flex flex-col gap-3 text-gray-700">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <MapPin className="h-6 w-6 text-pink-500" />
                  </div>
                  <span>{restaurant.address}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <Phone className="h-6 w-6 text-pink-500" />
                  </div>
                  <span>{restaurant.phone}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <Clock className="h-6 w-6 text-pink-500" />
                  </div>
                  <span>{restaurant.openTime}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <DollarSign className="h-6 w-6 text-pink-500" />
                  </div>
                  <span>{"$".repeat(restaurant.priceLevel)} - Giá trung bình</span>
                </div>
              </div>

              <Button
                onClick={() => setBookingOpen(true)}
                className="w-full bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl shadow-lg py-6"
                style={{ boxShadow: "0 0 25px rgba(255,182,193,0.5)" }}
              >
                <Calendar className="mr-2 h-6 w-6" />
                Đặt bàn ngay
              </Button>
            </div>
          </Card>

          {/* Reviews Section */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-xl p-6"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-6 w-6 text-pink-500" />
                <h2 className="text-pink-800">Đánh giá ({reviews.length})</h2>
              </div>
              <div className="flex items-center gap-2 bg-white/60 px-4 py-2 rounded-full">
                <Star className="h-6 w-6 fill-yellow-400 text-yellow-400" />
                <span className="font-semibold text-pink-800">{restaurant.rating.toFixed(1)}</span>
                <span className="text-gray-600 text-sm">/ 5</span>
              </div>
            </div>

            {loadingReviews ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pink-500"></div>
                <span className="ml-3 text-gray-600">Đang tải đánh giá...</span>
              </div>
            ) : reviews.length === 0 ? (
              <div className="text-center py-12">
                <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">Chưa có đánh giá nào cho nhà hàng này</p>
              </div>
            ) : (
              <div className="space-y-4">
                {reviews.map((review) => (
                  <Card
                    key={review.id}
                    className="bg-white/80 backdrop-blur-md border border-pink-200 rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-300 to-rose-300 flex items-center justify-center flex-shrink-0">
                        <User className="h-6 w-6 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gray-800">
                              {review.author_name || review.user_name || "Người dùng ẩn danh"}
                            </span>
                            {review.is_verified && (
                              <span title="Đã xác thực">
                                <CheckCircle className="h-4 w-4 text-green-500" />
                              </span>
                            )}
                          </div>
                          <span className="text-sm text-gray-500">{review.visit_date}</span>
                        </div>
                        
                        <div className="flex items-center gap-2 mt-1">
                          {renderStars(review.rating)}
                          <span className="text-sm text-gray-500">({review.rating}/5)</span>
                        </div>

                        {review.title && (
                          <h4 className="font-medium text-gray-800 mt-2">{review.title}</h4>
                        )}
                        
                        <p className="text-gray-700 mt-2 whitespace-pre-line">{review.content}</p>

                        {review.images && review.images.length > 0 && (
                          <div className="flex gap-2 mt-3 flex-wrap">
                            {review.images.map((img, idx) => (
                              <img
                                key={idx}
                                src={img}
                                alt={`Review image ${idx + 1}`}
                                className="w-20 h-20 object-cover rounded-lg border border-pink-200"
                              />
                            ))}
                          </div>
                        )}

                        <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                          <div className="flex items-center gap-1">
                            <ThumbsUp className="h-4 w-4" />
                            <span>{review.likes || 0} hữu ích</span>
                          </div>
                        </div>

                        {review.reply && (
                          <div className="mt-3 p-3 bg-pink-50 rounded-xl border border-pink-200">
                            <p className="text-sm font-medium text-pink-700 mb-1">Phản hồi từ nhà hàng:</p>
                            <p className="text-sm text-gray-700">{review.reply}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </Card>

          {/* Menu */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-xl p-6"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <h2 className="text-pink-800 mb-6">Thực đơn</h2>
            <Tabs defaultValue={categories[0]} className="w-full">
              <TabsList className="bg-pink-200/50 backdrop-blur-md rounded-2xl p-1 mb-6 flex-wrap h-auto">
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
                <TabsContent key={category} value={category} className="space-y-4">
                  {restaurant.menu
                    .filter((item) => item.category === category)
                    .map((item) => (
                      <Card
                        key={item.id}
                        className="flex gap-4 overflow-hidden bg-white/80 backdrop-blur-md border border-pink-200 rounded-2xl shadow-md hover:shadow-lg transition-shadow"
                      >
                        <ImageWithFallback
                          src={item.image}
                          alt={item.name}
                          className="w-24 h-24 object-cover rounded-l-2xl"
                        />
                        <div className="flex-1 p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="text-gray-900">{item.name}</h4>
                            <span className="text-pink-600">{item.price.toLocaleString("vi-VN")}đ</span>
                          </div>
                          <p className="text-sm text-gray-600">{item.description}</p>
                        </div>
                      </Card>
                    ))}
                </TabsContent>
              ))}
            </Tabs>
          </Card>
        </div>
      </ScrollArea>

      <BookingDialog
        open={bookingOpen}
        onOpenChange={setBookingOpen}
        restaurantName={restaurant.name}
      />
    </div>
  );
}
