import { useState } from "react";
import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import { ScrollArea } from "../../components/ui/scroll-area";
import { Mail, Phone, MapPin, Send, Clock } from "lucide-react";
import { toast } from "sonner";

export function ContactPage() {

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    subject: "",
    message: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.email || !formData.message) {
      toast.error("Vui lòng điền đầy đủ thông tin bắt buộc");
      return;
    }

    toast.success("Gửi tin nhắn thành công! 📧", {
      description: "Chúng tôi sẽ phản hồi trong vòng 24 giờ",
    });

    // Reset form
    setFormData({
      name: "",
      email: "",
      phone: "",
      subject: "",
      message: "",
    });
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-dvh">
      <ScrollArea className="h-dvh">
        <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-8 pb-12 pt-10">
          {/* Header */}
          <div className="text-center space-y-3">
            <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight">Liên hệ</h1>
            <p className="text-muted-foreground text-base sm:text-lg max-w-3xl mx-auto">
              Chúng tôi luôn sẵn sàng lắng nghe ý kiến và hỗ trợ bạn.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Contact Form */}
            <div className="lg:col-span-2">
              <Card
                className="rounded-xl border bg-card p-8 shadow-sm"
              >
                <h2 className="text-xl font-semibold tracking-tight">Gửi tin nhắn cho chúng tôi</h2>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Họ và tên <span className="text-destructive">*</span></Label>
                      <Input
                        id="name"
                        name="name"
                        placeholder="Nguyễn Văn A"
                        value={formData.name}
                        onChange={handleChange}
                        className="rounded-lg"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email <span className="text-destructive">*</span></Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        placeholder="Email@example.com"
                        value={formData.email}
                        onChange={handleChange}
                        className="rounded-lg"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="phone">Số điện thoại</Label>
                      <Input
                        id="phone"
                        name="phone"
                        type="tel"
                        placeholder="0912345678"
                        value={formData.phone}
                        onChange={handleChange}
                        className="rounded-lg"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="subject">Chủ đề</Label>
                      <Input
                        id="subject"
                        name="subject"
                        placeholder="Chủ đề tin nhắn"
                        value={formData.subject}
                        onChange={handleChange}
                        className="rounded-lg"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="message">Nội dung <span className="text-destructive">*</span></Label>
                    <Textarea
                      id="message"
                      name="message"
                      placeholder="Nhập nội dung tin nhắn của bạn..."
                      value={formData.message}
                      onChange={handleChange}
                      className="min-h-[150px] rounded-lg"
                      required
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full rounded-lg"
                  >
                    <Send className="h-4 w-4 font-bold" />
                    Gửi tin nhắn
                  </Button>
                </form>
              </Card>
            </div>

            {/* Contact Info */}
            <div className="space-y-6">
              <Card
                className="rounded-xl border bg-card p-6 shadow-sm"
              >
                <h3 className="text-lg font-semibold tracking-tight">Thông tin liên hệ</h3>
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
                      <MapPin className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-medium">Địa chỉ</p>
                      <p className="text-sm text-muted-foreground">
                        227 Nguyễn Văn Cừ phường Chợ Quán TP. Hồ Chí Minh, Việt Nam
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
                      <Phone className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-medium">Điện thoại</p>
                      <p className="text-sm text-muted-foreground">
                        028 3823 4567
                        <br />
                        0901 234 567
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
                      <Mail className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-medium">Email</p>
                      <p className="text-sm text-muted-foreground">
                        habiassistant@gmail.com
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
                      <Clock className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-medium">Giờ làm việc</p>
                      <p className="text-sm text-muted-foreground">
                        Thứ 2 - Thứ 6: 07:30 - 17:00
                        <br />
                        Thứ 7 - CN: 9:00 - 12:00
                      </p>
                    </div>
                  </div>
                </div>
              </Card>

              <Card
                className="rounded-xl border bg-card p-6 shadow-sm"
              >
                <h3 className="text-lg font-semibold tracking-tight">Mạng xã hội</h3>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    size="icon"
                    className="rounded-lg"
                  >
                    <span className="text-2xl">📘</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="rounded-lg"
                  >
                    <span className="text-2xl">📷</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="rounded-lg"
                  >
                    <span className="text-2xl">🐦</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="rounded-lg"
                  >
                    <span className="text-2xl">💬</span>
                  </Button>
                </div>
              </Card>
            </div>
          </div>

          {/* FAQ */}
          <Card
            className="rounded-xl border bg-card p-8 shadow-sm"
          >
            <h2 className="text-xl font-semibold tracking-tight">Câu hỏi thường gặp</h2>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium">Chatbot AI của HabiGroup hoạt động như thế nào?</h4>
                <p className="text-sm text-muted-foreground">
                Khác với tìm kiếm từ khóa thông thường, Chatbot của chúng tôi sử dụng công nghệ RAG (Retrieval-Augmented Generation) kết hợp tìm kiếm ngữ nghĩa. Nó có thể hiểu được nhu cầu phức tạp như "tìm quán phở bắc vị thanh, không bột ngọt gần đây" chứ không chỉ bắt từ khóa "phở". Hệ thống sẽ phân tích hàng nghìn đánh giá để đưa ra gợi ý phù hợp nhất với khẩu vị riêng của bạn.
                </p>
              </div>
              <div>
                <h4 className="font-medium">Làm sao tôi biết các quán ăn được gợi ý là uy tín và không phải "review ảo" (seeding)?</h4>
                <p className="text-sm text-muted-foreground">
                Đây là ưu tiên hàng đầu của chúng tôi. Hệ thống sử dụng thuật toán chấm điểm lai (Hybrid Scoring), kết hợp giữa điểm đánh giá của cộng đồng và trí tuệ nhân tạo (AI Sentiment Analysis) để phát hiện và lọc bỏ các bình luận spam hoặc seeding. Chúng tôi chỉ đề xuất những địa điểm thực sự chất lượng dựa trên dữ liệu xác thực.
                </p>
              </div>
              <div>
                <h4 className="font-medium">Ứng dụng có thu thập vị trí (Location) của tôi không?</h4>
                <p className="text-sm text-muted-foreground">
                Chúng tôi tuân thủ nguyên tắc "Privacy-First". Ứng dụng chỉ yêu cầu quyền truy cập vị trí khi bạn sử dụng tính năng "Tìm quán quanh đây" hoặc "Tìm đường". Dữ liệu này chỉ được dùng để tính toán khoảng cách theo thời gian thực và không được lưu trữ hay chia sẻ cho bên thứ ba trái phép.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
