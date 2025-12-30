import { useState } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { ScrollArea } from "./ui/scroll-area";
import { Mail, Phone, MapPin, Send, Clock } from "lucide-react";
import { toast } from "sonner@2.0.3";

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
        <div className="max-w-6xl mx-auto p-4 md:p-6 pt-20 space-y-6 pb-12">
          {/* Header */}
          <div className="text-center space-y-3">
            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
              📬 Liên hệ với chúng tôi
            </h1>
            <p className="text-pink-700">
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
                <h2 className="text-pink-800 mb-6">Gửi tin nhắn cho chúng tôi</h2>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name" className="text-gray-700">
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
                      <Label htmlFor="email" className="text-gray-700">
                        Email <span className="text-pink-500">*</span>
                      </Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        placeholder="email@example.com"
                        value={formData.email}
                        onChange={handleChange}
                        className="bg-white/80 border-pink-200 focus:border-pink-400 rounded-xl"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="phone" className="text-gray-700">
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
                      <Label htmlFor="subject" className="text-gray-700">
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
                    <Label htmlFor="message" className="text-gray-700">
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
                    <Send className="mr-2 h-5 w-5" />
                    Gửi tin nhắn
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
                <h3 className="text-pink-800 mb-4">Thông tin liên hệ</h3>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div
                      className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center flex-shrink-0"
                      style={{ boxShadow: "0 0 15px rgba(255,182,193,0.4)" }}
                    >
                      <MapPin className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-gray-900 mb-1">Địa chỉ</p>
                      <p className="text-sm text-gray-600">
                        123 Nguyễn Huệ, Quận 1
                        <br />
                        TP. Hồ Chí Minh, Việt Nam
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div
                      className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center flex-shrink-0"
                      style={{ boxShadow: "0 0 15px rgba(255,182,193,0.4)" }}
                    >
                      <Phone className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-gray-900 mb-1">Điện thoại</p>
                      <p className="text-sm text-gray-600">
                        028 3823 4567
                        <br />
                        0901 234 567
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div
                      className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center flex-shrink-0"
                      style={{ boxShadow: "0 0 15px rgba(255,182,193,0.4)" }}
                    >
                      <Mail className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-gray-900 mb-1">Email</p>
                      <p className="text-sm text-gray-600">
                        support@foodgalaxy.vn
                        <br />
                        info@foodgalaxy.vn
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div
                      className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center flex-shrink-0"
                      style={{ boxShadow: "0 0 15px rgba(255,182,193,0.4)" }}
                    >
                      <Clock className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-gray-900 mb-1">Giờ làm việc</p>
                      <p className="text-sm text-gray-600">
                        Thứ 2 - Thứ 6: 8:00 - 20:00
                        <br />
                        Thứ 7 - CN: 9:00 - 18:00
                      </p>
                    </div>
                  </div>
                </div>
              </Card>

              <Card
                className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-6 shadow-lg"
                style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
              >
                <h3 className="text-pink-800 mb-4">Mạng xã hội</h3>
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
            <h2 className="text-pink-800 mb-6">Câu hỏi thường gặp</h2>
            <div className="space-y-4">
              <div>
                <h4 className="text-gray-900 mb-2">Làm thế nào để đặt bàn?</h4>
                <p className="text-sm text-gray-600">
                  Bạn có thể đặt bàn bằng cách tìm kiếm nhà hàng, chọn nhà hàng yêu thích và nhấn nút "Đặt bàn ngay". Điền thông tin và xác nhận đặt chỗ.
                </p>
              </div>
              <div>
                <h4 className="text-gray-900 mb-2">Tôi có thể hủy đặt chỗ không?</h4>
                <p className="text-sm text-gray-600">
                  Có, bạn có thể hủy đặt chỗ trong trang "Quản lý đặt chỗ". Tuy nhiên, vui lòng hủy trước ít nhất 2 giờ để tránh phí hủy.
                </p>
              </div>
              <div>
                <h4 className="text-gray-900 mb-2">Chatbot AI hoạt động như thế nào?</h4>
                <p className="text-sm text-gray-600">
                  Chatbot AI của chúng tôi sử dụng công nghệ AI để gợi ý món ăn và nhà hàng phù hợp dựa trên sở thích và câu hỏi của bạn.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
