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
  Globe,
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
import { formatPriceLevelLabel } from "../../services/restaurantFormat";
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
  website?: string;
  openTime: string;
  specialty: string[];
  description: string;
  googleMapsUrl?: string;
  menu: MenuItem[];
}

function normalizeExternalUrl(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (trimmed.startsWith("//")) return `https:${trimmed}`;
  if (/^[a-z]+:\/\//i.test(trimmed)) return trimmed;
  return `https://${trimmed}`;
}

function formatWebsiteLabel(url: string): string {
  const normalized = normalizeExternalUrl(url);
  try {
    const parsed = new URL(normalized);
    return parsed.hostname.replace(/^www\./i, "");
  } catch {
    return url;
  }
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

  const website = restaurant.website?.trim() ? restaurant.website.trim() : "";

  const categories = Array.from(new Set(restaurant.menu.map((item) => item.category)));
  const hasMultipleImages = images.length > 1;

  const showPrevImage = () => {
    if (!hasMultipleImages) return;
    setActiveImageIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  const showNextImage = () => {
    if (!hasMultipleImages) return;
    setActiveImageIndex((prev) => (prev + 1) % images.length);
  };

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
    <div className="min-h-dvh">
      <ScrollArea className="h-dvh">
        <div className="max-w-5xl mx-auto p-4 md:p-8 space-y-6">
          {/* Back Button */}
          <Button
            onClick={onBack}
            variant="outline"
            className="ml-12 lg:ml-0 rounded-lg shadow-sm"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Quay lại
          </Button>

          {/* Restaurant Header */}
          <Card
            className="overflow-hidden rounded-xl border bg-card shadow-sm"
          >
            <div className="relative h-64 md:h-80 overflow-hidden">
              <ImageWithFallback
                src={images[activeImageIndex] || restaurant.image}
                alt={restaurant.name}
                className="w-full h-full object-cover"
              />

              {hasMultipleImages && (
                <>
                  <Button
                    type="button"
                    variant="secondary"
                    size="icon"
                    className="absolute left-4 top-1/2 -translate-y-1/2 z-20 bg-background/80 backdrop-blur border shadow-sm"
                    onClick={showPrevImage}
                    aria-label="Ảnh trước"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    size="icon"
                    className="absolute right-4 top-1/2 -translate-y-1/2 z-20 bg-background/80 backdrop-blur border shadow-sm"
                    onClick={showNextImage}
                    aria-label="Ảnh tiếp theo"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </Button>
                  <div className="absolute bottom-4 right-4 z-20 rounded-full border bg-background/80 px-3 py-1 text-xs text-muted-foreground backdrop-blur">
                    <span className="font-medium text-foreground">{activeImageIndex + 1}</span>/{images.length}
                  </div>
                </>
              )}

              <div className="absolute inset-0 pointer-events-none bg-gradient-to-t from-black/60 via-transparent to-transparent" />
              <div className="absolute bottom-6 left-6 right-6 text-white">
                <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-white mb-2">{restaurant.name}</h1>
                <div className="flex items-center gap-4 flex-wrap">
                  <div className="flex items-center gap-1 rounded-full bg-black/30 px-3 py-1 text-sm backdrop-blur">
                    <Star className="h-6 w-6 fill-yellow-400 text-yellow-400" />
                    <span>{restaurant.rating}</span>
                    <span className="text-sm">({restaurant.reviewCount} đánh giá)</span>
                  </div>
                  <span className="text-sm">{restaurant.cuisine}</span>
                </div>
              </div>
            </div>

            <div className="p-4 space-y-4">
              <p className="text-muted-foreground">{restaurant.description}</p>

              <div className="flex flex-wrap gap-2">
                {restaurant.specialty.map((item, idx) => (
                  <Badge
                    key={idx}
                    variant="secondary"
                    className="rounded-full"
                  >
                    {item}
                  </Badge>
                ))}
              </div>

              <div className="flex flex-col gap-3 text-sm">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <MapPin className="h-5 w-5 text-muted-foreground" />
                  </div>
                  {restaurant.googleMapsUrl ? (
                    <a
                      href={restaurant.googleMapsUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="underline underline-offset-4 decoration-primary/40 hover:decoration-primary hover:text-primary transition-colors"
                      title="Mở Google Maps"
                    >
                      {restaurant.address}
                    </a>
                  ) : (
                    <span>{restaurant.address}</span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <Phone className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <span>{restaurant.phone}</span>
                </div>
                {website ? (
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                      <Globe className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <a
                      href={normalizeExternalUrl(website)}
                      target="_blank"
                      rel="noreferrer"
                      className="underline underline-offset-4 decoration-primary/40 hover:decoration-primary hover:text-primary transition-colors"
                      title="Mở website"
                    >
                      {formatWebsiteLabel(website)}
                    </a>
                  </div>
                ) : null}
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <Clock className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <span>{restaurant.openTime}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <DollarSign className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <span>{formatPriceLevelLabel(restaurant.priceLevel)}</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Reviews Section */}
          <Card
            className="rounded-xl border bg-card p-4 sm:p-6 shadow-sm"
          >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
                <div className="flex items-center gap-2 min-w-0">
                  <MessageSquare className="h-6 w-6 text-muted-foreground" />
                  <h2 className="text-xl sm:text-2xl font-semibold tracking-tight">Đánh giá ({displayReviewCount})</h2>
                </div>
                <div className="flex flex-wrap items-center gap-2 justify-start sm:justify-end">
                  <Button
                    onClick={() => void openReviewDialog()}
                    variant={myReview?.id ? "outline" : "default"}
                    className="rounded-lg"
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
                      variant="destructive"
                      className="rounded-lg"
                      disabled={deletingReview || submittingReview}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Xóa
                    </Button>
                  )}

                  <div className="flex items-center gap-2 rounded-full bg-secondary px-3 py-1.5 text-sm text-secondary-foreground shrink-0">
                    <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                    <span className="font-semibold text-foreground">{displayRating.toFixed(1)}</span>
                    <span className="text-muted-foreground">/ 5</span>
                  </div>
                </div>
              </div>

            {loadingReviews ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-muted border-t-primary" />
                <span className="ml-3 text-muted-foreground">Đang tải đánh giá...</span>
              </div>
            ) : reviews.length === 0 ? (
              <div className="text-center py-12">
                <MessageSquare className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
                <p className="text-muted-foreground">Chưa có đánh giá nào cho nhà hàng này</p>
              </div>
            ) : (
              <div className="space-y-4">
                {reviews.map((review) => (
                  <Card
                    key={review.id}
                    className="rounded-xl border bg-card p-4 shadow-sm"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-full bg-secondary text-secondary-foreground ring-1 ring-border flex items-center justify-center flex-shrink-0">
                        <User className="h-5 w-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-foreground">
                              {review.author_name || review.user_name || "Người dùng ẩn danh"}
                            </span>
                            {review.is_verified && (
                              <span title="Đã xác thực">
                                <CheckCircle className="h-4 w-4 text-green-500" />
                              </span>
                            )}
                          </div>
                          <span className="text-sm text-muted-foreground">{review.visit_date}</span>
                        </div>
                        
                        <div className="flex items-center gap-2 mt-1">
                          {renderStars(review.rating)}
                          <span className="text-sm text-muted-foreground">({review.rating}/5)</span>
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
                          <h4 className="font-medium text-foreground mt-2">{review.title}</h4>
                        )}
                        
                        <p className="text-foreground/90 mt-2 whitespace-pre-line">{review.content}</p>

                        {review.images && review.images.length > 0 && (
                          <div className="flex gap-2 mt-3 flex-wrap">
                            {review.images.map((img, idx) => (
                              <img
                                key={idx}
                                src={img}
                                alt={`Review image ${idx + 1}`}
                                className="w-20 h-20 object-cover rounded-lg border border-border"
                              />
                            ))}
                          </div>
                        )}

                        <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <ThumbsUp className="h-4 w-4" />
                            <span>{review.likes || 0} hữu ích</span>
                          </div>
                        </div>

                        {review.reply && (
                          <div className="mt-3 p-3 bg-muted/40 rounded-xl border border-border">
                            <p className="text-sm font-medium text-muted-foreground mb-1">Phản hồi từ nhà hàng:</p>
                            <p className="text-sm text-foreground/90">
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

          {/* Menu (hide when empty) */}
          {Array.isArray(restaurant.menu) && restaurant.menu.length > 0 && categories.length > 0 ? (
            <Card className="rounded-xl border bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold tracking-tight mb-6">Thực đơn</h2>
              <Tabs defaultValue={categories[0]} className="w-full">
                <TabsList className="w-full flex-wrap justify-start h-auto mb-6">
                  {categories.map((category) => (
                    <TabsTrigger
                      key={category}
                      value={category}
                      className="px-3"
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
                          className="flex gap-4 overflow-hidden rounded-xl border bg-card shadow-sm"
                        >
                          <ImageWithFallback
                            src={item.image}
                            alt={item.name}
                            className="w-24 h-24 object-cover rounded-l-xl"
                          />
                          <div className="flex-1 p-4">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-medium text-foreground">{item.name}</h4>
                              <span className="font-medium text-highlight">{item.price.toLocaleString("vi-VN")}đ</span>
                            </div>
                            <p className="text-sm text-muted-foreground">{item.description}</p>
                          </div>
                        </Card>
                      ))}
                  </TabsContent>
                ))}
              </Tabs>
            </Card>
          ) : null}
        </div>
      </ScrollArea>

      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent className="sm:max-w-[560px]">
          <DialogHeader>
            <DialogTitle>{myReview?.id ? "Sửa đánh giá" : "Viết đánh giá"}</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Xếp hạng</p>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setReviewRating(star)}
                    className="rounded-md p-1 hover:bg-accent transition-colors"
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
                <span className="text-sm text-muted-foreground ml-2">{reviewRating}/5</span>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Tiêu đề (tùy chọn)</p>
              <Input
                value={reviewTitle}
                onChange={(e) => setReviewTitle(e.target.value)}
                placeholder="Ví dụ: Món ăn ngon, phục vụ nhiệt tình..."
              />
            </div>

            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Nội dung</p>
              <Textarea
                value={reviewContent}
                onChange={(e) => setReviewContent(e.target.value)}
                placeholder="Chia sẻ trải nghiệm của bạn... (ít nhất 10 ký tự)"
                className="min-h-[140px]"
              />
              <p className="text-xs text-muted-foreground">
                Đánh giá sẽ được chấm sentiment (0-100) và hiển thị màu xanh/vàng/đỏ.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              {myReview?.id && (
                <Button
                  type="button"
                  variant="destructive"
                  className="rounded-lg mr-auto"
                  onClick={() => void removeMyReview()}
                  disabled={submittingReview || deletingReview}
                >
                  <Trash2 className="h-4 w-4" />
                  Xóa
                </Button>
              )}
              <Button
                type="button"
                variant="outline"
                className="rounded-lg"
                onClick={() => setReviewDialogOpen(false)}
                disabled={submittingReview || deletingReview}
              >
                Hủy
              </Button>
              <Button
                type="button"
                className="rounded-lg"
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
