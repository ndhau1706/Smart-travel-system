import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { CheckCircle, Home, Calendar, MessageCircle } from "lucide-react";

interface ThankYouPageProps {
  onNavigateHome: () => void;
  onNavigateBookings: () => void;
  onNavigateChatbot: () => void;
}

export function ThankYouPage({ onNavigateHome, onNavigateBookings, onNavigateChatbot }: ThankYouPageProps) {
  return (
    <div className="min-h-dvh relative flex items-center justify-center p-4">
      <Card
        className="max-w-2xl w-full p-8 md:p-12 shadow-sm text-center"
      >
        {/* Success Icon */}
        <div className="flex justify-center mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <CheckCircle className="h-9 w-9" />
          </div>
        </div>

        {/* Thank You Message */}
        <div className="space-y-4 mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">Cảm ơn bạn!</h1>
          <p className="text-lg text-foreground">
            Đơn đặt bàn của bạn đã được ghi nhận thành công!
          </p>
          <p className="text-muted-foreground">
            Chúng tôi đã gửi email xác nhận đến địa chỉ email của bạn. 
            Nhà hàng sẽ liên hệ với bạn để xác nhận đặt chỗ trong vòng 15 phút.
          </p>
        </div>

        {/* Booking Details Summary */}
        <Card
          className="p-6 mb-8 text-left shadow-sm"
        >
          <h3 className="mb-4 text-center text-lg font-semibold">Chi tiết đặt chỗ</h3>
          <div className="space-y-2 text-sm text-foreground">
            <div className="flex justify-between">
              <span>Mã đặt chỗ:</span>
              <span className="font-medium text-primary">#BK2025{Math.floor(Math.random() * 10000)}</span>
            </div>
            <div className="flex justify-between">
              <span>Trạng thái:</span>
              <span className="font-medium text-highlight">Đang chờ xác nhận</span>
            </div>
          </div>
        </Card>

        {/* Next Steps */}
        <div className="space-y-3 mb-8">
          <h3 className="text-lg font-semibold">Bước tiếp theo</h3>
          <ul className="text-left text-muted-foreground space-y-2">
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
            className="h-11 px-6 rounded-lg"
          >
            <Home className="mr-2 h-5 w-5" />
            Về trang chủ
          </Button>
          <Button
            onClick={onNavigateBookings}
            variant="outline"
            className="h-11 px-6 rounded-lg"
          >
            <Calendar className="mr-2 h-5 w-5" />
            Xem đặt chỗ
          </Button>
        </div>

        {/* Chatbot CTA */}
        <div className="mt-8 pt-8 border-t">
          <p className="text-muted-foreground mb-4">
            Cần gợi ý món ăn hoặc tìm nhà hàng khác?
          </p>
          <Button
            onClick={onNavigateChatbot}
            variant="outline"
            className="h-11 px-6 rounded-lg"
          >
            <MessageCircle className="mr-2 h-5 w-5" />
            Hỏi chatbot AI
          </Button>
        </div>

        {/* Footer Message */}
        <div className="mt-8 text-sm text-muted-foreground">
          <p>Nếu cần hỗ trợ, vui lòng liên hệ: <strong className="text-primary">028 3823 4567</strong></p>
        </div>
      </Card>
    </div>
  );
}
