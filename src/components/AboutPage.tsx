import { Card } from "./ui/card";
import { ScrollArea } from "./ui/scroll-area";
import { UtensilsCrossed, Heart, Star, Users, Award, Sparkles } from "lucide-react";

const teamMembers = [
  { name: "Nguyễn Văn A", role: "Founder & CEO", emoji: "👨‍💼" },
  { name: "Trần Thị B", role: "Head Chef", emoji: "👩‍🍳" },
  { name: "Lê Văn C", role: "Operations Manager", emoji: "👨‍💻" },
  { name: "Phạm Thị D", role: "Customer Service", emoji: "👩‍💼" },
];

const stats = [
  { icon: Users, label: "Khách hàng", value: "10,000+" },
  { icon: UtensilsCrossed, label: "Nhà hàng", value: "50+" },
  { icon: Star, label: "Đánh giá 5 sao", value: "95%" },
  { icon: Award, label: "Giải thưởng", value: "15+" },
];

export function AboutPage() {
  return (
    <div className="min-h-screen relative">
      <ScrollArea className="h-screen">
        <div className="max-w-5xl mx-auto p-4 md:p-6 pt-20 space-y-12 pb-12">
          {/* Header */}
          <div className="text-center space-y-6">
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
              Về chúng tôi
            </h1>
            <p className="text-pink-700 text-lg max-w-3xl mx-auto">
              Chúng tôi là nền tảng đặt bàn nhà hàng hàng đầu, kết nối thực khách với những trải nghiệm ẩm thực tuyệt vời
            </p>
          </div>

          {/* Our Story */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="flex items-center gap-3 mb-6">
              <Sparkles className="h-8 w-8 text-pink-500" />
              <h2 className="text-pink-800">Câu chuyện của chúng tôi</h2>
            </div>
            <div className="space-y-4 text-gray-700">
              <p>
                Cosmic Vietnamese Food Galaxy được thành lập vào năm 2020 với sứ mệnh mang đến trải nghiệm ẩm thực Việt Nam tuyệt vời nhất cho mọi người. Chúng tôi tin rằng ẩm thực không chỉ là món ăn, mà còn là văn hóa, là câu chuyện, là kết nối.
              </p>
              <p>
                Với hệ thống đặt bàn thông minh và chatbot AI hỗ trợ, chúng tôi giúp bạn dễ dàng tìm kiếm và trải nghiệm các món ăn Việt Nam đích thực. Từ phở Hà Nội đến bánh mì Sài Gòn, từ bún chả đến gỏi cuốn, chúng tôi kết nối bạn với những hương vị tuyệt vời nhất.
              </p>
              <p>
                Đội ngũ của chúng tôi gồm những người đam mê ẩm thực, công nghệ và dịch vụ khách hàng. Chúng tôi không ngừng nỗ lực để mang đến trải nghiệm tốt nhất cho mỗi khách hàng.
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
                  className="w-14 h-14 rounded-2xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center shadow-lg mx-auto mb-3"
                  style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
                >
                  <stat.icon className="h-7 w-7 text-white" />
                </div>
                <div className="text-pink-800 mb-1">{stat.value}</div>
                <p className="text-sm text-gray-600">{stat.label}</p>
              </Card>
            ))}
          </div>

          {/* Our Values */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <h2 className="text-pink-800 mb-6 text-center">Giá trị cốt lõi</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center space-y-3">
                <div className="text-5xl mb-2">🌟</div>
                <h3 className="text-pink-700">Chất lượng</h3>
                <p className="text-sm text-gray-600">
                  Cam kết mang đến những nhà hàng và món ăn chất lượng cao nhất
                </p>
              </div>
              <div className="text-center space-y-3">
                <div className="text-5xl mb-2">💖</div>
                <h3 className="text-pink-700">Tận tâm</h3>
                <p className="text-sm text-gray-600">
                  Phục vụ khách hàng với sự tận tâm và nhiệt huyết
                </p>
              </div>
              <div className="text-center space-y-3">
                <div className="text-5xl mb-2">🚀</div>
                <h3 className="text-pink-700">Đổi mới</h3>
                <p className="text-sm text-gray-600">
                  Không ngừng đổi mới và cải tiến trải nghiệm người dùng
                </p>
              </div>
            </div>
          </Card>

          {/* Team */}
          <div className="space-y-6">
            <h2 className="text-pink-800 text-center">Đội ngũ của chúng tôi</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {teamMembers.map((member, idx) => (
                <Card
                  key={idx}
                  className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-6 text-center shadow-lg hover:shadow-xl transition-all"
                  style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
                >
                  <div className="text-6xl mb-3">{member.emoji}</div>
                  <h4 className="text-gray-900 mb-1">{member.name}</h4>
                  <p className="text-sm text-pink-600">{member.role}</p>
                </Card>
              ))}
            </div>
          </div>

          {/* Mission */}
          <Card
            className="bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 border-2 border-pink-300 rounded-3xl p-8 md:p-12 text-center shadow-2xl"
            style={{ boxShadow: "0 0 40px rgba(255,182,193,0.5)" }}
          >
            <h2 className="text-white mb-4">Sứ mệnh của chúng tôi</h2>
            <p className="text-white/90 text-lg max-w-3xl mx-auto">
              Kết nối mọi người với ẩm thực Việt Nam đích thực, tạo ra những trải nghiệm đáng nhớ và lan tỏa tình yêu với văn hóa ẩm thực Việt đến khắp thế giới.
            </p>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
