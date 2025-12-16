import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { User, Mail, Lock, Sparkles } from "lucide-react";
import { login, registerStart, registerVerify, forgotPassword, resetPassword } from "../services/auth";
import type { LoginResponse } from "../services/auth";

interface AuthDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLogin: (payload: LoginResponse) => void;
}

export function AuthDialog({ open, onOpenChange, onLogin }: AuthDialogProps) {
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerConfirm, setRegisterConfirm] = useState("");
  const [registerOtp, setRegisterOtp] = useState("");
  const [registerStep, setRegisterStep] = useState<"form" | "otp">("form");
  const [forgotMode, setForgotMode] = useState(false);
  const [forgotOtp, setForgotOtp] = useState("");
  const [forgotNewPass, setForgotNewPass] = useState("");
  const [forgotConfirmPass, setForgotConfirmPass] = useState("");
  const [loading, setLoading] = useState(false);
  const [info, setInfo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const resetMessages = () => {
    setInfo(null);
    setError(null);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    try {
      setLoading(true);
      const data = await login(loginEmail, loginPassword);
      onLogin(data);
      onOpenChange(false);
      setLoginEmail("");
      setLoginPassword("");
    } catch (err: any) {
      setError(err?.message || "Đăng nhập thất bại");
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterStart = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    if (registerPassword !== registerConfirm) {
      setError("Mật khẩu xác nhận không khớp");
      return;
    }
    try {
      setLoading(true);
      await registerStart({
        email: registerEmail,
        name: registerName,
        password: registerPassword,
        confirm_password: registerConfirm,
      });
      setRegisterStep("otp");
      setInfo("Đã gửi OTP đến email của bạn");
    } catch (err: any) {
      setError(err?.message || "Gửi OTP thất bại");
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    try {
      setLoading(true);
      const data = await registerVerify({ email: registerEmail, otp: registerOtp });
      onLogin(data);
      onOpenChange(false);
      setRegisterStep("form");
      setRegisterOtp("");
      setRegisterName("");
      setRegisterEmail("");
      setRegisterPassword("");
      setRegisterConfirm("");
    } catch (err: any) {
      setError(err?.message || "Xác thực OTP thất bại");
    } finally {
      setLoading(false);
    }
  };

  const handleForgotSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    try {
      setLoading(true);
      await forgotPassword(registerEmail);
      setInfo("Đã gửi OTP đặt lại mật khẩu");
      setForgotMode(true);
    } catch (err: any) {
      setError(err?.message || "Gửi OTP thất bại");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    if (forgotNewPass !== forgotConfirmPass) {
      setError("Mật khẩu xác nhận không khớp");
      return;
    }
    try {
      setLoading(true);
      await resetPassword({
        email: registerEmail,
        otp: forgotOtp,
        new_password: forgotNewPass,
        confirm_password: forgotConfirmPass,
      });
      setInfo("Đặt lại mật khẩu thành công, hãy đăng nhập");
      setForgotMode(false);
      setForgotOtp("");
      setForgotNewPass("");
      setForgotConfirmPass("");
    } catch (err: any) {
      setError(err?.message || "Đặt lại mật khẩu thất bại");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-[425px] bg-gradient-to-br from-pink-50 via-purple-50 to-fuchsia-50 border-2 border-pink-300 shadow-2xl rounded-3xl"
        style={{ boxShadow: "0 0 40px rgba(255,182,193,0.5), inset 0 0 30px rgba(255,255,255,0.5)" }}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-pink-700">
            <Sparkles className="h-5 w-5" />
            Chào mừng đến với Cosmic Food
          </DialogTitle>
          <DialogDescription className="text-pink-600">
            Đăng nhập hoặc tạo tài khoản để bắt đầu khám phá ẩm thực Việt Nam
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="login" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-pink-200/50">
            <TabsTrigger
              value="login"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-pink-300 data-[state=active]:to-rose-300 data-[state=active]:text-white rounded-xl"
            >
              Đăng nhập
            </TabsTrigger>
            <TabsTrigger
              value="register"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-pink-300 data-[state=active]:to-rose-300 data-[state=active]:text-white rounded-xl"
            >
              Đăng ký
            </TabsTrigger>
          </TabsList>

          <TabsContent value="login" className="space-y-4 mt-4">
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="login-email" className="text-pink-700">
                  Email
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-pink-400" />
                  <Input
                    id="login-email"
                    type="email"
                    placeholder="email@example.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="pl-10 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="login-password" className="text-pink-700">
                  Mật khẩu
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-pink-400" />
                  <Input
                    id="login-password"
                    type="password"
                    placeholder="••••••••"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="pl-10 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    required
                  />
                </div>
              </div>
              {!forgotMode && (
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 hover:from-pink-300 hover:via-rose-300 hover:to-fuchsia-300 text-white shadow-xl rounded-2xl border-2 border-pink-200"
                  style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
                  disabled={loading}
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  Đăng nhập
                </Button>
              )}
              <div className="text-right text-sm">
                <button
                  type="button"
                  className="text-pink-600 hover:underline"
                  onClick={() => {
                    setForgotMode(true);
                    resetMessages();
                  }}
                >
                  Quên mật khẩu?
                </button>
              </div>
            </form>

            {forgotMode && (
              <div className="space-y-3 border border-pink-200 rounded-2xl p-3 bg-white/70">
                <p className="text-pink-700 font-semibold">Đặt lại mật khẩu</p>
                <form onSubmit={handleResetPassword} className="space-y-3">
                  <Label className="text-pink-700">Email</Label>
                  <Input
                    type="email"
                    value={registerEmail}
                    onChange={(e) => setRegisterEmail(e.target.value)}
                    placeholder="email@example.com"
                    className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    required
                  />
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      className="bg-white border border-pink-200"
                      onClick={handleForgotSendOtp}
                      disabled={loading}
                    >
                      Gửi OTP
                    </Button>
                    <Input
                      type="text"
                      value={forgotOtp}
                      onChange={(e) => setForgotOtp(e.target.value)}
                      placeholder="Nhập OTP"
                      className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                      required
                    />
                  </div>
                  <Input
                    type="password"
                    value={forgotNewPass}
                    onChange={(e) => setForgotNewPass(e.target.value)}
                    placeholder="Mật khẩu mới"
                    className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    required
                  />
                  <Input
                    type="password"
                    value={forgotConfirmPass}
                    onChange={(e) => setForgotConfirmPass(e.target.value)}
                    placeholder="Xác nhận mật khẩu"
                    className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    required
                  />
                  <div className="flex gap-2">
                    <Button
                      type="submit"
                      className="flex-1 bg-gradient-to-r from-pink-400 to-rose-400 text-white"
                      disabled={loading}
                    >
                      Đặt lại mật khẩu
                    </Button>
                    <Button type="button" variant="ghost" onClick={() => setForgotMode(false)}>
                      Đóng
                    </Button>
                  </div>
                </form>
              </div>
            )}
          </TabsContent>

          <TabsContent value="register" className="space-y-4 mt-4">
            {registerStep === "form" ? (
              <form onSubmit={handleRegisterStart} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="register-name" className="text-pink-700">
                    Tên hiển thị
                  </Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-pink-400" />
                    <Input
                      id="register-name"
                      type="text"
                      placeholder="Nguyễn Văn A"
                      value={registerName}
                      onChange={(e) => setRegisterName(e.target.value)}
                      className="pl-10 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-email" className="text-pink-700">
                    Email
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-pink-400" />
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="email@example.com"
                      value={registerEmail}
                      onChange={(e) => setRegisterEmail(e.target.value)}
                      className="pl-10 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-password" className="text-pink-700">
                    Mật khẩu
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-pink-400" />
                    <Input
                      id="register-password"
                      type="password"
                      placeholder="••••••••"
                      value={registerPassword}
                      onChange={(e) => setRegisterPassword(e.target.value)}
                      className="pl-10 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                      required
                    />
                  </div>
                </div>
                <Input
                  type="password"
                  placeholder="Xác nhận mật khẩu"
                  value={registerConfirm}
                  onChange={(e) => setRegisterConfirm(e.target.value)}
                  className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                  required
                />
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 hover:from-pink-300 hover:via-rose-300 hover:to-fuchsia-300 text-white shadow-xl rounded-2xl border-2 border-pink-200"
                  style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
                  disabled={loading}
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  Gửi OTP
                </Button>
              </form>
            ) : (
              <form onSubmit={handleRegisterVerify} className="space-y-4">
                <p className="text-pink-700">Nhập OTP đã gửi tới {registerEmail}</p>
                <Input
                  type="text"
                  placeholder="Mã OTP"
                  value={registerOtp}
                  onChange={(e) => setRegisterOtp(e.target.value)}
                  className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                  required
                />
                <div className="flex gap-2">
                  <Button
                    type="submit"
                    className="flex-1 bg-gradient-to-r from-pink-400 to-rose-400 text-white"
                    disabled={loading}
                  >
                    Xác thực
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    className="bg-white border border-pink-200"
                    onClick={() => setRegisterStep("form")}
                  >
                    Quay lại
                  </Button>
                </div>
              </form>
            )}
          </TabsContent>
        </Tabs>

        {(info || error) && (
          <div
            className={`text-sm rounded-xl border px-3 py-2 ${
              info ? "bg-green-50 border-green-200 text-green-700" : "bg-red-50 border-red-200 text-red-700"
            }`}
          >
            {info || error}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

