import { Card } from "../../components/ui/card";
import { ScrollArea } from "../../components/ui/scroll-area";
import { UtensilsCrossed, Heart, Star, Users, Sparkles, Clock } from "lucide-react";

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
    <div className="min-h-dvh">
      <ScrollArea className="h-dvh">
        <div className="max-w-5xl mx-auto p-4 md:p-8 pt-10 space-y-10 pb-12">
          {/* Header */}
          <div className="text-center space-y-3">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <Heart className="h-7 w-7" />
            </div>
            <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight">Thông tin HabiGroup</h1>
            <p className="text-muted-foreground text-base sm:text-lg max-w-3xl mx-auto">
              Hơn cả một bữa ăn, đó là hành trình khám phá văn hóa ẩm thực Việt Nam.
            </p>
          </div>

          {/* Our Story */}
          <Card
            className="rounded-xl border bg-card p-8 shadow-sm"
          >
            <div className="flex items-center gap-3 mb-1">
              <Sparkles className="h-6 w-6 text-highlight" />
              <h2 className="text-xl font-semibold tracking-tight">Câu chuyện của chúng tôi</h2>
            </div>
            <div className="space-y-4 text-muted-foreground">
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
                className="rounded-xl border bg-card p-6 text-center shadow-sm"
              >
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <stat.icon className="h-6 w-6" />
                </div>
                <div className="text-xl font-semibold">{stat.value}</div>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </Card>
            ))}
          </div>

          {/* Our Values */}
          <Card
            className="rounded-xl border bg-card p-8 shadow-sm"
          >
            <h2 className="text-xl font-semibold tracking-tight text-center mb-6">Giá trị cốt lõi</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center space-y-3">
                <div className="text-4xl">🌟</div>
                <h3 className="font-semibold">Minh bạch</h3>
                <p className="text-sm text-muted-foreground">
                  Cam kết dữ liệu quán ăn được xác thực và đánh giá khách quan, nói không với review ảo 
                </p>
              </div>
              <div className="text-center space-y-3">
                <div className="text-4xl">💖</div>
                <h3 className="font-semibold">Thấu hiểu</h3>
                <p className="text-sm text-muted-foreground">
                    Cá nhân hóa trải nghiệm ăn uống. Chatbot AI lắng nghe và ghi nhớ khẩu vị riêng biệt của chính bạn
                </p>
              </div>
              <div className="text-center space-y-3">
                <div className="text-4xl">🚀</div>
                <h3 className="font-semibold">Bản sắc</h3>
                <p className="text-sm text-muted-foreground">
                  Tôn vinh ẩm thực địa phương. Giúp bạn tìm ra những "viên ngọc ẩn" (hidden gems) đậm chất Việt Nam
                </p>
              </div>
            </div>
          </Card>

          {/* Team */}
          <div className="space-y-6">
            <h2 className="text-xl font-semibold tracking-tight text-center">Đội ngũ của chúng tôi</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              {teamMembers.map((member, idx) => (
                <Card
                  key={idx}
                  className="rounded-xl border bg-card p-6 text-center shadow-sm"
                >
                  <div className="text-6xl">{member.emoji}</div>
                  <h4 className="font-bold">{member.name}</h4>
                  <div className="text-sm text-muted-foreground font-medium">
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
            className="rounded-xl border bg-primary text-primary-foreground p-8 md:p-12 text-center shadow-sm"
          >
            <h2 className="text-2xl font-semibold tracking-tight">Sứ mệnh của chúng tôi</h2>
            <p className="text-primary-foreground/90 text-base sm:text-lg max-w-3xl mx-auto">
              Sứ mệnh của HabiGroup là mang đến trải nghiệm khám phá ẩm thực Việt Nam chuẩn xác và đậm chất bản địa thông qua công nghệ AI cá nhân hóa. Chúng tôi khao khát kết nối thực khách với những giá trị văn hóa chân thực nhất, đậm đà nhất, đồng thời hỗ trợ các quán ăn địa phương lan tỏa hương vị truyền thống đến bạn bè quốc tế.
            </p>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
