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
    <div className="min-h-screen relative">
      <ScrollArea className="h-screen">
        <div className="max-w-6xl mx-auto p-4 md:p-6 space-y-6 pb-12" style={{ paddingTop: "100px" }}>
          {/* Header */}
          <div className="text-center space-y-3">
            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
              📬 LIÊN HỆ VỚI CHÚNG TÔI
            </h1>
            <p className="text-pink-700 text-lg max-w-3xl mx-auto">
              Chúng tôi luôn sẵn sàng lắng nghe ý kiến và hỗ trợ bạn
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Contact Form */}
            <div className="lg:col-span-2">
              <Card
                className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
                style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
              >
                <h2 className="text-pink-800 font-bold">GỬI TIN NHẮN CHO CHÚNG TÔI</h2>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name" className="text-pink-700 font-bold">
                        Họ và tên <span className="text-pink-500">*</span>
                      </Label>
                      <Input
                        id="name"
                        name="name"
                        placeholder="Nguyễn Văn A"
                        value={formData.name}
                        onChange={handleChange}
                        className="bg-white/80 border-pink-200 focus:border-pink-400 rounded-xl"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email" className="text-pink-700 font-bold">
                        Email <span className="text-pink-500">*</span>
                      </Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        placeholder="Email@example.com"
                        value={formData.email}
                        onChange={handleChange}
                        className="bg-white/80 border-pink-200 focus:border-pink-400 rounded-xl"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="phone" className="text-pink-700 font-bold">
                        Số điện thoại
                      </Label>
                      <Input
                        id="phone"
                        name="phone"
                        type="tel"
                        placeholder="0912345678"
                        value={formData.phone}
                        onChange={handleChange}
                        className="bg-white/80 border-pink-200 focus:border-pink-400 rounded-xl"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="subject" className="text-pink-700 font-bold">
                        Chủ đề
                      </Label>
                      <Input
                        id="subject"
                        name="subject"
                        placeholder="Chủ đề tin nhắn"
                        value={formData.subject}
                        onChange={handleChange}
                        className="bg-white/80 border-pink-200 focus:border-pink-400 rounded-xl"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="message" className="text-pink-700 font-bold">
                      Nội dung <span className="text-pink-500">*</span>
                    </Label>
                    <Textarea
                      id="message"
                      name="message"
                      placeholder="Nhập nội dung tin nhắn của bạn..."
                      value={formData.message}
                      onChange={handleChange}
                      className="bg-white/80 border-pink-200 focus:border-pink-400 rounded-xl min-h-[150px]"
                      required
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl py-6 shadow-lg"
                    style={{ boxShadow: "0 0 25px rgba(255,182,193,0.5)" }}
                  >
                    <Send className="h-4 w-4 font-bold" />
                    GỬI TIN NHẮN
                  </Button>
                </form>
              </Card>
            </div>

            {/* Contact Info */}
            <div className="space-y-6">
              <Card
                className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-6 shadow-lg"
                style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
              >
                <h3 className="text-pink-800 font-bold">THÔNG TIN LIÊN HỆ</h3>
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center flex-shrink-0"
                      style={{ boxShadow: "0 0 15px rgba(255,182,193,0.4)" }}
                    >
                      <MapPin className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-pink-700 font-bold">Địa chỉ</p>
                      <p className="text-sm text-gray-700">
                        227 Nguyễn Văn Cừ phường Chợ Quán TP. Hồ Chí Minh, Việt Nam
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center flex-shrink-0"
                      style={{ boxShadow: "0 0 15px rgba(255,182,193,0.4)" }}
                    >
                      <Phone className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-pink-700 font-bold">Điện thoại</p>
                      <p className="text-sm text-gray-700">
                        028 3823 4567
                        <br />
                        0901 234 567
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center flex-shrink-0"
                      style={{ boxShadow: "0 0 15px rgba(255,182,193,0.4)" }}
                    >
                      <Mail className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className=" text-pink-700 font-bold">Email</p>
                      <p className="text-sm text-gray-700">
                      habiassistant@gmail.com
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center flex-shrink-0"
                      style={{ boxShadow: "0 0 15px rgba(255,182,193,0.4)" }}
                    >
                      <Clock className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-pink-700 font-bold">Giờ làm việc</p>
                      <p className="text-sm text-gray-700">
                        Thứ 2 - Thứ 6: 07:30 - 17:00
                        <br />
                        Thứ 7 - CN: 9:00 - 12:00
                      </p>
                    </div>
                  </div>
                </div>
              </Card>

              <Card
                className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-6 shadow-lg"
                style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
              >
                <h3 className="text-pink-800 font-bold">MẠNG XÃ HỘI</h3>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    size="icon"
                    className="rounded-xl border-pink-300 hover:bg-pink-100"
                  >
                    <span className="text-2xl">📘</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="rounded-xl border-pink-300 hover:bg-pink-100"
                  >
                    <span className="text-2xl">📷</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="rounded-xl border-pink-300 hover:bg-pink-100"
                  >
                    <span className="text-2xl">🐦</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="rounded-xl border-pink-300 hover:bg-pink-100"
                  >
                    <span className="text-2xl">💬</span>
                  </Button>
                </div>
              </Card>
            </div>
          </div>

          {/* FAQ */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-8 shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <h2 className="text-pink-800 font-bold">CÂU HỎI THƯỜNG GẶP</h2>
            <div className="space-y-4">
              <div>
                <h4 className="text-pink-700 font-bold">Chatbot AI của HabiGroup hoạt động như thế nào?</h4>
                <p className="text-sm text-gray-700 text-ju">
                Khác với tìm kiếm từ khóa thông thường, Chatbot của chúng tôi sử dụng công nghệ RAG (Retrieval-Augmented Generation) kết hợp tìm kiếm ngữ nghĩa. Nó có thể hiểu được nhu cầu phức tạp như "tìm quán phở bắc vị thanh, không bột ngọt gần đây" chứ không chỉ bắt từ khóa "phở". Hệ thống sẽ phân tích hàng nghìn đánh giá để đưa ra gợi ý phù hợp nhất với khẩu vị riêng của bạn.
                </p>
              </div>
              <div>
                <h4 className="text-pink-700 font-bold mb-1">Làm sao tôi biết các quán ăn được gợi ý là uy tín và không phải "review ảo" (seeding)?</h4>
                <p className="text-sm text-gray-700 text-ju">
                Đây là ưu tiên hàng đầu của chúng tôi. Hệ thống sử dụng thuật toán chấm điểm lai (Hybrid Scoring), kết hợp giữa điểm đánh giá của cộng đồng và trí tuệ nhân tạo (AI Sentiment Analysis) để phát hiện và lọc bỏ các bình luận spam hoặc seeding. Chúng tôi chỉ đề xuất những địa điểm thực sự chất lượng dựa trên dữ liệu xác thực.
                </p>
              </div>
              <div>
                <h4 className="text-pink-700 font-bold">Ứng dụng có thu thập vị trí (Location) của tôi không?</h4>
                <p className="text-sm text-gray-700 text-ju">
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
