import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, KeyRound, Lock, ShieldCheck } from "lucide-react";

import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { changePassword } from "../../services/auth";

export function SettingsPage() {
  const navigate = useNavigate();
  const [needsLogin, setNeedsLogin] = useState(false);
  const [savingPwd, setSavingPwd] = useState(false);
  const [pwd, setPwd] = useState({ current: "", next: "", confirm: "" });

  useEffect(() => {
    const stored = localStorage.getItem("auth");
    setNeedsLogin(!stored);
  }, []);

  const savePassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (needsLogin) {
      toast.error("Bạn cần đăng nhập để đổi mật khẩu");
      return;
    }
    if (!pwd.current || !pwd.next || !pwd.confirm) {
      toast.error("Vui lòng nhập đầy đủ thông tin");
      return;
    }
    if (pwd.next.length < 6) {
      toast.error("Mật khẩu mới phải có ít nhất 6 ký tự");
      return;
    }
    if (pwd.next !== pwd.confirm) {
      toast.error("Mật khẩu xác nhận không khớp");
      return;
    }

    setSavingPwd(true);
    try {
      await changePassword({
        current_password: pwd.current,
        new_password: pwd.next,
        confirm_password: pwd.confirm,
      });
      toast.success("Đổi mật khẩu thành công");
      setPwd({ current: "", next: "", confirm: "" });
    } catch (err: any) {
      toast.error(err?.message || "Đổi mật khẩu thất bại");
    } finally {
      setSavingPwd(false);
    }
  };

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
            <h1 className="text-2xl font-semibold tracking-tight">Cài đặt</h1>
            <p className="text-sm text-muted-foreground">Bảo mật và tuỳ chọn tài khoản</p>
          </div>
        </div>

        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <CardTitle className="flex items-center gap-2 font-semibold">
              <ShieldCheck className="h-5 w-5 text-primary" />
              Bảo mật
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {needsLogin ? (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Bạn cần đăng nhập để đổi mật khẩu.
                </p>
                <Button
                  onClick={() => navigate("/")}
                  className="rounded-lg"
                >
                  Về trang chủ
                </Button>
              </div>
            ) : (
              <form onSubmit={savePassword} className="space-y-4">
                <div className="space-y-2">
                  <Label>
                    <Lock className="h-4 w-4 text-muted-foreground" />
                    Mật khẩu hiện tại
                  </Label>
                  <Input
                    type="password"
                    value={pwd.current}
                    onChange={(e) =>
                      setPwd((prev) => ({ ...prev, current: e.target.value }))
                    }
                    placeholder="••••••••"
                    className="rounded-lg"
                    autoComplete="current-password"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>
                      <KeyRound className="h-4 w-4 text-muted-foreground" />
                      Mật khẩu mới
                    </Label>
                    <Input
                      type="password"
                      value={pwd.next}
                      onChange={(e) =>
                        setPwd((prev) => ({ ...prev, next: e.target.value }))
                      }
                      placeholder="Tối thiểu 6 ký tự"
                      className="rounded-lg"
                      autoComplete="new-password"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Xác nhận mật khẩu</Label>
                    <Input
                      type="password"
                      value={pwd.confirm}
                      onChange={(e) =>
                        setPwd((prev) => ({ ...prev, confirm: e.target.value }))
                      }
                      placeholder="Nhập lại mật khẩu mới"
                      className="rounded-lg"
                      autoComplete="new-password"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={savingPwd}
                  className="rounded-lg shadow-sm"
                >
                  {savingPwd ? "Đang đổi..." : "ĐỔI MẬT KHẨU"}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
