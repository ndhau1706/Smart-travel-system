import { Card } from "./ui/card";
import { ScrollArea } from "./ui/scroll-area";
import { UtensilsCrossed, Heart, Star, Users, Award, Sparkles , Clock} from "lucide-react";

const teamMembers = [
  { name: "Nguyễn Đăng Hậu", role: ["Founder", "Chatbot Engineer"], emoji: "👨‍💼" },
  { name: "Nguyễn Khánh Linh", role: ["Data Engineer"], emoji: "👩‍💼" }, 
  { name: "Bùi Thị Bích Loan", role: ["Front-end Developer"], emoji: "👩‍💻" },
  { name: "Lê Đoàn Nhật Huy", role: ["Front-end Developer"], emoji: "👨‍💼" },
  { name: "Trần Cao Danh", role: ["Back-end Developer"], emoji: "👨‍💻" },
  { name: "Trần Lê Hải", role: ["Back-end Developer"], emoji: "👨‍💻" }, 
  
];

const stats = [
  { icon: Users, label: "Truy vấn AI đã xử lý", value: "1,000+" },
  { icon: UtensilsCrossed, label: "Nhà hàng", value: "100+" },
  { icon: Star, label: "Độ chính xác gợi ý", value: "90%+" },
  { icon: Clock, label: "Thời gian chọn quán", value: "< 5 Phút" },
];

export function AboutPage() {
  return (
    <div className="min-h-screen relative">
      <ScrollArea className="h-screen">
        <div className="max-w-5xl mx-auto p-4 md:p-6 pt-20 space-y-12 pb-12">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="flex justify-center mb-4">
              <div
                className="p-8 rounded-full bg-gradient-to-br from-pink-400 via-rose-400 to-fuchsia-400 shadow-2xl animate-pulse border-4 border-pink-200"
                style={{
                  animationDuration: "2s",
                  boxShadow: "0 0 60px rgba(255,182,193,0.8), inset 0 0 30px rgba(255,255,255,0.5)",
                }}
              >
                <Heart className="h-20 w-20 text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.9)]" />
              </div>
            </div>
            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
            Thông tin HabiGroup
            </h1>
            <p className="text-pink-700 text-lg max-w-3xl mx-auto">
            Hơn cả một bữa ăn, đó là hành trình khám phá văn hóa ẩm thực Việt Nam
            </p>
          </div>

          {/* Our Story */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="flex items-center gap-3 mb-1">
              <Sparkles className="h-8 w-8 text-pink-500" />
              <h2 className="text-pink-800">Câu chuyện của chúng tôi</h2>
            </div>
            <div className="space-y-4 text-gray-700 text-ju">
              <p>
                Bạn đã bao giờ mất hàng giờ đồng hồ lướt điện thoại chỉ để trả lời câu hỏi "Hôm nay ăn gì?", hay thất vọng vì những quán ăn "trên ảnh lung linh, ngoài đời tàn khốc"? Chúng tôi hiểu cảm giác đó.
              </p>
              <p>
                HabiGroup ra đời với một sứ mệnh đơn giản: Trở thành người bạn đồng hành tin cậy của bạn trên bản đồ ẩm thực Việt Nam. Không chỉ là công cụ tìm kiếm, chúng tôi sử dụng Trí tuệ nhân tạo (AI) để thấu hiểu khẩu vị riêng biệt của bạn, từ đó gợi ý những "viên ngọc ẩn" (hidden gems) mà chỉ người bản địa mới biết.
              </p>
              <p>
                Tại đây, chúng tôi nói "Không" với review ảo. Mọi gợi ý đều dựa trên dữ liệu xác thực và đánh giá khách quan, giúp bạn tự tin khám phá từ những gánh hàng rong bình dị đến những nhà hàng tinh tế nhất.
              </p>
              <p>
                Hãy để chúng tôi lo phần "nghĩ", bạn chỉ việc tận hưởng trọn vẹn hương vị Việt Nam.
              </p>
            </div>
          </Card>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((stat, idx) => (
              <Card
                key={idx}
                className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-6 text-center shadow-lg hover:shadow-xl transition-all"
                style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
              >
                <div
                  className="w-14 h-14 rounded-2xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center shadow-lg mx-auto mb"
                  style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
                >
                  <stat.icon className="h-7 w-7 text-white" />
                </div>
                <div className="text-pink-800 mb">{stat.value}</div>
                <p className="text-sm text-gray-600">{stat.label}</p>
              </Card>
            ))}
          </div>

          {/* Our Values */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <h2 className="text-pink-800 mb-1 text-center">Giá trị cốt lõi</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center space-y-3">
                <div className="text-5xl mb-3">🌟</div>
                <h3 className="text-pink-700 mb-2">Minh bạch</h3>
                <p className="text-sm text-gray-600 text-center">
                  Cam kết dữ liệu quán ăn được xác thực và đánh giá khách quan, nói không với review ảo 
                </p>
              </div>
              <div className="text-center space-y-3">
                <div className="text-5xl mb-3">💖</div>
                <h3 className="text-pink-700 mb-2">Thấu hiểu</h3>
                <p className="text-sm text-gray-600 text-center">
                    Cá nhân hóa trải nghiệm ăn uống. Chatbot AI lắng nghe và ghi nhớ khẩu vị riêng biệt của chính bạn
                </p>
              </div>
              <div className="text-center space-y-3">
                <div className="text-5xl mb-3">🚀</div>
                <h3 className="text-pink-700 mb-2">Bản sắc</h3>
                <p className="text-sm text-gray-600 text-center">
                  Tôn vinh ẩm thực địa phương. Giúp bạn tìm ra những "viên ngọc ẩn" (hidden gems) đậm chất Việt Nam
                </p>
              </div>
            </div>
          </Card>

          {/* Team */}
          <div className="space-y-6">
            <h2 className="text-pink-800 text-center">Đội ngũ của chúng tôi</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              {teamMembers.map((member, idx) => (
                <Card
                  key={idx}
                  className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-6 text-center shadow-lg hover:shadow-xl transition-all"
                  style={{ boxShadow: "0 0 50px rgba(255,182,193,0.3)" }}
                >
                  <div className="text-6xl mb">{member.emoji}</div>
                  <h4 className="text-gray-900 mb font-bold">{member.name}</h4>
                  <div className="text-sm text-pink-600">
                    {Array.isArray(member.role) ? (
                      member.role.map((r, i) => (
                        <div key={i}>{r}</div>
                      ))
                    ) : (
                      member.role
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Mission */}
          <Card
            className="bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 border-2 border-pink-300 rounded-3xl p-8 md:p-12 text-center shadow-2xl"
            style={{ boxShadow: "0 0 40px rgba(255,182,193,0.5)" }}
          >
            <h2 className="text-white mb-2">Sứ mệnh của chúng tôi</h2>
            <p className="text-white/90 text-lg max-w-3xl mx-auto text-ju">
              Sứ mệnh của HabiGroup là mang đến trải nghiệm khám phá ẩm thực Việt Nam chuẩn xác và đậm chất bản địa thông qua công nghệ AI cá nhân hóa. Chúng tôi khao khát kết nối thực khách với những giá trị văn hóa chân thực nhất, đậm đà nhất, đồng thời hỗ trợ các quán ăn địa phương lan tỏa hương vị truyền thống đến bạn bè quốc tế.
            </p>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
