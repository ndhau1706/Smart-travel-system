import { Card } from "./ui/card";
import { ScrollArea } from "./ui/scroll-area";
import { Shield, Lock, Eye, FileText } from "lucide-react";

export function PolicyPage() {
  return (
    <div className="min-h-screen relative">
      <ScrollArea className="h-screen">
        <div className="max-w-4xl mx-auto p-4 md:p-6 pt-20 space-y-6 pb-12">
          {/* Header */}
          <div className="text-center space-y-3">
            <div className="flex justify-center mb-4">
              <div
                className="p-6 rounded-full bg-gradient-to-br from-pink-400 via-rose-400 to-fuchsia-400 shadow-2xl animate-pulse border-4 border-pink-200"
                style={{
                  animationDuration: "2s",
                  boxShadow: "0 0 50px rgba(255,182,193,0.8), inset 0 0 25px rgba(255,255,255,0.5)",
                }}
              >
                <Shield className="h-16 w-16 text-white drop-shadow-[0_0_12px_rgba(255,255,255,0.9)]" />
              </div>
            </div>
            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
              Chính sách & Điều khoản
            </h1>
            <p className="text-pink-700">
              Cập nhật lần cuối: 6 tháng 11, 2025
            </p>
          </div>

          {/* Privacy Policy */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div
                className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center"
                style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
              >
                <Lock className="h-6 w-6 text-white" />
              </div>
              <h2 className="text-pink-800">Chính sách bảo mật</h2>
            </div>
            <div className="space-y-4 text-gray-700">
              <div>
                <h3 className="text-pink-700 mb-2">1. Thu thập thông tin</h3>
                <p>
                  Chúng tôi thu thập thông tin cá nhân như tên, email, số điện thoại khi bạn đăng ký tài khoản hoặc đặt bàn. Thông tin này được sử dụng để cung cấp dịch vụ tốt hơn cho bạn.
                </p>
              </div>
              <div>
                <h3 className="text-pink-700 mb-2">2. Sử dụng thông tin</h3>
                <p>
                  Thông tin của bạn được sử dụng để:
                </p>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                  <li>Xác nhận và quản lý đặt chỗ</li>
                  <li>Liên hệ về đơn đặt bàn của bạn</li>
                  <li>Cải thiện dịch vụ và trải nghiệm người dùng</li>
                  <li>Gửi thông tin khuyến mãi (nếu bạn đồng ý)</li>
                </ul>
              </div>
              <div>
                <h3 className="text-pink-700 mb-2">3. Bảo vệ thông tin</h3>
                <p>
                  Chúng tôi cam kết bảo vệ thông tin cá nhân của bạn bằng các biện pháp bảo mật hiện đại. Thông tin của bạn được mã hóa và lưu trữ an toàn.
                </p>
              </div>
              <div>
                <h3 className="text-pink-700 mb-2">4. Chia sẻ thông tin</h3>
                <p>
                  Chúng tôi không bán hoặc cho thuê thông tin cá nhân của bạn cho bên thứ ba. Thông tin chỉ được chia sẻ với nhà hàng liên quan để xử lý đặt chỗ.
                </p>
              </div>
            </div>
          </Card>

          {/* Terms of Service */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div
                className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center"
                style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
              >
                <FileText className="h-6 w-6 text-white" />
              </div>
              <h2 className="text-pink-800">Điều khoản sử dụng</h2>
            </div>
            <div className="space-y-4 text-gray-700">
              <div>
                <h3 className="text-pink-700 mb-2">1. Chấp nhận điều khoản</h3>
                <p>
                  Khi sử dụng dịch vụ của chúng tôi, bạn đồng ý tuân theo các điều khoản và điều kiện được nêu dưới đây.
                </p>
              </div>
              <div>
                <h3 className="text-pink-700 mb-2">2. Đặt chỗ và hủy bỏ</h3>
                <p>
                  - Bạn có thể đặt chỗ trực tuyến 24/7
                  <br />
                  - Hủy đặt chỗ miễn phí nếu thông báo trước ít nhất 2 giờ
                  <br />
                  - Hủy muộn hoặc không đến có thể bị tính phí theo chính sách của nhà hàng
                </p>
              </div>
              <div>
                <h3 className="text-pink-700 mb-2">3. Trách nhiệm người dùng</h3>
                <p>
                  Bạn cam kết:
                </p>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                  <li>Cung cấp thông tin chính xác khi đặt chỗ</li>
                  <li>Đến đúng giờ đã đặt</li>
                  <li>Thông báo kịp thời nếu cần thay đổi hoặc hủy</li>
                  <li>Không sử dụng dịch vụ cho mục đích gian lận</li>
                </ul>
              </div>
              <div>
                <h3 className="text-pink-700 mb-2">4. Trách nhiệm của chúng tôi</h3>
                <p>
                  Chúng tôi cam kết:
                </p>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                  <li>Xác nhận đặt chỗ trong vòng 15 phút</li>
                  <li>Cung cấp thông tin chính xác về nhà hàng</li>
                  <li>Hỗ trợ khách hàng kịp thời</li>
                  <li>Bảo vệ thông tin cá nhân của bạn</li>
                </ul>
              </div>
            </div>
          </Card>

          {/* Cookie Policy */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div
                className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center"
                style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
              >
                <Eye className="h-6 w-6 text-white" />
              </div>
              <h2 className="text-pink-800">Chính sách Cookie</h2>
            </div>
            <div className="space-y-4 text-gray-700">
              <p>
                Chúng tôi sử dụng cookies và các công nghệ tương tự để cải thiện trải nghiệm người dùng, phân tích lưu lượng truy cập và cá nhân hóa nội dung.
              </p>
              <div>
                <h3 className="text-pink-700 mb-2">Loại cookies chúng tôi sử dụng:</h3>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                  <li><strong>Cookies cần thiết:</strong> Để website hoạt động đúng cách</li>
                  <li><strong>Cookies hiệu suất:</strong> Để phân tích cách người dùng sử dụng website</li>
                  <li><strong>Cookies chức năng:</strong> Để ghi nhớ các tùy chọn của bạn</li>
                  <li><strong>Cookies quảng cáo:</strong> Để hiển thị quảng cáo phù hợp (nếu có)</li>
                </ul>
              </div>
              <p>
                Bạn có thể quản lý hoặc xóa cookies trong cài đặt trình duyệt của mình. Tuy nhiên, việc tắt cookies có thể ảnh hưởng đến trải nghiệm sử dụng.
              </p>
            </div>
          </Card>

          {/* Contact for Policy */}
          <Card
            className="bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 border-2 border-pink-300 rounded-3xl p-8 text-center shadow-2xl"
            style={{ boxShadow: "0 0 40px rgba(255,182,193,0.5)" }}
          >
            <h3 className="text-white mb-3">Có câu hỏi về chính sách?</h3>
            <p className="text-white/90 mb-4">
              Nếu bạn có bất kỳ câu hỏi nào về chính sách bảo mật hoặc điều khoản sử dụng, vui lòng liên hệ với chúng tôi qua email:
            </p>
            <p className="text-white">
              <strong>privacy@foodgalaxy.vn</strong>
            </p>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
