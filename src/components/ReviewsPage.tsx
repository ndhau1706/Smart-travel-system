import { useState } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { Textarea } from "./ui/textarea";
import { Star, ThumbsUp, MessageSquare, Plus } from "lucide-react";
import { toast } from "sonner@2.0.3";
import { ImageWithFallback } from "./figma/ImageWithFallback";

interface Review {
  id: string;
  restaurantName: string;
  restaurantImage: string;
  userName: string;
  rating: number;
  date: string;
  comment: string;
  likes: number;
  images?: string[];
}

const mockReviews: Review[] = [
  {
    id: "1",
    restaurantName: "Phở Hà Nội",
    restaurantImage: "https://images.unsplash.com/photo-1701480253822-1842236c9a97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcGhvJTIwbm9vZGxlJTIwc291cHxlbnwxfHx8fDE3NjI0MDY1OTB8MA&ixlib=rb-4.1.0&q=80&w=1080",
    userName: "Nguyễn Văn A",
    rating: 5,
    date: "2 ngày trước",
    comment: "Phở ở đây ngon tuyệt vời! Nước dùng đậm đà, thịt bò tươi và mềm. Không gian sạch sẽ, nhân viên phục vụ nhiệt tình. Chắc chắn sẽ quay lại!",
    likes: 24,
  },
  {
    id: "2",
    restaurantName: "Bánh Mì Sài Gòn",
    restaurantImage: "https://images.unsplash.com/photo-1599719455360-ff0be7c4dd06?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwYmFuaCUyMG1pJTIwc2FuZHdpY2h8ZW58MXx8fHwxNzYyNDA2NTkwfDA&ixlib=rb-4.1.0&q=80&w=1080",
    userName: "Trần Thị B",
    rating: 4,
    date: "5 ngày trước",
    comment: "Bánh mì giòn tan, nhân thịt nướng thơm ngon. Giá cả phải chăng. Tuy nhiên phải xếp hàng khá lâu vào giờ cao điểm.",
    likes: 18,
  },
  {
    id: "3",
    restaurantName: "Nhà Hàng Hải Sản Biển Xanh",
    restaurantImage: "https://images.unsplash.com/photo-1595215909290-847cb783facf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2MjMzMjYwNXww&ixlib=rb-4.1.0&q=80&w=1080",
    userName: "Lê Văn C",
    rating: 5,
    date: "1 tuần trước",
    comment: "Hải sản tươi sống, chế biến rất ngon! Tôm hấp bia và cua rang me đều tuyệt vời. Không gian rộng rãi, phù hợp cho gia đình.",
    likes: 32,
  },
];

export function ReviewsPage() {
  const [reviews] = useState<Review[]>(mockReviews);
  const [newReview, setNewReview] = useState("");
  const [newRating, setNewRating] = useState(5);
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleSubmitReview = () => {
    if (!newReview.trim()) {
      toast.error("Vui lòng nhập nội dung đánh giá");
      return;
    }

    toast.success("Đánh giá của bạn đã được gửi! ⭐", {
      description: "Cảm ơn bạn đã chia sẻ trải nghiệm",
    });

    setNewReview("");
    setNewRating(5);
    setDialogOpen(false);
  };

  const StarRating = ({ rating, interactive = false, onRate }: { rating: number; interactive?: boolean; onRate?: (rating: number) => void }) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-5 w-5 ${
              star <= rating
                ? "fill-yellow-400 text-yellow-400"
                : "text-gray-300"
            } ${interactive ? "cursor-pointer hover:scale-110 transition-transform" : ""}`}
            onClick={() => interactive && onRate?.(star)}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen relative">
      <ScrollArea className="h-screen">
        <div className="max-w-5xl mx-auto p-4 md:p-6 pt-20 space-y-6 pb-12">
          {/* Header */}
          <div className="text-center space-y-3">
            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
              ⭐ Đánh giá & Nhận xét
            </h1>
            <p className="text-pink-700">
              Chia sẻ trải nghiệm của bạn và xem đánh giá từ cộng đồng
            </p>
          </div>

          {/* Write Review Button */}
          <div className="flex justify-center">
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  className="bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl px-8 py-6 shadow-lg"
                  style={{ boxShadow: "0 0 25px rgba(255,182,193,0.5)" }}
                >
                  <Plus className="mr-2 h-5 w-5" />
                  Viết đánh giá mới
                </Button>
              </DialogTrigger>
              <DialogContent
                className="sm:max-w-md bg-gradient-to-br from-pink-50/95 via-rose-50/95 to-fuchsia-50/95 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-2xl"
                style={{ boxShadow: "0 0 40px rgba(255,182,193,0.4)" }}
              >
                <DialogHeader>
                  <DialogTitle className="text-pink-800">Viết đánh giá mới</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <label className="text-gray-700">Đánh giá của bạn</label>
                    <StarRating rating={newRating} interactive onRate={setNewRating} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-gray-700">Nhận xét</label>
                    <Textarea
                      placeholder="Chia sẻ trải nghiệm của bạn..."
                      value={newReview}
                      onChange={(e) => setNewReview(e.target.value)}
                      className="bg-white/80 border-pink-200 focus:border-pink-400 rounded-xl min-h-[120px]"
                    />
                  </div>
                  <Button
                    onClick={handleSubmitReview}
                    className="w-full bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-xl"
                  >
                    Gửi đánh giá
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="bg-pink-200/50 backdrop-blur-md rounded-2xl p-1 mb-6 w-full max-w-md mx-auto grid grid-cols-3">
              <TabsTrigger
                value="all"
                className="data-[state=active]:bg-white data-[state=active]:text-pink-700 rounded-xl"
              >
                Tất cả
              </TabsTrigger>
              <TabsTrigger
                value="recent"
                className="data-[state=active]:bg-white data-[state=active]:text-pink-700 rounded-xl"
              >
                Mới nhất
              </TabsTrigger>
              <TabsTrigger
                value="popular"
                className="data-[state=active]:bg-white data-[state=active]:text-pink-700 rounded-xl"
              >
                Phổ biến
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="space-y-4">
              {reviews.map((review) => (
                <Card
                  key={review.id}
                  className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl overflow-hidden shadow-lg"
                  style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
                >
                  <div className="flex gap-4 p-6">
                    <ImageWithFallback
                      src={review.restaurantImage}
                      alt={review.restaurantName}
                      className="w-20 h-20 rounded-2xl object-cover border-2 border-pink-200"
                    />
                    <div className="flex-1 space-y-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-pink-800">{review.restaurantName}</h3>
                          <p className="text-sm text-gray-600">{review.userName} • {review.date}</p>
                        </div>
                        <Badge
                          variant="secondary"
                          className="bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border-yellow-300 rounded-full"
                        >
                          <Star className="h-3 w-3 fill-yellow-400 text-yellow-400 mr-1" />
                          {review.rating}.0
                        </Badge>
                      </div>

                      <StarRating rating={review.rating} />

                      <p className="text-gray-700">{review.comment}</p>

                      <div className="flex gap-4 pt-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-pink-600 hover:text-pink-700 hover:bg-pink-100 rounded-xl"
                        >
                          <ThumbsUp className="h-4 w-4 mr-2" />
                          {review.likes}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-pink-600 hover:text-pink-700 hover:bg-pink-100 rounded-xl"
                        >
                          <MessageSquare className="h-4 w-4 mr-2" />
                          Trả lời
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </TabsContent>

            <TabsContent value="recent" className="space-y-4">
              {reviews.slice().reverse().map((review) => (
                <Card
                  key={review.id}
                  className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl overflow-hidden shadow-lg"
                  style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
                >
                  <div className="flex gap-4 p-6">
                    <ImageWithFallback
                      src={review.restaurantImage}
                      alt={review.restaurantName}
                      className="w-20 h-20 rounded-2xl object-cover border-2 border-pink-200"
                    />
                    <div className="flex-1 space-y-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-pink-800">{review.restaurantName}</h3>
                          <p className="text-sm text-gray-600">{review.userName} • {review.date}</p>
                        </div>
                        <Badge
                          variant="secondary"
                          className="bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border-yellow-300 rounded-full"
                        >
                          <Star className="h-3 w-3 fill-yellow-400 text-yellow-400 mr-1" />
                          {review.rating}.0
                        </Badge>
                      </div>
                      <StarRating rating={review.rating} />
                      <p className="text-gray-700">{review.comment}</p>
                      <div className="flex gap-4 pt-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-pink-600 hover:text-pink-700 hover:bg-pink-100 rounded-xl"
                        >
                          <ThumbsUp className="h-4 w-4 mr-2" />
                          {review.likes}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-pink-600 hover:text-pink-700 hover:bg-pink-100 rounded-xl"
                        >
                          <MessageSquare className="h-4 w-4 mr-2" />
                          Trả lời
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </TabsContent>

            <TabsContent value="popular" className="space-y-4">
              {reviews.slice().sort((a, b) => b.likes - a.likes).map((review) => (
                <Card
                  key={review.id}
                  className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl overflow-hidden shadow-lg"
                  style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
                >
                  <div className="flex gap-4 p-6">
                    <ImageWithFallback
                      src={review.restaurantImage}
                      alt={review.restaurantName}
                      className="w-20 h-20 rounded-2xl object-cover border-2 border-pink-200"
                    />
                    <div className="flex-1 space-y-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-pink-800">{review.restaurantName}</h3>
                          <p className="text-sm text-gray-600">{review.userName} • {review.date}</p>
                        </div>
                        <Badge
                          variant="secondary"
                          className="bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border-yellow-300 rounded-full"
                        >
                          <Star className="h-3 w-3 fill-yellow-400 text-yellow-400 mr-1" />
                          {review.rating}.0
                        </Badge>
                      </div>
                      <StarRating rating={review.rating} />
                      <p className="text-gray-700">{review.comment}</p>
                      <div className="flex gap-4 pt-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-pink-600 hover:text-pink-700 hover:bg-pink-100 rounded-xl"
                        >
                          <ThumbsUp className="h-4 w-4 mr-2" />
                          {review.likes}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-pink-600 hover:text-pink-700 hover:bg-pink-100 rounded-xl"
                        >
                          <MessageSquare className="h-4 w-4 mr-2" />
                          Trả lời
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </TabsContent>
          </Tabs>
        </div>
      </ScrollArea>
    </div>
  );
}
