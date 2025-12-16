import { Card } from "../../components/ui/card";
import { ScrollArea } from "../../components/ui/scroll-area";
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
            <p className="text-pink-700 text-lg max-w-3xl mx-auto">
              Cập nhật lần cuối: 08 tháng 12, 2025
            </p>
          </div>

          {/* Privacy Policy */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="flex items-center gap-3 mb">
              <div
                className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center"
                style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
              >
                <Lock className="h-6 w-6 text-white" />
              </div>
              <h2 className="text-pink-800 font-bold">CHÍNH SÁCH BẢO MẬT</h2>
            </div>
            <div className="space-y-4 text-gray-700 text-ju">
              <div>
                <h3 className="font-bold text-pink-700 mb-2">1. Thu thập thông tin</h3>
                <p>
                Để cung cấp trải nghiệm cá nhân hóa, hệ thống thu thập các thông tin tối thiểu sau:
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1 text-ju">
                  <li><strong>Thông tin tài khoản:</strong> Tên hiển thị và Email (được sử dụng để đăng nhập và xác thực OTP).</li>
                  <li><strong>Dữ liệu vị trí (Location):</strong> Tọa độ GPS của bạn chỉ được thu thập khi bạn cấp quyền, nhằm mục đích tính khoảng cách đến nhà hàng và gợi ý quán ăn gần nhất. Chúng tôi không lưu trữ lịch sử di chuyển của bạn.</li>
                  <li><strong>Nội dung tương tác:</strong> Lịch sử trò chuyện với Chatbot và các bài Đánh giá (Review) bạn đăng tải.</li>
                </ul>
                </p>
              </div>
              <div>
                <h3 className="font-bold text-pink-700 mb-2">2. Sử dụng thông tin</h3>
                <p>
                  Thông tin của bạn được sử dụng để:
                </p>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                  <li>Xác nhận và quản lý đặt chỗ</li>
                  <li>Liên hệ về đơn đặt bàn của bạn</li>
                  <li>Cung cấp gợi ý món ăn phù hợp với khẩu vị và ngân sách</li>
                  <li>Cải thiện dịch vụ và trải nghiệm người dùng</li>
                  <li>Gửi thông tin khuyến mãi (nếu bạn đồng ý)</li>
                </ul>
              </div>
              <div>
                <h3 className="font-bold text-pink-700 mb-2">3. Cam kết bảo mật</h3>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1 text-ju">
                <li>Mật khẩu của bạn được mã hóa một chiều (Hashing) trước khi lưu vào cơ sở dữ liệu, đảm bảo không ai (kể cả quản trị viên) có thể nhìn thấy</li>
                <li>Chúng tôi cam kết không chia sẻ, bán hoặc trao đổi thông tin cá nhân của bạn cho bất kỳ bên thứ ba nào vì mục đích thương mại</li>
                </ul>
              </div>
            </div>
          </Card>

          {/* Terms of Service */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="flex items-center gap-3 mb">
              <div
                className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center"
                style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
              >
                <FileText className="h-6 w-6 text-white" />
              </div>
              <h2 className="text-pink-800 font-bold">ĐIỀU KHOẢN SỬ DỤNG</h2>
            </div>
            <div className="space-y-4 text-gray-700">
              <div>
                <h3 className="font-bold text-pink-700 mb-2">1. Chấp nhận điều khoản</h3>
                <p>
                  Khi sử dụng dịch vụ của chúng tôi, bạn đồng ý tuân theo các điều khoản và điều kiện được nêu dưới đây.
                </p>
              </div>
              <div>
                <h3 className="font-bold text-pink-700 mb-2">2. Tài khoản và Bảo mật</h3>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1 text-ju">
                <li> Bạn chịu trách nhiệm bảo mật thông tin đăng nhập của mình</li>
                <li> Hệ thống sử dụng xác thực qua Email và OTP. Bạn cần cung cấp email thật để kích hoạt tài khoản</li>
                <li> Hệ thống có cơ chế giới hạn đăng nhập (Rate Limiting) để bảo vệ tài khoản khỏi các cuộc tấn công dò mật khẩu</li>
                </ul> 
              </div>
              <div>
                <h3 className="font-bold text-pink-700 mb-2">3. Trách nhiệm người dùng</h3>
                <p>
                Khi sử dụng Food Journey Assistant, bạn đồng ý và cam kết:
                </p>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1 text-ju">
                  <li><strong>Sử dụng văn minh:</strong> Không sử dụng ngôn từ thô tục, kích động, xúc phạm hoặc các nội dung vi phạm pháp luật Việt Nam khi tương tác với Chatbot hoặc viết đánh giá</li>
                  <li><strong>Không gian lận:</strong> Không thực hiện các hành vi gian lận như spam đánh giá (seeding), sử dụng công cụ tự động để thao túng thứ hạng quán ăn, hoặc cố tình phá hoại uy tín của nhà hàng/đối thủ cạnh tranh</li>
                  <li><strong>Bảo vệ tài khoản:</strong> Tự bảo quản mật khẩu và mã OTP. Thông báo ngay cho chúng tôi nếu phát hiện tài khoản bị truy cập trái phép.</li>
                </ul>
              </div>
              <div>
                <h3 className="font-bold text-pink-700 mb-2">4. Trách nhiệm của chúng tôi</h3>
                <p>
                Với vai trò là đơn vị phát triển và vận hành nền tảng, chúng tôi cam kết:
                </p>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1 text-ju">
                  <li><strong>Duy trì hoạt động:</strong> Nỗ lực đảm bảo hệ thống hoạt động ổn định 24/7 để phục vụ nhu cầu tra cứu của bạn (ngoại trừ các trường hợp bảo trì đã thông báo trước hoặc sự cố bất khả kháng)</li>
                  <li><strong>Bảo vệ dữ liệu:</strong> Áp dụng các biện pháp kỹ thuật (như mã hóa mật khẩu, bảo mật 2 lớp) để bảo vệ thông tin cá nhân của bạn khỏi các truy cập trái phép</li>
                  <li><strong>Trung lập & Khách quan:</strong> Đảm bảo các thuật toán gợi ý và xếp hạng quán ăn hoạt động công bằng, không thiên vị hoặc nhận tiền để ưu tiên (trừ các vị trí quảng cáo được đánh dấu rõ ràng)</li>
                  <li><strong>Hỗ trợ người dùng:</strong> Tiếp nhận và xử lý các báo cáo về lỗi kỹ thuật, nội dung xấu hoặc tranh chấp trong thời gian sớm nhất có thể</li>
                </ul>
              </div>
            </div>
          </Card>

          {/* Cookie Policy */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="flex items-center gap-3">
              <div
                className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center"
                style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
              >
                <Eye className="h-6 w-6 text-white" />
              </div>
              <h2 className="text-pink-800 font-bold">CHÍNH SÁCH COOKIE VÀ CÔNG NGHỆ LƯU TRỮ</h2>
            </div>
            <div className="space-y-4 text-gray-700 text-ju">
              <div>
                <h3 className="font-bold text-pink-700 mb-2">1. Giới thiệu chung</h3>
                <p>
                  Để đảm bảo Food Journey Assistant vận hành trơn tru, bảo mật và mang lại trải nghiệm cá nhân hóa tốt nhất, chúng tôi sử dụng các công nghệ lưu trữ dữ liệu trên trình duyệt (Browser Storage) bao gồm Cookie và Local Storage.
                  <br/>
                  Vì nền tảng của chúng tôi được xây dựng theo kiến trúc Single Page Application (SPA) hiện đại, chúng tôi ưu tiên sử dụng Local Storage để lưu trữ dữ liệu phiên làm việc thay vì Cookie truyền thống, giúp tăng tốc độ tải trang và bảo mật tốt hơn.
                </p>
              </div>
              <div>
                <h3 className="font-bold text-pink-700 mb-2">2. Các loại dữ liệu chúng tôi lưu trữ</h3>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1 text-ju">
                <li> <strong>Lưu trữ Thiết yếu (Strictly Necessary):</strong> Đây là các dữ liệu bắt buộc để hệ thống hoạt động. Nếu thiếu chúng, bạn sẽ không thể đăng nhập hoặc sử dụng các tính năng bảo mật. Giúp hệ thống nhận diện bạn là ai sau khi đăng nhập, cho phép bạn truy cập vào các tính năng dành riêng cho thành viên như: Chatbot tư vấn chuyên sâu, Đặt bàn, và Viết đánh giá.</li>
                <li> <strong>Lưu trữ Chức năng (Functional Storage):</strong> Giúp hệ thống "ghi nhớ" các cài đặt ưa thích của bạn để bạn không phải thiết lập lại mỗi lần truy cập. Lưu trữ lựa chọn ngôn ngữ (Tiếng Việt / Tiếng Anh) và trạng thái giao diện (Sáng/Tối) để duy trì trải nghiệm nhất quán.</li>
                <li> <strong>Cookie Phân tích (Analytics Cookies):</strong> Giúp chúng tôi hiểu cách người dùng tương tác với website để cải thiện chất lượng dịch vụ. Đo lường các chỉ số ẩn danh như: số lượng người truy cập, thời gian trung bình trên trang, và luồng di chuyển của người dùng (User Flows). Những dữ liệu này hoàn toàn ẩn danh và không được dùng để định danh cá nhân bạn.</li>
                </ul> 
              </div>
              <div>
                <h3 className="font-bold text-pink-700 mb-2">3. Quản lý và Kiểm soát</h3>
                <ul className="list-disc list-inside ml-4 mt-2 space-y-1 text-ju">
                <li> <strong>Lưu trữ Thiết yếu (Strictly Necessary):</strong> Bạn có quyền xóa bộ nhớ Cache, Local Storage hoặc chặn Cookie bất kỳ lúc nào thông qua phần "Cài đặt" (Settings) trên trình duyệt web của bạn</li>
                <li> <strong>Lưu trữ Chức năng (Functional Storage):</strong> Vì hệ thống sử dụng Local Storage để xác thực đăng nhập, nếu bạn xóa toàn bộ dữ liệu trang web, bạn sẽ bị đăng xuất ngay lập tức và quay trở lại chế độ khách (Guest Mode). Các cài đặt cá nhân như ngôn ngữ cũng sẽ trở về mặc định</li>
                </ul> 
              </div>
            </div>
          </Card>

          {/* Contact for Policy */}
          <Card
            className="bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 border-2 border-pink-300 rounded-3xl p-8 md:p-12 text-center shadow-2xl"
            style={{ boxShadow: "0 0 40px rgba(255,182,193,0.5)" }}
          >
            <h2 className="text-white font-bold">CÂU HỎI VỀ CHÍNH SÁCH</h2>
            <p className="text-white/90 text-lg max-w-3xl mx-auto text-ju">
              Nếu bạn có bất kỳ thắc mắc hoặc cần hỗ trợ liên quan đến Chính sách & Điều khoản, vui lòng liên hệ với chúng tôi qua email:{" "}
              <strong>habiassistant@gmail.com</strong>
            </p>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
