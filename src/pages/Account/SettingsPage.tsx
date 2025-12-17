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
            className="rounded-2xl hover:bg-pink-100 text-pink-700"
            aria-label="Quay lại"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-pink-800">Cài đặt</h1>
            <p className="text-sm text-pink-600">Bảo mật và tuỳ chọn tài khoản</p>
          </div>
        </div>

        <Card className="bg-gradient-to-br from-pink-50/90 via-purple-50/90 to-fuchsia-50/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-2xl">
          <CardHeader className="border-b border-pink-200/60">
            <CardTitle className="text-pink-800 font-bold flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-pink-600" />
              Bảo mật
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {needsLogin ? (
              <div className="space-y-3">
                <p className="text-sm text-pink-600">
                  Bạn cần đăng nhập để đổi mật khẩu.
                </p>
                <Button
                  onClick={() => navigate("/")}
                  className="bg-gradient-to-r from-pink-400 to-rose-400 text-white rounded-2xl border-2 border-pink-200"
                >
                  Về trang chủ
                </Button>
              </div>
            ) : (
              <form onSubmit={savePassword} className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-pink-700 flex items-center gap-2">
                    <Lock className="h-4 w-4 text-pink-600" />
                    Mật khẩu hiện tại
                  </Label>
                  <Input
                    type="password"
                    value={pwd.current}
                    onChange={(e) =>
                      setPwd((prev) => ({ ...prev, current: e.target.value }))
                    }
                    placeholder="••••••••"
                    className=" placeholder:text-gray-700 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    autoComplete="current-password"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-pink-700 flex items-center gap-2">
                      <KeyRound className="h-4 w-4 text-pink-400" />
                      Mật khẩu mới
                    </Label>
                    <Input
                      type="password"
                      value={pwd.next}
                      onChange={(e) =>
                        setPwd((prev) => ({ ...prev, next: e.target.value }))
                      }
                      placeholder="Tối thiểu 6 ký tự"
                      className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl placeholder:text-gray-700"
                      autoComplete="new-password"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-pink-700">Xác nhận mật khẩu</Label>
                    <Input
                      type="password"
                      value={pwd.confirm}
                      onChange={(e) =>
                        setPwd((prev) => ({ ...prev, confirm: e.target.value }))
                      }
                      placeholder="Nhập lại mật khẩu mới"
                      className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl placeholder:text-gray-700"
                      autoComplete="new-password"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={savingPwd}
                  className="bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl shadow-xl border-2 border-pink-200"
                  style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
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
