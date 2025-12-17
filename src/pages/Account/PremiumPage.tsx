import { useNavigate } from "react-router-dom";
import { ArrowLeft, Sparkles } from "lucide-react";

import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";

export function PremiumPage() {
  const navigate = useNavigate();

  return (
    <div className="h-full overflow-y-auto px-4 sm:px-6 lg:px-10 py-8 pb-24">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(-1)}
            className="rounded-2xl hover:bg-pink-100 text-pink-700"
            aria-label="Quay lại"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-pink-800">Gói Premium</h1>
            <p className="text-sm text-pink-600">Sắp ra mắt</p>
          </div>
        </div>

        <Card className="bg-gradient-to-br from-pink-50/90 via-purple-50/90 to-fuchsia-50/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-2xl">
          <CardHeader className="border-b border-pink-200/60">
            <CardTitle className="text-pink-800 font-bold flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-pink-800" />
              Tính năng nâng cao
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-pink-700">
              Trang này đang được hoàn thiện. Mình sẽ bổ sung các tính năng Premium (ưu đãi, trải nghiệm AI nâng cao,
              đánh giá nâng cao...) trong bản cập nhật tiếp theo.
            </p>
            <Button
              onClick={() => navigate("/")}
              className="bg-gradient-to-r from-pink-400 to-rose-400 text-white rounded-2xl border-2 border-pink-200"
            >
              VỀ TRANG CHỦ
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

