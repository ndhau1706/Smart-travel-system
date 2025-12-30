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
            className="rounded-lg text-muted-foreground hover:text-foreground"
            aria-label="Quay lại"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Gói Premium</h1>
            <p className="text-sm text-muted-foreground">Sắp ra mắt</p>
          </div>
        </div>

        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <CardTitle className="flex items-center gap-2 font-semibold">
              <Sparkles className="h-5 w-5 text-highlight" />
              Tính năng nâng cao
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-muted-foreground">
              Trang này đang được hoàn thiện. Mình sẽ bổ sung các tính năng Premium (ưu đãi, trải nghiệm AI nâng cao,
              đánh giá nâng cao...) trong bản cập nhật tiếp theo.
            </p>
            <Button
              onClick={() => navigate("/")}
              className="rounded-lg"
            >
              VỀ TRANG CHỦ
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
