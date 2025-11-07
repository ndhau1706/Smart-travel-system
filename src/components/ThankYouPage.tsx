import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { CheckCircle, Home, Calendar, MessageCircle } from "lucide-react";

interface ThankYouPageProps {
  onNavigateHome: () => void;
  onNavigateBookings: () => void;
  onNavigateChatbot: () => void;
}

export function ThankYouPage({ onNavigateHome, onNavigateBookings, onNavigateChatbot }: ThankYouPageProps) {
  return (
    <div className="min-h-screen relative flex items-center justify-center p-4">
      <Card
        className="max-w-2xl w-full bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 md:p-12 shadow-2xl text-center"
        style={{ boxShadow: "0 0 40px rgba(255,182,193,0.5)" }}
      >
        {/* Success Icon */}
        <div className="flex justify-center mb-6">
          <div
            className="p-8 rounded-full bg-gradient-to-br from-pink-400 via-rose-400 to-fuchsia-400 shadow-2xl animate-bounce border-4 border-pink-200"
            style={{
              animationDuration: "1s",
              animationIterationCount: "3",
              boxShadow: "0 0 60px rgba(255,182,193,0.8), inset 0 0 30px rgba(255,255,255,0.5)",
            }}
          >
            <CheckCircle className="h-20 w-20 text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.9)]" />
          </div>
        </div>

        {/* Thank You Message */}
        <div className="space-y-4 mb-8">
          <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
            🎉 Cảm ơn bạn! 🎉
          </h1>
          <p className="text-pink-700 text-lg">
            Đơn đặt bàn của bạn đã được ghi nhận thành công!
          </p>
          <p className="text-gray-600">
            Chúng tôi đã gửi email xác nhận đến địa chỉ email của bạn. 
            Nhà hàng sẽ liên hệ với bạn để xác nhận đặt chỗ trong vòng 15 phút.
          </p>
        </div>

        {/* Booking Details Summary */}
        <Card
          className="bg-white/80 backdrop-blur-md border-2 border-pink-200 rounded-2xl p-6 mb-8 text-left"
          style={{ boxShadow: "0 0 20px rgba(255,182,193,0.3)" }}
        >
          <h3 className="text-pink-800 mb-4 text-center">Chi tiết đặt chỗ</h3>
          <div className="space-y-2 text-gray-700">
            <div className="flex justify-between">
              <span>Mã đặt chỗ:</span>
              <span className="text-pink-600">#BK2025{Math.floor(Math.random() * 10000)}</span>
            </div>
            <div className="flex justify-between">
              <span>Trạng thái:</span>
              <span className="text-green-600">Đang chờ xác nhận</span>
            </div>
          </div>
        </Card>

        {/* Next Steps */}
        <div className="space-y-3 mb-8">
          <h3 className="text-pink-800">Bước tiếp theo</h3>
          <ul className="text-left text-gray-600 space-y-2">
            <li className="flex gap-2">
              <span>✅</span>
              <span>Kiểm tra email để xem chi tiết đặt chỗ</span>
            </li>
            <li className="flex gap-2">
              <span>📱</span>
              <span>Nhà hàng sẽ gọi điện xác nhận trong vòng 15 phút</span>
            </li>
            <li className="flex gap-2">
              <span>🍽️</span>
              <span>Đến nhà hàng đúng giờ để thưởng thức bữa ăn</span>
            </li>
            <li className="flex gap-2">
              <span>⭐</span>
              <span>Đánh giá trải nghiệm của bạn sau bữa ăn</span>
            </li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            onClick={onNavigateHome}
            className="bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl px-8 py-6 shadow-lg"
            style={{ boxShadow: "0 0 25px rgba(255,182,193,0.5)" }}
          >
            <Home className="mr-2 h-5 w-5" />
            Về trang chủ
          </Button>
          <Button
            onClick={onNavigateBookings}
            variant="outline"
            className="bg-white/80 border-2 border-pink-300 hover:bg-pink-100 text-pink-700 rounded-2xl px-8 py-6 shadow-lg"
          >
            <Calendar className="mr-2 h-5 w-5" />
            Xem đặt chỗ
          </Button>
        </div>

        {/* Chatbot CTA */}
        <div className="mt-8 pt-8 border-t-2 border-pink-200">
          <p className="text-gray-600 mb-4">
            Cần gợi ý món ăn hoặc tìm nhà hàng khác?
          </p>
          <Button
            onClick={onNavigateChatbot}
            variant="outline"
            className="bg-white/80 border-2 border-pink-300 hover:bg-pink-100 text-pink-700 rounded-2xl px-8 py-4"
          >
            <MessageCircle className="mr-2 h-5 w-5" />
            Hỏi chatbot AI
          </Button>
        </div>

        {/* Footer Message */}
        <div className="mt-8 text-sm text-gray-500">
          <p>Nếu cần hỗ trợ, vui lòng liên hệ: <strong className="text-pink-600">028 3823 4567</strong></p>
        </div>
      </Card>
    </div>
  );
}
