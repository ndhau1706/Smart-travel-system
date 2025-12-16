import { useState, useEffect } from "react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Card } from "../../components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
import { Input } from "../../components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { ScrollArea } from "../../components/ui/scroll-area";
import { Textarea } from "../../components/ui/textarea";
import {
  ArrowLeft,
  Star,
  MapPin,
  Clock,
  Phone,
  DollarSign,
  User,
  MessageSquare,
  ThumbsUp,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Plus,
  Pencil,
  Trash2,
} from "lucide-react";
import { ImageWithFallback } from "../../components/figma/ImageWithFallback";
import { toast } from "sonner";
import {
  ApiReview,
  createReview,
  deleteReview,
  fetchMyReviewForRestaurant,
  fetchRestaurantById,
  fetchRestaurantReviews,
  updateReview,
} from "../../services/api";
import { getAuthHeaders } from "../../services/auth";

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
  images: string[];
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
  const [reviews, setReviews] = useState<ApiReview[]>([]);
  const [loadingReviews, setLoadingReviews] = useState(true);
  const [activeTab, setActiveTab] = useState("info");
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewTitle, setReviewTitle] = useState("");
  const [reviewContent, setReviewContent] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);
  const [deletingReview, setDeletingReview] = useState(false);
  const [myReview, setMyReview] = useState<ApiReview | null>(null);
  const [loadingMyReview, setLoadingMyReview] = useState(false);
  const [displayRating, setDisplayRating] = useState(restaurant.rating);
  const [displayReviewCount, setDisplayReviewCount] = useState(restaurant.reviewCount);

  const images =
    restaurant.images && restaurant.images.length > 0
      ? restaurant.images
      : [restaurant.image];

  const categories = Array.from(new Set(restaurant.menu.map((item) => item.category)));

  useEffect(() => {
    setActiveImageIndex(0);
    setReviewDialogOpen(false);
    setReviewRating(5);
    setReviewTitle("");
    setReviewContent("");
    setMyReview(null);
    setDisplayRating(restaurant.rating);
    setDisplayReviewCount(restaurant.reviewCount);
  }, [restaurant.id]);

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

  const getSentimentMeta = (score: number) => {
    if (score >= 70) {
      return { label: "Tích cực", className: "bg-green-100 text-green-700 border-green-200" };
    }
    if (score >= 35) {
      return { label: "Trung lập", className: "bg-yellow-100 text-yellow-800 border-yellow-200" };
    }
    return { label: "Tiêu cực", className: "bg-red-100 text-red-700 border-red-200" };
  };

  const isAuthenticated = Boolean((getAuthHeaders() as Record<string, string>).Authorization);

  const resetReviewForm = () => {
    setReviewRating(5);
    setReviewTitle("");
    setReviewContent("");
  };

  const loadMyReview = async (): Promise<ApiReview | null> => {
    const auth = getAuthHeaders() as Record<string, string>;
    if (!auth.Authorization) {
      setMyReview(null);
      return null;
    }

    setLoadingMyReview(true);
    try {
      const mine = await fetchMyReviewForRestaurant(restaurant.id);
      setMyReview(mine);
      return mine;
    } catch {
      setMyReview(null);
      return null;
    } finally {
      setLoadingMyReview(false);
    }
  };

  useEffect(() => {
    // Avoid calling authenticated endpoints on page load to prevent 401 noise when the user is not logged in.
    // We'll load the user's review only when they open the review dialog.
    return undefined;
  }, [restaurant.id]);

  const openReviewDialog = async () => {
    const auth = getAuthHeaders() as Record<string, string>;
    if (!auth.Authorization) {
      toast.error("Vui lòng đăng nhập để viết đánh giá");
      window.dispatchEvent(new Event("auth:open"));
      return;
    }

    const mine = await loadMyReview();
    if (mine) {
      setReviewRating(mine.rating || 5);
      setReviewTitle(mine.title || "");
      setReviewContent(mine.content || "");
    } else {
      resetReviewForm();
    }

    setReviewDialogOpen(true);
  };

  const submitReview = async () => {
    const trimmed = reviewContent.trim();
    if (!trimmed || trimmed.length < 10) {
      toast.error("Nội dung đánh giá phải có ít nhất 10 ký tự");
      return;
    }

    setSubmittingReview(true);
    try {
      const title = reviewTitle.trim() ? reviewTitle.trim() : undefined;
      let saved: ApiReview;

      if (myReview?.id) {
        saved = await updateReview(myReview.id, {
          rating: reviewRating,
          title: title ?? null,
          content: trimmed,
          images: [],
        });

        setReviews((prev) =>
          prev.map((r) => (r.id === saved.id ? { ...r, ...saved } : r)),
        );
        setMyReview((prev) => ({ ...(prev || {}), ...saved }));
        toast.success("Cập nhật đánh giá thành công");
      } else {
        saved = await createReview({
          restaurant_id: restaurant.id,
          rating: reviewRating,
          title,
          content: trimmed,
          images: [],
        });

        setReviews((prev) => {
          const next = [saved, ...prev];
          const seen = new Set<string>();
          return next.filter((r) => {
            if (!r?.id) return false;
            if (seen.has(r.id)) return false;
            seen.add(r.id);
            return true;
          });
        });
        setMyReview(saved);
        toast.success("Gửi đánh giá thành công");
      }

      const refreshed = await fetchRestaurantById(restaurant.id);
      if (refreshed) {
        setDisplayRating(refreshed.rating);
        setDisplayReviewCount(refreshed.reviewCount);
      } else {
        if (!myReview?.id) setDisplayReviewCount((c) => c + 1);
      }
      setReviewDialogOpen(false);
      resetReviewForm();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Gửi đánh giá thất bại";
      if (!myReview?.id && typeof message === "string" && message.includes("đã đánh giá")) {
        await loadMyReview();
      }
      toast.error(message);
    } finally {
      setSubmittingReview(false);
    }
  };

  const removeMyReview = async () => {
    if (!myReview?.id) return;
    if (!confirm("Bạn có chắc muốn xóa đánh giá này?")) return;

    setDeletingReview(true);
    try {
      await deleteReview(myReview.id);
      setReviews((prev) => prev.filter((r) => r.id !== myReview.id));
      setMyReview(null);

      const refreshed = await fetchRestaurantById(restaurant.id);
      if (refreshed) {
        setDisplayRating(refreshed.rating);
        setDisplayReviewCount(refreshed.reviewCount);
      } else {
        setDisplayReviewCount((c) => Math.max(0, c - 1));
      }

      toast.success("Xóa đánh giá thành công");
      setReviewDialogOpen(false);
      resetReviewForm();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Xóa đánh giá thất bại");
    } finally {
      setDeletingReview(false);
    }
  };

  return (
    <div className="min-h-app relative">
      <ScrollArea className="h-app">
        <div className="max-w-5xl mx-auto p-4 md:p-6 space-y-6">
          {/* Back Button */}
          <Button
            onClick={onBack}
            variant="outline"
            className="ml-12 lg:ml-0 bg-white/80 backdrop-blur-lg border-2 border-pink-200 hover:border-pink-300 rounded-2xl shadow-lg"
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
            </div>
          </Card>

          {/* Reviews Section */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-xl p-4 sm:p-6"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
                <div className="flex items-center gap-2 min-w-0">
                  <MessageSquare className="h-6 w-6 text-pink-500" />
                  <h2 className="text-pink-800 text-xl sm:text-2xl">Đánh giá ({displayReviewCount})</h2>
                </div>
                <div className="flex flex-wrap items-center gap-2 justify-start sm:justify-end">
                  <Button
                    onClick={() => void openReviewDialog()}
                    variant="outline"
                    className="bg-white/70 hover:bg-white/90 backdrop-blur-md border-2 border-pink-200 text-pink-700 rounded-full shadow-md"
                    disabled={loadingMyReview}
                  >
                    {myReview?.id ? (
                      <>
                        <Pencil className="h-4 w-4 mr-2" />
                        Sửa đánh giá
                      </>
                    ) : (
                      <>
                        <Plus className="h-4 w-4 mr-2" />
                        Viết đánh giá
                      </>
                    )}
                  </Button>

                  {myReview?.id && (
                    <Button
                      onClick={() => void removeMyReview()}
                      variant="outline"
                      className="bg-white/70 hover:bg-white/90 backdrop-blur-md border-2 border-red-200 text-red-600 rounded-full shadow-md"
                      disabled={deletingReview || submittingReview}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Xóa
                    </Button>
                  )}

                  <div className="flex items-center gap-2 bg-white/60 px-3 py-1.5 rounded-full shrink-0">
                    <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                    <span className="font-semibold text-pink-800 text-lg">{displayRating.toFixed(1)}</span>
                    <span className="text-gray-600 text-sm">/ 5</span>
                </div>
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
                        <User className="h-5 w-5 text-white" />
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
                          {typeof review.sentiment_score === "number" && (
                            <Badge
                              variant="secondary"
                              className={`rounded-full border ${getSentimentMeta(review.sentiment_score).className}`}
                              title="Điểm cảm xúc (TextBlob + dịch sang English)"
                            >
                              {getSentimentMeta(review.sentiment_score).label} • {review.sentiment_score}/100
                            </Badge>
                          )}
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
                            <p className="text-sm text-gray-700">
                              {typeof review.reply === "string" ? review.reply : review.reply.content}
                            </p>
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

      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent className="sm:max-w-[560px] bg-gradient-to-br from-pink-50 via-purple-50 to-fuchsia-50 border-2 border-pink-300 shadow-2xl rounded-3xl">
          <DialogHeader>
            <DialogTitle className="text-pink-800">
              {myReview?.id ? "Sửa đánh giá" : "Viết đánh giá"}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-pink-700">Xếp hạng</p>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setReviewRating(star)}
                    className="rounded-md p-1 hover:bg-pink-100 transition"
                    aria-label={`Chọn ${star} sao`}
                  >
                    <Star
                      className={`h-7 w-7 ${
                        star <= reviewRating
                          ? "fill-yellow-400 text-yellow-400"
                          : "fill-gray-200 text-gray-200"
                      }`}
                    />
                  </button>
                ))}
                <span className="text-sm text-gray-600 ml-2">{reviewRating}/5</span>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm text-pink-700">Tiêu đề (tùy chọn)</p>
              <Input
                value={reviewTitle}
                onChange={(e) => setReviewTitle(e.target.value)}
                placeholder="Ví dụ: Món ăn ngon, phục vụ nhiệt tình..."
                className="bg-white/90 border-2 border-pink-200 focus:border-pink-400 rounded-2xl"
              />
            </div>

            <div className="space-y-2">
              <p className="text-sm text-pink-700">Nội dung</p>
              <Textarea
                value={reviewContent}
                onChange={(e) => setReviewContent(e.target.value)}
                placeholder="Chia sẻ trải nghiệm của bạn... (ít nhất 10 ký tự)"
                className="min-h-[140px] bg-white/90 border-2 border-pink-200 focus:border-pink-400 rounded-2xl"
              />
              <p className="text-xs text-gray-500">
                Đánh giá sẽ được chấm sentiment (0-100) và hiển thị màu xanh/vàng/đỏ.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              {myReview?.id && (
                <Button
                  type="button"
                  variant="outline"
                  className="border-red-200 text-red-600 hover:bg-red-50 rounded-2xl mr-auto"
                  onClick={() => void removeMyReview()}
                  disabled={submittingReview || deletingReview}
                >
                  <Trash2 className="h-4 w-4" />
                  Xóa
                </Button>
              )}
              <Button
                type="button"
                variant="ghost"
                className="text-pink-700 hover:bg-pink-100 rounded-2xl"
                onClick={() => setReviewDialogOpen(false)}
                disabled={submittingReview || deletingReview}
              >
                Hủy
              </Button>
              <Button
                type="button"
                className="bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl shadow-lg"
                onClick={submitReview}
                disabled={submittingReview || deletingReview}
              >
                {submittingReview ? "Đang lưu..." : myReview?.id ? "Lưu thay đổi" : "Gửi đánh giá"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
